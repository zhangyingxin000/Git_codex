from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.generate_allure_report import convert_junit
from scripts.mobile_pytest_evidence import finalize_mobile_pytest_run
from scripts.mobile_observability import (
    build_performance_interpretation,
    evaluate_performance,
    parse_gfxinfo_framestats,
    parse_runtime_health,
    parse_startup_timing,
    parse_top_cpu,
    render_performance_interpretation,
)
from scripts.run_ci import secret_fingerprints
from scripts.run_mobile_ci import (
    build_coverage_scope,
    load_mobile_assets,
    parse_adb_devices,
    redact,
    run_workflow,
    sdk_root_from_adb,
    select_devices,
    select_server_port,
    select_workflows,
)

ROOT = Path(__file__).resolve().parents[1]


def test_mobile_performance_interpretation_explains_thresholds_and_cpu_actions() -> None:
    interpretation = build_performance_interpretation(
        {
            "startup": {
                "cold": {"total_time_ms": 755},
                "warm": {"total_time_ms": 60},
            },
            "after_workflows": {
                "total_pss_kb": 200000,
                "process_cpu_percent": 61.5,
                "graphics": {"estimated_fps": 66.36, "jank_percent": 0},
            },
            "runtime_health": {"signal_count": 0},
        }
    )
    markdown = render_performance_interpretation(interpretation)

    assert interpretation["status"] == "WARN"
    assert "冷启动耗时**：755ms" in markdown
    assert "<2000ms合格" in markdown
    assert "界面帧率**：66.36FPS" in markdown
    assert "CPU峰值**：61.5%" in markdown
    assert "CPU Profiler" in markdown


def test_mobile_performance_interpretation_explains_multicore_cpu_values() -> None:
    interpretation = build_performance_interpretation(
        {"after_workflows": {"process_cpu_percent": 119.0}}
    )
    markdown = render_performance_interpretation(interpretation)

    assert "Android多核进程统计可超过100%" in markdown
    assert "1.19个CPU核心" in markdown


def test_mobile_coverage_keeps_reproducible_skipped_steps() -> None:
    scope = build_coverage_scope(
        {
            "coverage": {
                "project_name": "Soulfree",
                "reproducible_scenarios": [
                    {"id": "startup-ad", "name": "启动广告", "status": "PENDING_REPRODUCTION"}
                ],
            }
        },
        [],
        {},
        [
            {
                "udid": "phone-1",
                "workflow_steps": [
                    {
                        "name": "Skip startup advertisement when shown",
                        "workflow_id": "soulfree-room-smoke",
                        "status": "SKIPPED",
                        "message": "optional element was not present",
                    }
                ],
            }
        ],
    )

    skipped = scope["actual_verification"][0]["skipped_steps"][0]
    assert skipped["verification_status"] == "NOT_OBSERVED_THIS_RUN"
    assert skipped["reason"] == "optional element was not present"
    assert scope["current_project"]["registered_reproducible_scenarios"][0]["id"] == "startup-ad"


def test_junit_conversion_creates_allure_results(tmp_path: Path) -> None:
    junit = tmp_path / "junit.xml"
    junit.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="sample" tests="2" failures="1">
  <testcase classname="sample.Cases" name="passes" time="0.01" />
  <testcase classname="sample.Cases" name="fails" time="0.02">
    <failure message="expected true">trace</failure>
  </testcase>
