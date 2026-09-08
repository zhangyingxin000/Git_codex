from __future__ import annotations

import json
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts.manage_android_emulator import build_emulator_command
from scripts.prepare_android_apk import acquire_apk, inspect_apk, sha256_file, source_label
from scripts.run_mobile_ci import (
    collect_device_preflight,
    merge_device_sources,
    parse_battery_level,
    parse_data_free_mb,
    parse_device_inventory,
    report_device,
    run_workflow,
)

ROOT = Path(__file__).resolve().parents[1]


def fake_apk(path: Path) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("AndroidManifest.xml", b"manifest")
        archive.writestr("classes.dex", b"dex")
    return path


def test_apk_acquisition_copies_validates_and_records_immutable_metadata(tmp_path: Path) -> None:
    source = fake_apk(tmp_path / "source.apk")
    output = tmp_path / "artifacts"

    metadata = acquire_apk(str(source), output, "jenkins-42")

    copied = Path(str(metadata["apk_path"]))
    assert copied.is_file()
    assert copied != source
    assert metadata["sha256"] == sha256_file(copied)
    assert Path((output / "current-apk.path").read_text(encoding="utf-8")).is_file()
    metadata_path = Path(
        (output / "current-apk-metadata.path").read_text(encoding="utf-8")
    )
    assert json.loads(metadata_path.read_text(encoding="utf-8"))["build_id"] == "jenkins-42"


def test_apk_acquisition_rejects_html_and_checksum_mismatch(tmp_path: Path) -> None:
    html = tmp_path / "download.apk"
    html.write_text("<html>download page</html>", encoding="utf-8")
    with pytest.raises(ValueError, match="direct APK URL"):
        acquire_apk(str(html), tmp_path / "html-output", "html")

    source = fake_apk(tmp_path / "source.apk")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        acquire_apk(
            str(source),
            tmp_path / "checksum-output",
            "checksum",
            expected_sha256="0" * 64,
        )


def test_apk_source_label_removes_url_credentials_and_query_values() -> None:
    assert source_label("https://user:password@downloads.example.com/app.apk?token=secret") == (
        "https://downloads.example.com/app.apk"
    )


def test_apk_metadata_does_not_confuse_sdk_codename_with_package_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    apk = fake_apk(tmp_path / "source.apk")
    monkeypatch.setattr("scripts.prepare_android_apk.find_aapt", lambda: Path("aapt2"))
    monkeypatch.setattr(
        "scripts.prepare_android_apk.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout=(
                "package: name='com.example.app' versionCode='42' versionName='1.2.3' "
                "compileSdkVersionCodename='16'\n"
            ),
            stderr="",
        ),
    )

    assert inspect_apk(apk) == {
        "package_name": "com.example.app",
        "version_code": "42",
        "version_name": "1.2.3",
    }


def test_android_emulator_command_has_stable_ci_ports_and_headless_flags() -> None:
    command = build_emulator_command(Path("emulator"), "Pixel_7_API_34", 5556)

    assert command[:5] == ["emulator", "-avd", "Pixel_7_API_34", "-port", "5556"]
    assert "-no-window" in command
    assert "-no-audio" in command
    assert "-wipe-data" not in command