</testsuite>
""",
        encoding="utf-8",
    )
    results_dir = tmp_path / "allure-results"

    summary = convert_junit([junit], results_dir)

    assert summary == {"converted": 2, "status_counts": {"passed": 1, "failed": 1}}
    result_payloads = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in results_dir.glob("*-result.json")
    ]
    assert {payload["status"] for payload in result_payloads} == {"passed", "failed"}


def test_secret_fingerprints_ignore_line_number_changes() -> None:
    first = {
        "results": {
            "config.py": [
                {
                    "type": "Secret Keyword",
                    "hashed_secret": "abc123",  # pragma: allowlist secret
                    "line_number": 10,
                }
            ]
        }
    }
    moved = {
        "results": {
            "config.py": [
                {
                    "type": "Secret Keyword",
                    "hashed_secret": "abc123",  # pragma: allowlist secret
                    "line_number": 99,
                }
            ]
        }
    }

    assert secret_fingerprints(first) == secret_fingerprints(moved)


def test_mobile_logs_redact_query_credentials_and_jwts() -> None:
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJ1aWQiOjEyM30.signature"  # pragma: allowlist secret
    raw = f"GET /client?ticket={jwt}&access_token={jwt}&uid=123"

    sanitized = redact(raw, {})

    assert jwt not in sanitized
    assert "ticket=***" in sanitized
    assert "access_token=***" in sanitized
    assert "uid=123" in sanitized


def test_disabled_mobile_ci_is_reported_as_skipped(tmp_path: Path) -> None:
    config = tmp_path / "mobile.yaml"
    config.write_text('schema_version: "1.0"\nenabled: false\n', encoding="utf-8")
    report_root = tmp_path / "reports"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_mobile_ci.py"),
            "--config",
            str(config),
            "--report-root",
            str(report_root),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    summary_path = next(report_root.glob("*/summary.json"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "SKIPPED"


def test_mobile_pytest_runtime_is_the_explicit_top_level_runner(tmp_path: Path) -> None:
    config = tmp_path / "mobile.yaml"
    config.write_text('schema_version: "1.0"\nenabled: false\n', encoding="utf-8")
    report_root = tmp_path / "reports"
    pytest_work = tmp_path / "pytest-work"
    environment = os.environ.copy()
    environment.update(
        {
            "AUTOTEST_MOBILE_CONFIG": str(config),
            "AUTOTEST_MOBILE_REPORT_ROOT": str(report_root),
            "AUTOTEST_MOBILE_SCENARIOS": "[]",
            "AUTOTEST_MOBILE_DEVICES": "[]",
        }
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-s",
            "--basetemp",
            str(pytest_work),
            "mobile/pytest_runtime.py",
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "Android Appium CI: SKIPPED" in completed.stdout
    assert next(report_root.glob("*/summary.json")).is_file()


def test_mobile_pytest_evidence_is_archived_into_the_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report_root = tmp_path / "reports"
    run_root = report_root / "mobile-test"
    task_root = report_root / "task-runs" / "task-test"
    run_root.mkdir(parents=True)
    task_root.mkdir(parents=True)
    summary_path = run_root / "summary.json"
    summary_path.write_text(
        json.dumps({"status": "PASSED", "artifacts": {}}, ensure_ascii=False),
        encoding="utf-8",
    )
    console = task_root / "pytest-console.log"
    console.write_text(f"Summary: {summary_path}\n1 passed\n", encoding="utf-8")
    junit = task_root / "pytest-junit.xml"
    junit.write_text(
        '<testsuite tests="1"><testcase classname="mobile" name="runtime" /></testsuite>',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "scripts.mobile_pytest_evidence.generate_report",
        lambda *_: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )

    result = finalize_mobile_pytest_run(report_root, console, junit, 0)

    archived = json.loads(summary_path.read_text(encoding="utf-8"))
    assert result["allure_status"] == "PASSED"
    assert archived["execution_chain"] == [
        "pytest",
        "Appium",
        "Android device/emulator",
        "Allure",
    ]
    assert (run_root / "pytest-evidence.json").is_file()
    assert (run_root / "pytest-junit.xml").is_file()


def test_mobile_page_objects_resolve_scenario_targets(tmp_path: Path) -> None:
    pages = tmp_path / "pages.yaml"
    scenarios = tmp_path / "scenarios.yaml"
    config_path = tmp_path / "mobile.yaml"
    pages.write_text(
        'schema_version: "1.0"\npages:\n  login:\n    submit:\n'
        '      by: id\n      value: sample:id/login\n',
        encoding="utf-8",
    )
    scenarios.write_text(
        'schema_version: "1.0"\nworkflows:\n  - id: login\n    enabled: true\n'
        '    steps:\n      - name: Submit\n        action: click\n        target: login.submit\n',
        encoding="utf-8",
    )
    config_path.write_text('schema_version: "1.0"\n', encoding="utf-8")

    merged = load_mobile_assets(
        {
            "page_object_files": [str(pages)],
            "scenario_files": [str(scenarios)],
        },
        config_path,
    )

    step = merged["workflows"][0]["steps"][0]
    assert step["page_object"] == "login.submit"
    assert step["by"] == "id"
    assert step["value"] == "sample:id/login"


def test_explicit_mobile_scenario_can_enable_a_default_off_template(tmp_path: Path) -> None:
    del tmp_path
    selected = select_workflows(
        [
            {"id": "room", "enabled": True},
            {"id": "startup-check", "enabled": False},
        ],
        ["startup-check"],
    )

    assert selected == [{"id": "startup-check", "enabled": True}]


def test_sdk_root_is_derived_from_platform_tools_adb(tmp_path: Path) -> None:
    adb = tmp_path / "Android" / "Sdk" / "platform-tools" / "adb.exe"
    adb.parent.mkdir(parents=True)
    adb.touch()

    assert sdk_root_from_adb(str(adb)) == str(adb.parent.parent)


def test_adb_device_pool_distinguishes_physical_devices_and_emulators() -> None:
    devices = parse_adb_devices(
        """List of devices attached
RZCW400ET6X device product:a54x model:SM_A546B transport_id:1
emulator-5554 device product:sdk_gphone64_x86_64 model:sdk_gphone64_x86_64 transport_id:2
offline-device offline
"""
    )

    assert devices == [
        {"udid": "RZCW400ET6X", "model": "SM_A546B", "kind": "physical"},
        {
            "udid": "emulator-5554",
            "model": "sdk_gphone64_x86_64",
            "kind": "emulator",
        },
    ]
    assert select_devices(devices, {"mode": "all"}) == devices
    assert select_devices(devices, {"mode": "first"}) == devices[:1]


def test_device_pool_can_select_only_emulators() -> None:
    devices = [
        {"udid": "phone-1", "model": "Phone", "kind": "physical"},
        {"udid": "emulator-5554", "model": "Pixel", "kind": "emulator"},
    ]

    selected = select_devices(
        devices,
        {"mode": "all", "allow_physical": False, "allow_emulators": True},
    )

    assert selected == [{"udid": "emulator-5554", "model": "Pixel", "kind": "emulator"}]


def test_appium_port_can_avoid_an_existing_listener() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        occupied_port = int(listener.getsockname()[1])

        selected_port = select_server_port("127.0.0.1", occupied_port, auto_select=True)
        assert selected_port != occupied_port
        with pytest.raises(RuntimeError, match="already in use"):
            select_server_port("127.0.0.1", occupied_port, auto_select=False)


def test_mobile_workflow_allows_optional_elements_and_captures_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("scripts.run_mobile_ci.find_element", lambda *args, **kwargs: None)

    def fake_screenshot(server_url: str, session_id: str, path: Path) -> None:
        path.write_bytes(b"png")

    monkeypatch.setattr("scripts.run_mobile_ci.capture_screenshot", fake_screenshot)
    workflow = {
        "enabled": True,
        "id": "sample-smoke",
        "steps": [
            {
                "name": "Optional startup prompt",
                "action": "click_optional",
                "by": "id",
                "value": "sample:id/prompt",
                "timeout_seconds": 1,
            },
            {"name": "Final page", "action": "screenshot"},
        ],
    }

    status, message, steps, attachments = run_workflow(
        "http://127.0.0.1:4723", "session", workflow, tmp_path
    )

    assert status == "PASSED"
    assert message == "workflow passed with 2 steps"
    assert [step["status"] for step in steps] == ["SKIPPED", "PASSED"]
    assert attachments[0][1].is_file()


def test_mobile_workflow_blocks_unapproved_data_mutation(tmp_path: Path) -> None:
    workflow = {
        "enabled": True,
        "id": "payment",
        "steps": [
            {
                "name": "Submit sandbox payment",
                "action": "click",
                "by": "id",
                "value": "sample:id/pay",
                "mutates_data": True,
                "risk_level": "high",
            }
        ],
    }

    status, message, steps, attachments = run_workflow(
        "http://127.0.0.1:4723",
        "session",
        workflow,
        tmp_path,
        safety={"allow_mutations": False, "allow_high_risk": False},
    )

    assert status == "BLOCKED"
    assert "data mutation is disabled" in message
    assert steps[0]["status"] == "BLOCKED"
    assert attachments == []


def test_mobile_workflow_supports_ui_and_navigation_assertions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("scripts.run_mobile_ci.find_element", lambda *args, **kwargs: "element")

    def fake_http_json(url: str, method: str = "GET", payload: dict | None = None, **kwargs: object) -> dict:
        del method, payload, kwargs
        if url.endswith("/text"):
            return {"value": "Welcome home"}
        if url.endswith("/attribute/enabled"):
            return {"value": "true"}
        if url.endswith("/current_activity"):
            return {"value": ".HomeActivity"}
        return {"value": None}

    monkeypatch.setattr("scripts.run_mobile_ci.http_json", fake_http_json)
    workflow = {
        "enabled": True,
        "id": "ui-checks",
        "steps": [
            {
                "name": "Verify welcome text",
                "action": "assert_text",
                "by": "id",
                "value": "sample:id/title",
                "contains": "Welcome",
            },
            {
                "name": "Verify input enabled",
                "action": "assert_enabled",
                "by": "id",
                "value": "sample:id/account",
            },
            {
                "name": "Verify navigation",
                "action": "assert_activity",
                "contains": "HomeActivity",
            },
        ],
    }

    status, message, steps, _ = run_workflow(
        "http://127.0.0.1:4723", "session", workflow, tmp_path
    )

    assert status == "PASSED"
    assert message == "workflow passed with 3 steps"
    assert [step["status"] for step in steps] == ["PASSED", "PASSED", "PASSED"]


def test_mobile_workflow_validates_and_compares_repeated_startup_pages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    screenshot_number = 0

    def fake_screenshot(server_url: str, session_id: str, path: Path) -> None:
        nonlocal screenshot_number
        del server_url, session_id
        screenshot_number += 1
        path.write_bytes(f"png-{screenshot_number}".encode())

    def fake_http_json(
        url: str, method: str = "GET", payload: dict | None = None, **kwargs: object
    ) -> dict:
        del method, payload, kwargs
        if url.endswith("/appium/device/current_package"):
            return {"value": "com.soulfree.happiness"}
        if url.endswith("/appium/device/current_activity"):
            return {"value": "LaunchSplashActivity"}
        if url.endswith("/source"):
            return {
                "value": "<hierarchy resource-id='com.soulfree.happiness:id/dtv_time'>"
                + "x" * 120
                + "</hierarchy>"
            }
        return {"value": True}

    monkeypatch.setattr("scripts.run_mobile_ci.capture_screenshot", fake_screenshot)
    monkeypatch.setattr("scripts.run_mobile_ci.http_json", fake_http_json)
    workflow = {
        "enabled": True,
        "id": "startup-pages",
        "steps": [
            {
                "name": "Repeated startup",
                "action": "assert_startup_pages",
                "attempts": 3,
                "capture_delay_seconds": 0,
                "required_source_contains": "com.soulfree.happiness:id/dtv_time",
            }
        ],
    }

    status, message, steps, attachments = run_workflow(
        "http://127.0.0.1:4723",
        "session",
        workflow,
        tmp_path,
        runtime={"app_package": "com.soulfree.happiness"},
    )

    comparison = steps[0]["details"]["startup_pages"]
    assert status == "PASSED"
    assert message == "workflow passed with 1 steps"
    assert comparison["normal_launches"] == 3
    assert comparison["unique_screenshots"] == 3
    assert comparison["pages_varied"] is True
    assert all(sample["required_marker_present"] for sample in comparison["samples"])
    assert len(attachments) == 6


def test_mobile_network_simulation_is_blocked_on_physical_device(tmp_path: Path) -> None:
    workflow = {
        "enabled": True,
        "steps": [{"name": "Disconnect", "action": "network_off"}],
    }

    status, message, steps, _ = run_workflow(
        "http://127.0.0.1:4723",
        "session",
        workflow,
        tmp_path,
        runtime={"device_kind": "physical"},
        safety={"allow_network_changes": True},
    )

    assert status == "BLOCKED"
    assert "only on an Android emulator" in message
    assert steps[0]["status"] == "BLOCKED"


def test_android_startup_and_frame_metrics_are_parsed() -> None:
    startup = parse_startup_timing(
        "Status: ok\nThisTime: 120\nTotalTime: 180\nWaitTime: 190\n"
    )
    first_frame = ["0", "1000000000", *("0" for _ in range(14)), "1010000000"]
    second_frame = ["0", "1020000000", *("0" for _ in range(14)), "1050000000"]
    graphics = parse_gfxinfo_framestats(
        ",".join(first_frame) + "\n" + ",".join(second_frame)
    )

    assert startup["total_time_ms"] == 180
    assert graphics["rendered_frames"] == 2
    assert graphics["janky_frames"] == 1
    assert graphics["jank_percent"] == 50.0

    android_16 = "\n".join(
        [
            "Flags,FrameTimelineVsyncId,IntendedVsync,Vsync,InputEventId,"
            "HandleInputStart,AnimationStart,PerformTraversalsStart,DrawStart,"
            "FrameDeadline,FrameStartTime,FrameInterval,WorkloadTarget,SyncQueued,"
            "SyncStart,IssueDrawCommandsStart,SwapBuffers,FrameCompleted,",
            "0,1,2000000000,2000000000,0,0,0,0,0,0,0,0,0,0,0,0,0,2010000000,",
            "0,2,2016666667,2016666667,0,0,0,0,0,0,0,0,0,0,0,0,0,2036666667,",
        ]
    )
    android_16_graphics = parse_gfxinfo_framestats(android_16)

    assert android_16_graphics["rendered_frames"] == 2
    assert android_16_graphics["janky_frames"] == 1


def test_android_performance_thresholds_report_failures() -> None:
    result = evaluate_performance(
        {"cold": {"total_time_ms": 3200}, "warm": {"total_time_ms": 900}},
        {"total_pss_kb": 100000},
        {
            "total_pss_kb": 170000,
            "process_cpu_percent": 25,
            "graphics": {"estimated_fps": 42, "jank_percent": 30},
        },
        {
            "max_cold_start_ms": 3000,
            "max_warm_start_ms": 1500,
            "max_memory_growth_kb": 50000,
            "min_fps": 45,
            "max_jank_percent": 20,
        },
    )

    assert result["status"] == "FAIL"
    failed = {check["name"] for check in result["checks"] if check["status"] == "FAIL"}
    assert failed == {
        "cold_start_ms",
        "memory_growth_kb",
        "estimated_fps",
        "jank_percent",
    }


def test_android_runtime_health_scopes_crashes_to_target_package() -> None:
    healthy = parse_runtime_health(
        "FATAL EXCEPTION: main\nProcess: com.other.app, PID: 1",
        "com.example.app",
    )
    failed = parse_runtime_health(
        "FATAL EXCEPTION: main\nProcess: com.example.app, PID: 2\n"
        "java.lang.OutOfMemoryError",
        "com.example.app",
    )

    assert healthy["status"] == "PASS"
    assert failed["status"] == "FAIL"
    assert {signal["type"] for signal in failed["signals"]} == {
        "fatal_exception",
        "out_of_memory",
    }


def test_android_top_cpu_is_parsed_for_target_process() -> None:
    output = (
        "  PID USER PR NI VIRT RES SHR S[%CPU] %MEM TIME+ ARGS\n"
        "30445 u0_a282 10 -10 19G 422M 240M S 88.8 5.6 1:24.62 com.example.app\n"
    )

    assert parse_top_cpu(output, "com.example.app") == {
        "process_cpu_percent": 88.8,
        "cpu_source": "top",
    }