def test_android_device_preflight_parses_and_enforces_device_health(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outputs = {
        ("get-state",): "device\n",
        ("shell", "getprop", "sys.boot_completed"): "1\n",
        ("shell", "dumpsys", "battery"): "level: 83\n",
        ("shell", "df", "-k", "/data"): (
            "Filesystem 1K-blocks Used Available Use% Mounted on\n"
            "/dev/block/data 10000000 1000000 9000000 10% /data\n"
        ),
        ("shell", "getprop", "ro.product.manufacturer"): "samsung\n",
        ("shell", "getprop", "ro.build.version.release"): "14\n",
        ("shell", "getprop", "ro.build.version.sdk"): "34\n",
        ("shell", "wm", "size"): "Physical size: 1080x2340\n",
    }

    def fake_run_adb(
        adb_path: str,
        udid: str,
        arguments: list[str],
        timeout_seconds: int = 30,
        check: bool = True,
    ) -> str:
        del adb_path, udid, timeout_seconds, check
        return outputs.get(tuple(arguments), "")

    monkeypatch.setattr("scripts.run_mobile_ci.run_adb", fake_run_adb)
    result = collect_device_preflight(
        "adb",
        {"udid": "phone-1", "model": "SM_A546B", "kind": "physical"},
        {"min_battery_percent": 20, "min_data_free_mb": 512},
    )

    assert parse_battery_level("level: 83") == 83
    assert parse_data_free_mb(outputs[("shell", "df", "-k", "/data")]) == 8789
    assert result["status"] == "PASS"
    assert result["android_version"] == "14"


def test_grid_inventory_merges_with_adb_without_exposing_capability_values() -> None:
    inventory = parse_device_inventory(
        json.dumps(
            [
                {
                    "udid": "emulator-5554",
                    "model": "Pixel_8_API_35",
                    "kind": "emulator",
                    "capabilities": {
                        "appium:systemPort": 8201,
                        "vendor:accessKey": "secret-value",
                    },
                }
            ]
        )
    )
    merged = merge_device_sources(
        [{"udid": "phone-1", "model": "SM_A546B", "kind": "physical"}],
        inventory,
    )

    assert [item["udid"] for item in merged] == ["phone-1", "emulator-5554"]
    assert merged[1]["capabilities"]["appium:systemPort"] == 8201
    assert report_device(merged[1])["capability_names"] == [
        "appium:systemPort",
        "vendor:accessKey",
    ]
    assert "secret-value" not in json.dumps(report_device(merged[1]))


def test_monkey_is_gated_and_records_a_reproducible_seed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workflow = {
        "enabled": True,
        "id": "monkey",
        "steps": [
            {
                "name": "Monkey",
                "action": "adb_monkey",
                "mutates_data": True,
                "risk_level": "high",
                "events": 25,
                "seed": 42,
                "throttle_ms": 0,
            }
        ],
    }
    blocked = run_workflow(
        "http://127.0.0.1:4723",
        "session",
        workflow,
        tmp_path,
        runtime={"adb_path": "adb", "udid": "emulator-5554", "app_package": "app"},
        safety={"allow_mutations": False, "allow_high_risk": False, "allow_monkey": False},
    )
    assert blocked[0] == "BLOCKED"
    assert "data mutation is disabled" in blocked[1]

    monkeypatch.setattr(
        "scripts.run_mobile_ci.run_adb",
        lambda *args, **kwargs: "Events injected: 25\nMonkey finished",
    )
    status, _, steps, attachments = run_workflow(
        "http://127.0.0.1:4723",
        "session",
        workflow,
        tmp_path,
        runtime={"adb_path": "adb", "udid": "emulator-5554", "app_package": "app"},
        safety={"allow_mutations": True, "allow_high_risk": True, "allow_monkey": True},
    )

    assert status == "PASSED"
    assert steps[0]["details"]["monkey"]["seed"] == 42
    assert steps[0]["details"]["monkey"]["injected_events"] == 25
    assert attachments[0][1].is_file()


def test_grid_workflow_falls_back_to_appium_for_swipe_and_background(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[tuple[str, str, dict | None]] = []

    def fake_http_json(
        url: str,
        method: str = "GET",
        payload: dict | None = None,
        timeout_seconds: int = 30,
    ) -> dict:
        del timeout_seconds
        requests.append((url, method, payload))
        return {}

    monkeypatch.setattr("scripts.run_mobile_ci.http_json", fake_http_json)
    workflow = {
        "enabled": True,
        "id": "grid-gestures",
        "steps": [
            {
                "name": "Remote swipe",
                "action": "swipe",
                "repeat": 1,
                "pause_seconds": 0,
                "measure_rendering": True,
            },
            {"name": "Remote background", "action": "background", "seconds": 0},
        ],
    }

    status, _, steps, _ = run_workflow(
        "http://grid:4444/wd/hub",
        "session-1",
        workflow,
        tmp_path,
        runtime={"adb_path": "", "udid": "grid-device", "app_package": "app"},
        safety={},
    )

    assert status == "PASSED"
    assert any(url.endswith("/actions") and method == "POST" for url, method, _ in requests)
    assert any(url.endswith("/press_keycode") for url, _, _ in requests)
    assert steps[0]["details"]["performance"]["status"] == "SKIPPED"


def test_hybrid_android_ci_assets_are_portable_and_registered() -> None:
    real = yaml.safe_load((ROOT / "config" / "mobile-ci.soulfree.yaml").read_text(encoding="utf-8"))
    emulator = yaml.safe_load(
        (ROOT / "config" / "mobile-ci.emulator.yaml").read_text(encoding="utf-8")
    )
    grid = yaml.safe_load(
        (ROOT / "config" / "mobile-ci.grid.yaml").read_text(encoding="utf-8")
    )
    monkey_scenario = yaml.safe_load(
        (ROOT / "mobile" / "scenarios" / "android-monkey.yaml").read_text(encoding="utf-8")
    )
    jenkins = (ROOT / "Jenkinsfile").read_text(encoding="utf-8")

    assert real["adb_path"] == ""
    assert real["server_mode"] == "managed"
    assert real["device_pool"]["source"] == "adb"
    assert real["device_pool"]["allow_physical"] is True
    assert emulator["server_mode"] == "managed"
    assert emulator["device_pool"]["source"] == "adb"
    assert emulator["device_pool"]["allow_emulators"] is True
    assert grid["server_mode"] == "external"
    assert grid["device_pool"]["source"] == "inventory"
    assert grid["device_preflight"]["enabled"] is False
    assert "githubPush()" in jenkins
    assert "Android Windows Emulator" in jenkins
    assert "Android Monkey Stability" in jenkins
    assert "setup-mobile.ps1 -SkipCiSetup" in jenkins
    assert "RUN_ANDROID_MONKEY" in jenkins
    assert "CONFIRM_ANDROID_MONKEY_ISOLATED_ENV" in jenkins
    assert "AUTOTEST_MOBILE_SCENARIOS" in jenkins
    assert "android-monkey-stability" in jenkins
    assert "AUTOTEST_MOBILE_ALLOW_MONKEY=true" in jenkins
    assert monkey_scenario["workflows"][0]["enabled"] is False
    assert monkey_scenario["workflows"][0]["steps"][0]["mutates_data"] is True
    assert "linux-android" not in jenkins
    assert "RUN_ANDROID_GRID" not in jenkins
    assert "reports/mobile-ci/**/pytest-junit.xml" in jenkins
