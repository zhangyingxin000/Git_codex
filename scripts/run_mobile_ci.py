from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

try:
    from scripts.mobile_observability import (
        build_performance_interpretation,
        collect_device_metrics,
        evaluate_performance,
        measure_app_start,
        parse_runtime_health,
        render_performance_interpretation,
        reset_graphics,
        resolve_launcher_component,
        run_adb,
    )
except ModuleNotFoundError:
    from mobile_observability import (  # type: ignore[no-redef]
        build_performance_interpretation,
        collect_device_metrics,
        evaluate_performance,
        measure_app_start,
        parse_runtime_health,
        render_performance_interpretation,
        reset_graphics,
        resolve_launcher_component,
        run_adb,
    )

ROOT = Path(__file__).resolve().parents[1]
ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
SENSITIVE_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "TICKET", "KEY")
ELEMENT_KEY = "element-6066-11e4-a52e-4f735466cecf"
SECRET_QUERY_PATTERN = re.compile(
    r"(?i)([?&](?:access_?token|id_?token|refresh_?token|token|ticket|password|secret|api_?key)=)([^&\s;]+)"
)
JWT_PATTERN = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
PLATFORM_SUPPORTED_SCOPE = [
    "登录、注册、支付和CRUD等业务流程模板",
    "文本、控件状态和页面跳转等UI断言",
    "前后台切换、重启、锁屏和来电等系统中断场景",
    "断网重连和弱网等模拟器网络场景",
    "冷/热启动、CPU、PSS内存、FPS、卡顿帧、OOM、崩溃和ANR采集",
]


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def definition_path(value: str, config_path: Path, project_root: Path | None = None) -> Path:
    boundary = (project_root or ROOT).resolve()
    if project_root is None and boundary not in config_path.resolve().parents:
        boundary = config_path.resolve().parent
    candidate = Path(value)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        root_candidate = (boundary / candidate).resolve()
        config_candidate = (config_path.parent / candidate).resolve()
        resolved = root_candidate if root_candidate.is_file() else config_candidate
    if resolved != boundary and boundary not in resolved.parents:
        raise ValueError(f"mobile definition must stay inside the project: {value}")
    if not resolved.is_file():
        raise FileNotFoundError(f"mobile definition does not exist: {resolved}")
    return resolved


def load_mobile_assets(
    config: dict[str, Any],
    config_path: Path,
    project_root: Path | None = None,
) -> dict[str, Any]:
    merged = copy.deepcopy(config)
    pages: dict[str, dict[str, Any]] = {}
    for value in merged.get("page_object_files") or []:
        source = definition_path(str(value), config_path, project_root)
        document = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
        if str(document.get("schema_version") or "") != "1.0":
            raise ValueError(f"mobile page object schema_version must be 1.0: {source}")
        source_pages = document.get("pages") or {}
        if not isinstance(source_pages, dict):
            raise TypeError(f"mobile page object pages must be an object: {source}")
        duplicates = set(pages).intersection(source_pages)
        if duplicates:
            raise ValueError(f"duplicate mobile page objects: {', '.join(sorted(duplicates))}")
        pages.update(copy.deepcopy(source_pages))

    workflows: list[dict[str, Any]] = []
    for value in merged.get("scenario_files") or []:
        source = definition_path(str(value), config_path, project_root)
        document = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
        if str(document.get("schema_version") or "") != "1.0":
            raise ValueError(f"mobile scenario schema_version must be 1.0: {source}")
        source_workflows = document.get("workflows") or []
        if not isinstance(source_workflows, list) or any(
            not isinstance(item, dict) for item in source_workflows
        ):
            raise TypeError(f"mobile scenario workflows must be a list: {source}")
        workflows.extend(copy.deepcopy(source_workflows))

    embedded = merged.get("workflows")
    if embedded is not None:
        if not isinstance(embedded, list) or any(not isinstance(item, dict) for item in embedded):
            raise TypeError("mobile CI workflows must be a list of objects")
        workflows.extend(copy.deepcopy(embedded))
    elif isinstance(merged.get("workflow"), dict) and merged.get("workflow"):
        workflows.append(copy.deepcopy(merged["workflow"]))

    for workflow in workflows:
        for step in workflow.get("steps") or []:
            target = str(step.get("target") or "").strip()
            if not target:
                continue
            if "." not in target:
                raise ValueError(f"mobile target must use page.element format: {target}")
            page_name, element_name = target.split(".", 1)
            page = pages.get(page_name)
            locator = page.get(element_name) if isinstance(page, dict) else None
            if not isinstance(locator, dict):
                raise ValueError(f"mobile page object was not found: {target}")
            step.setdefault("by", locator.get("by") or "id")
            step.setdefault("value", locator.get("value") or "")
            step["page_object"] = target

    merged["pages"] = pages
    merged["workflows"] = workflows
    merged.pop("workflow", None)
    return merged


def expand(value: Any, environment: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {key: expand(item, environment) for key, item in value.items()}
    if isinstance(value, list):
        return [expand(item, environment) for item in value]
    if not isinstance(value, str):
        return value
    missing: list[str] = []

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if not environment.get(name):
            missing.append(name)
            return match.group(0)
        return environment[name]

    result = ENV_PATTERN.sub(replace, value)
    if missing:
        raise ValueError(f"missing environment variables: {', '.join(sorted(set(missing)))}")
    return result


def find_adb(configured: str = "") -> str | None:
    candidates = []
    if configured:
        candidates.append(Path(configured))
    for name in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        if os.environ.get(name):
            sdk_root = Path(os.environ[name])
            candidates.extend(
                [sdk_root / "platform-tools" / "adb.exe", sdk_root / "platform-tools" / "adb"]
            )
    if os.environ.get("LOCALAPPDATA"):
        candidates.append(Path(os.environ["LOCALAPPDATA"]) / "Android" / "Sdk" / "platform-tools" / "adb.exe")
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return shutil.which("adb")


def project_node_cli(name: str) -> Path:
    candidates = [
        ROOT / "node_modules" / ".bin" / f"{name}.cmd",
        ROOT / "node_modules" / ".bin" / name,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0] if os.name == "nt" else candidates[1]


def sdk_root_from_adb(adb_path: str) -> str | None:
    path = Path(adb_path).resolve()
    if path.parent.name.lower() != "platform-tools":
        return None
    return str(path.parent.parent)


def parse_adb_devices(output: str) -> list[dict[str, Any]]:
    devices: list[dict[str, Any]] = []
    for line in output.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 2 or parts[1] != "device":
            continue
        metadata = {
            key: value
            for item in parts[2:]
            if ":" in item
            for key, value in [item.split(":", 1)]
        }
        udid = parts[0]
        devices.append(
            {
                "udid": udid,
                "model": metadata.get("model", udid),
                "kind": "emulator" if udid.startswith("emulator-") else "physical",
            }
        )
    return devices


def parse_device_inventory(value: Any) -> list[dict[str, Any]]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"mobile device inventory is not valid JSON: {exc}") from exc
    if not isinstance(value, list):
        raise TypeError("mobile device inventory must be a list")

    devices: list[dict[str, Any]] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise TypeError(f"mobile device inventory item {index} must be an object")
        udid = str(item.get("udid") or "").strip()
        if not udid:
            raise ValueError(f"mobile device inventory item {index} requires udid")
        capabilities = item.get("capabilities") or {}
        if not isinstance(capabilities, dict):
            raise TypeError(
                f"mobile device inventory capabilities for {udid} must be an object"
            )
        kind = str(item.get("kind") or "").strip().lower()
        if not kind:
            kind = "emulator" if udid.startswith("emulator-") else "physical"
        if kind not in {"emulator", "physical", "remote"}:
            raise ValueError(f"unsupported mobile device kind for {udid}: {kind}")
        devices.append(
            {
                **item,
                "udid": udid,
                "model": str(item.get("model") or udid).strip(),
                "kind": kind,
                "capabilities": copy.deepcopy(capabilities),
                "source": str(item.get("source") or "inventory").strip(),
            }
        )
    return devices


def merge_device_sources(*groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for group in groups:
        for device in group:
            udid = str(device.get("udid") or "").strip()
            if not udid:
                continue
            if udid not in merged:
                order.append(udid)
            merged[udid] = {**merged.get(udid, {}), **device}
    return [merged[udid] for udid in order]


def select_devices(
    devices: list[dict[str, Any]],
    pool: dict[str, Any],
    requested_udid: str = "",
) -> list[dict[str, Any]]:
    mode = str(pool.get("mode") or ("listed" if requested_udid else "first")).lower()
    include = {str(value) for value in pool.get("include", []) if str(value).strip()}
    exclude = {str(value) for value in pool.get("exclude", []) if str(value).strip()}
    if requested_udid:
        include.add(requested_udid)
    selected = [
        device
        for device in devices
        if device["udid"] not in exclude
        and (pool.get("allow_physical", True) or device["kind"] != "physical")
        and (pool.get("allow_emulators", True) or device["kind"] != "emulator")
        and (not include or device["udid"] in include or device["model"] in include)
    ]
    if mode == "first":
        return selected[:1]
    if mode in {"all", "listed"}:
        return selected
    raise ValueError(f"unsupported device_pool mode: {mode}")


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "android-device"


def report_device(device: dict[str, Any]) -> dict[str, Any]:
    public = {
        key: device[key]
        for key in ("udid", "model", "kind", "source")
        if key in device
    }
    capabilities = device.get("capabilities") or {}
    if isinstance(capabilities, dict) and capabilities:
        public["capability_names"] = sorted(str(key) for key in capabilities)
    return public


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_battery_level(output: str) -> int | None:
    match = re.search(r"(?m)^\s*level:\s*(\d+)\s*$", output)
    return int(match.group(1)) if match else None


def parse_data_free_mb(output: str) -> int | None:
    for line in reversed(output.splitlines()):
        columns = line.split()
        percent_indexes = [index for index, value in enumerate(columns) if value.endswith("%")]
        if not percent_indexes:
            continue
        percent_index = percent_indexes[0]
        if percent_index < 2:
            continue
        try:
            return round(int(columns[percent_index - 1]) / 1024)
        except ValueError:
            continue
    return None


def collect_device_preflight(
    adb_path: str,
    device: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    udid = device["udid"]
    if config.get("enabled", True) is not True:
        return {**report_device(device), "status": "SKIPPED", "checks": []}
    if config.get("wake_and_unlock", True) is True:
        run_adb(adb_path, udid, ["shell", "input", "keyevent", "KEYCODE_WAKEUP"], check=False)
        run_adb(adb_path, udid, ["shell", "wm", "dismiss-keyguard"], check=False)
    state = run_adb(adb_path, udid, ["get-state"], check=False).strip()
    boot_completed = run_adb(
        adb_path, udid, ["shell", "getprop", "sys.boot_completed"], check=False
    ).strip()
    battery_level = parse_battery_level(
        run_adb(adb_path, udid, ["shell", "dumpsys", "battery"], check=False)
    )
    data_free_mb = parse_data_free_mb(
        run_adb(adb_path, udid, ["shell", "df", "-k", "/data"], check=False)
    )
    minimum_battery = int(config.get("min_battery_percent") or 0)
    minimum_data_free = int(config.get("min_data_free_mb") or 0)
    checks = [
        {"name": "adb_state", "actual": state, "expected": "device", "status": "PASS" if state == "device" else "FAIL"},
        {"name": "boot_completed", "actual": boot_completed, "expected": "1", "status": "PASS" if boot_completed == "1" else "FAIL"},
        {
            "name": "battery_percent",
            "actual": battery_level,
            "minimum": minimum_battery,
            "status": "PASS" if battery_level is None or battery_level >= minimum_battery else "FAIL",
        },
        {
            "name": "data_free_mb",
            "actual": data_free_mb,
            "minimum": minimum_data_free,
            "status": "PASS" if data_free_mb is None or data_free_mb >= minimum_data_free else "FAIL",
        },
    ]
    status = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    return {
        **report_device(device),
        "status": status,
        "manufacturer": run_adb(
            adb_path, udid, ["shell", "getprop", "ro.product.manufacturer"], check=False
        ).strip(),
        "android_version": run_adb(
            adb_path, udid, ["shell", "getprop", "ro.build.version.release"], check=False
        ).strip(),
        "sdk_level": run_adb(
            adb_path, udid, ["shell", "getprop", "ro.build.version.sdk"], check=False
        ).strip(),
        "screen_size": run_adb(adb_path, udid, ["shell", "wm", "size"], check=False).strip(),
        "checks": checks,
    }


def build_coverage_scope(
    config: dict[str, Any],
    workflows: list[dict[str, Any]],
    safety: dict[str, Any],
    device_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    declared = config.get("coverage") or {}
    if not isinstance(declared, dict):
        declared = {}
    selected = [
        {
            "id": str(workflow.get("id") or "mobile-workflow"),
            "name": str(workflow.get("name") or workflow.get("id") or "Mobile workflow"),
            "enabled": workflow.get("enabled", False) is True,
            "steps": [
                str(step.get("name") or step.get("action") or "Unnamed step")
                for step in workflow.get("steps") or []
                if isinstance(step, dict)
            ],
        }
        for workflow in workflows
    ]
    actual = []
    for device in device_results or []:
        steps = device.get("workflow_steps") or []
        actual.append(
            {
                "udid": device.get("udid") or "",
                "model": device.get("model") or "",
                "status": device.get("status") or "UNKNOWN",
                "passed_steps": [
                    step.get("name")
                    for step in steps
                    if str(step.get("status") or "").upper() == "PASSED"
                ],
                "blocked_steps": [
                    {
                        "name": step.get("name"),
                        "workflow_id": step.get("workflow_id") or "",
                        "reason": step.get("message") or "",
                    }
                    for step in steps
                    if str(step.get("status") or "").upper() == "BLOCKED"
                ],
                "failed_steps": [
                    {
                        "name": step.get("name"),
                        "workflow_id": step.get("workflow_id") or "",
                        "reason": step.get("message") or "",
                    }
                    for step in steps
                    if str(step.get("status") or "").upper() == "FAILED"
                ],
                "skipped_steps": [
                    {
                        "name": step.get("name"),
                        "workflow_id": step.get("workflow_id") or "",
                        "reason": step.get("message") or "",
                        "verification_status": "NOT_OBSERVED_THIS_RUN",
                    }
                    for step in steps
                    if str(step.get("status") or "").upper() == "SKIPPED"
                ],
            }
        )
    return {
        "platform_supported": declared.get("platform_supported") or PLATFORM_SUPPORTED_SCOPE,
        "current_project": {
            "name": declared.get("project_name") or "Current Android project",
            "selected_workflows": selected,
            "configured_scope": declared.get("configured_scope") or [],
            "explicitly_not_verified": declared.get("not_verified") or [],
            "registered_reproducible_scenarios": (
                declared.get("reproducible_scenarios") or []
            ),
        },
        "actual_verification": actual,
        "safety_gates": {
            "allow_mutations": bool_value(safety.get("allow_mutations")),
            "allow_high_risk": bool_value(safety.get("allow_high_risk")),
            "allow_network_changes": bool_value(safety.get("allow_network_changes")),
            "allow_system_events": bool_value(safety.get("allow_system_events")),
        },
        "claim_policy": (
            "Only steps recorded as PASSED in actual_verification are claimed as verified. "
            "Platform templates and configured scope do not represent executed results."
        ),
    }


def select_workflows(
    workflows: list[dict[str, Any]], requested: list[str]
) -> list[dict[str, Any]]:
    if not requested:
        return workflows
    requested_scenarios = set(requested)
    available_scenarios = {str(item.get("id") or "") for item in workflows}
    missing_scenarios = sorted(requested_scenarios - available_scenarios)
    if missing_scenarios:
        raise ValueError(f"mobile scenarios were not found: {', '.join(missing_scenarios)}")
    return [
        {**item, "enabled": True}
        for item in workflows
        if str(item.get("id") or "") in requested_scenarios
    ]


def select_server_port(host: str, preferred_port: int, auto_select: bool = True) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, preferred_port))
            return preferred_port
        except OSError:
            if not auto_select:
                raise RuntimeError(f"Appium port is already in use: {host}:{preferred_port}") from None
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind((host, 0))
        return int(probe.getsockname()[1])


def redact(text: str, environment: dict[str, str]) -> str:
    values = [
        value
        for name, value in environment.items()
        if value and len(value) >= 4 and any(marker in name.upper() for marker in SENSITIVE_MARKERS)
    ]
    for value in sorted(set(values), key=len, reverse=True):
        text = text.replace(value, "***")
    text = SECRET_QUERY_PATTERN.sub(r"\1***", text)
    return JWT_PATTERN.sub("***", text)


def http_json(
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        content = response.read().decode("utf-8")
        return json.loads(content) if content else {}


def wait_for_appium(status_url: str, timeout_seconds: int) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error = ""
    while time.monotonic() < deadline:
        try:
            payload = http_json(status_url)
            if payload.get("value", {}).get("ready") is not False:
                return
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        time.sleep(1)
    raise TimeoutError(f"Appium did not become ready: {last_error}")


def wait_for_package(server_url: str, session_id: str, expected: str, timeout_seconds: int) -> str:
    deadline = time.monotonic() + timeout_seconds
    current = ""
    while time.monotonic() < deadline:
        result = http_json(f"{server_url}/session/{session_id}/appium/device/current_package")
        current = str(result.get("value") or "")
        if not expected or current == expected:
            return current
        time.sleep(1)
    return current


def find_element(
    server_url: str,
    session_id: str,
    using: str,
    value: str,
    timeout_seconds: int,
) -> str | None:
    strategies = {
        "id": "id",
        "xpath": "xpath",
        "accessibility_id": "accessibility id",
        "class_name": "class name",
    }
    strategy = strategies.get(using, using)
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            result = http_json(
                f"{server_url}/session/{session_id}/element",
                "POST",
                {"using": strategy, "value": value},
            )
            element = result.get("value") or {}
            element_id = str(element.get(ELEMENT_KEY) or element.get("ELEMENT") or "")
            if element_id:
                return element_id
        except urllib.error.HTTPError:
            pass
        time.sleep(0.5)
    return None


def capture_screenshot(server_url: str, session_id: str, path: Path) -> None:
    result = http_json(f"{server_url}/session/{session_id}/screenshot")
    value = str(result.get("value") or "")
    if not value:
        raise RuntimeError("Appium returned an empty screenshot")
    path.write_bytes(base64.b64decode(value))


def element_attribute(server_url: str, session_id: str, element_id: str, name: str) -> Any:
    result = http_json(
        f"{server_url}/session/{session_id}/element/{element_id}/attribute/{name}"
    )
    return result.get("value")


def current_activity(server_url: str, session_id: str) -> str:
    result = http_json(f"{server_url}/session/{session_id}/appium/device/current_activity")
    return str(result.get("value") or "")


def current_package(server_url: str, session_id: str) -> str:
    result = http_json(f"{server_url}/session/{session_id}/appium/device/current_package")
    return str(result.get("value") or "")


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def safety_block_reason(
    step: dict[str, Any],
    action: str,
    safety: dict[str, Any],
    runtime: dict[str, Any],
) -> str:
    required = step.get("requires") or []
    if isinstance(required, str):
        required = [required]
    missing = [name for name in required if not os.environ.get(str(name))]
    if missing:
        return f"missing required resources: {', '.join(sorted(map(str, missing)))}"
    if bool_value(step.get("mutates_data")) and not bool_value(safety.get("allow_mutations")):
        return "data mutation is disabled; set safety.allow_mutations only for an isolated test account"
    if str(step.get("risk_level") or "low").lower() == "high" and not bool_value(
        safety.get("allow_high_risk")
    ):
        return "high-risk mobile action is disabled"
    if action == "adb_monkey" and not bool_value(safety.get("allow_monkey")):
        return "Monkey stability execution is disabled"
    if action in {"network_off", "network_on", "network_profile", "network_restore"}:
        if not bool_value(safety.get("allow_network_changes")):
            return "network changes are disabled"
        if runtime.get("device_kind") != "emulator":
            return "network simulation is supported only on an Android emulator"
    if action in {"incoming_call", "end_call", "lock", "unlock"}:
        if not bool_value(safety.get("allow_system_events")):
            return "system-event simulation is disabled"
        if action in {"incoming_call", "end_call"} and runtime.get("device_kind") != "emulator":
            return "incoming-call simulation is supported only on an Android emulator"
    return ""


def assert_expected(actual: Any, step: dict[str, Any], label: str) -> str:
    expected = step.get("expected")
    contains = step.get("contains")
    matches = step.get("matches")
    actual_text = "" if actual is None else str(actual)
    if expected is not None and actual_text != str(expected):
        raise AssertionError(f"{label} was {actual_text!r}, expected {str(expected)!r}")
    if contains is not None and str(contains) not in actual_text:
        raise AssertionError(f"{label} did not contain {str(contains)!r}: {actual_text!r}")
    if matches is not None and not re.search(str(matches), actual_text):
        raise AssertionError(f"{label} did not match {str(matches)!r}: {actual_text!r}")
    if expected is None and contains is None and matches is None:
        raise ValueError(f"{label} assertion requires expected, contains, or matches")
    return actual_text


def run_workflow(
    server_url: str,
    session_id: str,
    workflow: dict[str, Any],
    device_root: Path,
    runtime: dict[str, Any] | None = None,
    safety: dict[str, Any] | None = None,
) -> tuple[str, str, list[dict[str, Any]], list[tuple[str, Path, str]]]:
    if workflow.get("enabled", False) is not True:
        return "SKIPPED", "mobile workflow is disabled", [], []
    steps = workflow.get("steps") or []
    if not isinstance(steps, list) or not steps:
        raise ValueError("enabled mobile workflow must contain steps")

    results: list[dict[str, Any]] = []
    attachments: list[tuple[str, Path, str]] = []
    runtime = runtime or {}
    safety = safety or {}
    workflow_id = safe_name(str(workflow.get("id") or "mobile-workflow"))
    adb_path = str(runtime.get("adb_path") or "")
    udid = str(runtime.get("udid") or "")
    app_package = str(runtime.get("app_package") or "")
    network_disabled = False
    network_profile_changed = False
    call_active = False
    call_phone = "5551234"
    workflow_status = "PASSED"
    workflow_message = ""
    for index, raw_step in enumerate(steps, start=1):
        if not isinstance(raw_step, dict):
            raise ValueError(f"workflow step {index} must be an object")
        action = str(raw_step.get("action") or "").strip().lower()
        name = str(raw_step.get("name") or f"Step {index}")
        started_ms = int(time.time() * 1000)
        step_status = "PASSED"
        step_message = ""
        step_details: dict[str, Any] = {}
        block_reason = safety_block_reason(raw_step, action, safety, runtime)
        if block_reason:
            step_status = "BLOCKED"
            step_message = block_reason
            stopped_ms = int(time.time() * 1000)
            results.append(
                {
                    "name": name,
                    "action": action,
                    "category": str(raw_step.get("category") or workflow.get("category") or "business"),
                    "risk_level": str(raw_step.get("risk_level") or "low"),
                    "mutates_data": bool_value(raw_step.get("mutates_data")),
                    "status": step_status,
                    "message": step_message,
                    "start": started_ms,
                    "stop": stopped_ms,
                }
            )
            workflow_status = "BLOCKED"
            workflow_message = f"workflow blocked at step {index}: {name}: {block_reason}"
            break
        try:
            if action == "wait":
                seconds = float(raw_step.get("seconds") or 1)
                time.sleep(seconds)
                step_message = f"waited {seconds:g} seconds"
            elif action in {
                "click",
                "click_optional",
                "input",
                "input_optional",
                "assert_present",
                "assert_text",
                "assert_attribute",
                "assert_enabled",
                "assert_disabled",
            }:
                using = str(raw_step.get("by") or "id")
                selector = str(raw_step.get("value") or "")
                if not selector:
                    raise ValueError(f"{action} requires a selector value")
                element_id = find_element(
                    server_url,
                    session_id,
                    using,
                    selector,
                    int(raw_step.get("timeout_seconds") or 10),
                )
                optional = action.endswith("_optional")
                if not element_id:
                    if optional:
                        step_status = "SKIPPED"
                        step_message = f"optional element was not present: {selector}"
                    else:
                        raise AssertionError(f"element was not present: {selector}")
                elif action.startswith("click"):
                    http_json(
                        f"{server_url}/session/{session_id}/element/{element_id}/click",
                        "POST",
                        {},
                    )
                    step_message = f"clicked {selector}"
                elif action.startswith("input"):
                    text_environment_name = str(raw_step.get("text_env") or "").strip()
                    text_value = (
                        os.environ.get(text_environment_name, "")
                        if text_environment_name
                        else str(raw_step.get("text") or "")
                    )
                    if text_environment_name and not text_value:
                        raise ValueError(
                            f"input environment variable is empty: {text_environment_name}"
                        )
                    if raw_step.get("clear", True):
                        http_json(
                            f"{server_url}/session/{session_id}/element/{element_id}/clear",
                            "POST",
                            {},
                        )
                    http_json(
                        f"{server_url}/session/{session_id}/element/{element_id}/value",
                        "POST",
                        {"text": text_value, "value": list(text_value)},
                    )
                    step_message = f"entered {len(text_value)} characters"
                elif action == "assert_text":
                    text_result = http_json(
                        f"{server_url}/session/{session_id}/element/{element_id}/text"
                    )
                    actual_text = assert_expected(text_result.get("value"), raw_step, "element text")
                    step_message = f"text assertion passed: {actual_text!r}"
                elif action == "assert_attribute":
                    attribute_name = str(raw_step.get("attribute") or "")
                    if not attribute_name:
                        raise ValueError("assert_attribute requires attribute")
                    actual_value = element_attribute(
                        server_url, session_id, element_id, attribute_name
                    )
                    assert_expected(actual_value, raw_step, f"element attribute {attribute_name}")
                    step_message = f"attribute assertion passed: {attribute_name}={actual_value!r}"
                elif action in {"assert_enabled", "assert_disabled"}:
                    enabled = bool_value(
                        element_attribute(server_url, session_id, element_id, "enabled")
                    )
                    expected_enabled = action == "assert_enabled"
                    if enabled != expected_enabled:
                        raise AssertionError(
                            f"element enabled state was {enabled}, expected {expected_enabled}"
                        )
                    step_message = f"element enabled state is {enabled}"
                else:
                    step_message = f"found {selector}"
            elif action == "assert_not_present":
                using = str(raw_step.get("by") or "id")
                selector = str(raw_step.get("value") or "")
                if not selector:
                    raise ValueError("assert_not_present requires a selector value")
                element_id = find_element(
                    server_url,
                    session_id,
                    using,
                    selector,
                    int(raw_step.get("timeout_seconds") or 3),
                )
                if element_id:
                    raise AssertionError(f"element was unexpectedly present: {selector}")
                step_message = f"element was absent as expected: {selector}"
            elif action == "assert_activity":
                actual_activity = current_activity(server_url, session_id)
                assert_expected(actual_activity, raw_step, "current activity")
                step_message = f"activity assertion passed: {actual_activity}"
            elif action == "assert_package":
                actual_package = current_package(server_url, session_id)
                assert_expected(actual_package, raw_step, "current package")
                step_message = f"package assertion passed: {actual_package}"
            elif action == "back":
                http_json(f"{server_url}/session/{session_id}/back", "POST", {})
                step_message = "pressed Android back"
            elif action == "swipe":
                measure_rendering = bool_value(raw_step.get("measure_rendering"))
                if measure_rendering and adb_path and udid:
                    if not app_package:
                        raise ValueError("rendering measurement requires the expected app package")
                    reset_graphics(adb_path, udid, app_package)
                start_x = int(raw_step.get("start_x") or 500)
                start_y = int(raw_step.get("start_y") or 1500)
                end_x = int(raw_step.get("end_x") or 500)
                end_y = int(raw_step.get("end_y") or 400)
                duration_ms = int(raw_step.get("duration_ms") or 400)
                repeat = max(1, int(raw_step.get("repeat") or 1))
                pause_seconds = float(raw_step.get("pause_seconds") or 0.2)
                for _ in range(repeat):
                    if adb_path and udid:
                        run_adb(
                            adb_path,
                            udid,
                            [
                                "shell",
                                "input",
                                "swipe",
                                str(start_x),
                                str(start_y),
                                str(end_x),
                                str(end_y),
                                str(duration_ms),
                            ],
                        )
                    else:
                        http_json(
                            f"{server_url}/session/{session_id}/actions",
                            "POST",
                            {
                                "actions": [
                                    {
                                        "type": "pointer",
                                        "id": "finger1",
                                        "parameters": {"pointerType": "touch"},
                                        "actions": [
                                            {
                                                "type": "pointerMove",
                                                "duration": 0,
                                                "origin": "viewport",
                                                "x": start_x,
                                                "y": start_y,
                                            },
                                            {"type": "pointerDown", "button": 0},
                                            {"type": "pause", "duration": 100},
                                            {
                                                "type": "pointerMove",
                                                "duration": duration_ms,
                                                "origin": "viewport",
                                                "x": end_x,
                                                "y": end_y,
                                            },
                                            {"type": "pointerUp", "button": 0},
                                        ],
                                    }
                                ]
                            },
                        )
                        http_json(
                            f"{server_url}/session/{session_id}/actions",
                            "DELETE",
                        )
                    time.sleep(max(pause_seconds, 0.0))
                if measure_rendering and adb_path and udid:
                    step_details["performance"] = collect_device_metrics(
                        adb_path,
                        udid,
                        app_package,
                        include_graphics=True,
                        frame_budget_ms=float(raw_step.get("frame_budget_ms") or 16.67),
                    )
                elif measure_rendering:
                    step_details["performance"] = {
                        "status": "SKIPPED",
                        "reason": "Grid gesture passed but rendering metrics require ADB",
                    }
                step_message = f"performed {repeat} swipe gesture(s)"
            elif action == "background":
                if adb_path and udid:
                    run_adb(adb_path, udid, ["shell", "input", "keyevent", "KEYCODE_HOME"])
                else:
                    http_json(
                        f"{server_url}/session/{session_id}/appium/device/press_keycode",
                        "POST",
                        {"keycode": 3},
                    )
                seconds = float(raw_step.get("seconds") or 2)
                time.sleep(max(seconds, 0.0))
                step_message = f"sent app to background for {seconds:g} seconds"
            elif action in {"activate", "resume"}:
                if not app_package:
                    raise ValueError(f"{action} requires the expected app package")
                http_json(
                    f"{server_url}/session/{session_id}/appium/device/activate_app",
                    "POST",
                    {"appId": app_package},
                )
                time.sleep(float(raw_step.get("wait_seconds") or 1))
                step_message = f"activated {app_package}"
            elif action == "terminate":
                if not app_package:
                    raise ValueError("terminate requires the expected app package")
                http_json(
                    f"{server_url}/session/{session_id}/appium/device/terminate_app",
                    "POST",
                    {"appId": app_package},
                )
                step_message = f"terminated {app_package}"
            elif action == "relaunch":
                if not app_package:
                    raise ValueError("relaunch requires the expected app package")
                http_json(
                    f"{server_url}/session/{session_id}/appium/device/terminate_app",
                    "POST",
                    {"appId": app_package},
                )
                http_json(
                    f"{server_url}/session/{session_id}/appium/device/activate_app",
                    "POST",
                    {"appId": app_package},
                )
                time.sleep(float(raw_step.get("wait_seconds") or 2))
                step_message = f"restarted {app_package}"
            elif action == "assert_startup_pages":
                if not app_package:
                    raise ValueError("assert_startup_pages requires the expected app package")
                attempts = max(2, int(raw_step.get("attempts") or 3))
                capture_delay = max(0.0, float(raw_step.get("capture_delay_seconds") or 0.3))
                stop_settle = max(0.0, float(raw_step.get("force_stop_settle_seconds") or 0.5))
                launch_timeout = max(1, int(raw_step.get("launch_timeout_seconds") or 15))
                minimum_source_chars = max(1, int(raw_step.get("min_page_source_chars") or 100))
                required_source_contains = str(
                    raw_step.get("required_source_contains") or ""
                ).strip()
                require_variation = bool_value(raw_step.get("require_variation"))
                samples: list[dict[str, Any]] = []
                screenshot_hashes: set[str] = set()
                source_hashes: set[str] = set()
                for attempt in range(1, attempts + 1):
                    if adb_path and udid:
                        run_adb(
                            adb_path,
                            udid,
                            ["shell", "am", "force-stop", app_package],
                        )
                    else:
                        http_json(
                            f"{server_url}/session/{session_id}/appium/device/terminate_app",
                            "POST",
                            {"appId": app_package},
                        )
                    time.sleep(stop_settle)
                    http_json(
                        f"{server_url}/session/{session_id}/appium/device/activate_app",
                        "POST",
                        {"appId": app_package},
                    )
                    wait_for_package(
                        server_url,
                        session_id,
                        app_package,
                        launch_timeout,
                    )
                    time.sleep(capture_delay)
                    observed_package = current_package(server_url, session_id)
                    observed_activity = current_activity(server_url, session_id)
                    source_result = http_json(f"{server_url}/session/{session_id}/source")
                    page_source = str(source_result.get("value") or "")
                    sample_source = (
                        device_root / f"{workflow_id}-step-{index:02d}-launch-{attempt:02d}.xml"
                    )
                    sample_screenshot = (
                        device_root / f"{workflow_id}-step-{index:02d}-launch-{attempt:02d}.png"
                    )
                    sample_source.write_text(page_source, encoding="utf-8")
                    capture_screenshot(server_url, session_id, sample_screenshot)
                    source_hash = hashlib.sha256(page_source.encode("utf-8")).hexdigest()
                    screenshot_hash = hashlib.sha256(sample_screenshot.read_bytes()).hexdigest()
                    source_hashes.add(source_hash)
                    screenshot_hashes.add(screenshot_hash)
                    attachments.append(
                        (f"{name} launch {attempt} screenshot", sample_screenshot, "image/png")
                    )
                    attachments.append(
                        (f"{name} launch {attempt} page source", sample_source, "application/xml")
                    )
                    sample = {
                        "attempt": attempt,
                        "package": observed_package,
                        "activity": observed_activity,
                        "page_source_chars": len(page_source),
                        "required_marker_present": (
                            required_source_contains in page_source
                            if required_source_contains
                            else None
                        ),
                        "source_sha256": source_hash,
                        "screenshot_sha256": screenshot_hash,
                        "screenshot": str(sample_screenshot),
                        "page_source": str(sample_source),
                    }
                    samples.append(sample)
                    if observed_package != app_package:
                        raise AssertionError(
                            f"launch {attempt} foreground package was {observed_package!r}, "
                            f"expected {app_package!r}"
                        )
                    if len(page_source) < minimum_source_chars:
                        raise AssertionError(
                            f"launch {attempt} page source had {len(page_source)} characters, "
                            f"expected at least {minimum_source_chars}"
                        )
                    if required_source_contains and required_source_contains not in page_source:
                        raise AssertionError(
                            f"launch {attempt} page source did not contain required marker "
                            f"{required_source_contains!r}"
                        )
                pages_varied = len(screenshot_hashes) > 1 or len(source_hashes) > 1
                step_details["startup_pages"] = {
                    "attempts": attempts,
                    "normal_launches": len(samples),
                    "unique_screenshots": len(screenshot_hashes),
                    "unique_page_sources": len(source_hashes),
                    "pages_varied": pages_varied,
                    "require_variation": require_variation,
                    "required_source_contains": required_source_contains,
                    "restart_mode": "adb_force_stop" if adb_path and udid else "appium_terminate",
                    "samples": samples,
                }
                if require_variation and not pages_varied:
                    raise AssertionError(
                        f"startup page was identical across {attempts} launches"
                    )
                variation_text = "different startup pages were observed" if pages_varied else "startup pages were identical"
                step_message = f"validated {attempts} normal launches; {variation_text}"
            elif action == "adb_monkey":
                if not adb_path or not udid or not app_package:
                    raise ValueError("adb_monkey requires ADB, a device and the expected package")
                events = max(1, int(raw_step.get("events") or 1000))
                seed = int(raw_step.get("seed") or 20260908)
                throttle_ms = max(0, int(raw_step.get("throttle_ms") or 200))
                timeout_seconds = int(
                    raw_step.get("timeout_seconds") or max(300, events * throttle_ms / 1000 + 120)
                )
                monkey_log = device_root / f"{workflow_id}-step-{index:02d}-monkey.log"
                monkey_output = run_adb(
                    adb_path,
                    udid,
                    [
                        "shell",
                        "monkey",
                        "-p",
                        app_package,
                        "-s",
                        str(seed),
                        "--throttle",
                        str(throttle_ms),
                        "--pct-syskeys",
                        str(int(raw_step.get("pct_syskeys") or 0)),
                        "--pct-appswitch",
                        str(int(raw_step.get("pct_appswitch") or 0)),
                        "--monitor-native-crashes",
                        "-v",
                        "-v",
                        str(events),
                    ],
                    timeout_seconds=timeout_seconds,
                )
                monkey_log.write_text(monkey_output, encoding="utf-8")
                attachments.append((f"{name} log", monkey_log, "text/plain"))
                failure_markers = re.findall(
                    r"(?im)^.*(?:CRASH:|ANR in|Monkey aborted|native crash).*$",
                    monkey_output,
                )
                injected_match = re.search(r"Events injected:\s*(\d+)", monkey_output)
                injected = int(injected_match.group(1)) if injected_match else None
                step_details["monkey"] = {
                    "seed": seed,
                    "requested_events": events,
                    "injected_events": injected,
                    "throttle_ms": throttle_ms,
                    "failure_markers": failure_markers,
                    "log": str(monkey_log),
                }
                if failure_markers:
                    raise AssertionError("Monkey reported a crash, ANR or aborted execution")
                if injected is not None and injected < events:
                    raise AssertionError(f"Monkey injected {injected}/{events} requested events")
                step_message = f"Monkey completed {injected or events} events with seed {seed}"
            elif action == "lock":
                http_json(
                    f"{server_url}/session/{session_id}/appium/device/lock",
                    "POST",
                    {"seconds": int(raw_step.get("seconds") or 2)},
                )
                step_message = "locked and resumed the device"
            elif action == "unlock":
                http_json(
                    f"{server_url}/session/{session_id}/appium/device/unlock", "POST", {}
                )
                step_message = "unlocked the device"
            elif action in {"incoming_call", "end_call"}:
                if not adb_path or not udid:
                    raise ValueError(f"{action} requires an ADB runtime")
                phone = str(raw_step.get("phone") or "5551234")
                call_phone = phone
                command = "call" if action == "incoming_call" else "cancel"
                run_adb(adb_path, udid, ["emu", "gsm", command, phone])
                call_active = action == "incoming_call"
                if action == "incoming_call" and bool_value(raw_step.get("auto_end", True)):
                    time.sleep(float(raw_step.get("seconds") or 2))
                    run_adb(adb_path, udid, ["emu", "gsm", "cancel", phone])
                    call_active = False
                step_message = f"emulator call event completed: {command}"
            elif action in {"network_off", "network_on"}:
                if not adb_path or not udid:
                    raise ValueError(f"{action} requires an ADB runtime")
                mode = "enable" if action == "network_off" else "disable"
                run_adb(
                    adb_path,
                    udid,
                    ["shell", "cmd", "connectivity", "airplane-mode", mode],
                )
                network_disabled = action == "network_off"
                time.sleep(float(raw_step.get("wait_seconds") or 1))
                step_message = f"emulator airplane mode {mode}d"
            elif action in {"network_profile", "network_restore"}:
                if not adb_path or not udid:
                    raise ValueError(f"{action} requires an ADB runtime")
                speed = "full" if action == "network_restore" else str(raw_step.get("speed") or "edge")
                delay = "none" if action == "network_restore" else str(raw_step.get("delay") or "gprs")
                run_adb(adb_path, udid, ["emu", "network", "speed", speed])
                run_adb(adb_path, udid, ["emu", "network", "delay", delay])
                network_profile_changed = action == "network_profile"
                step_message = f"emulator network profile set to speed={speed}, delay={delay}"
            elif action == "screenshot":
                screenshot_path = device_root / f"{workflow_id}-step-{index:02d}.png"
                capture_screenshot(server_url, session_id, screenshot_path)
                attachments.append((name, screenshot_path, "image/png"))
                step_message = f"captured {screenshot_path.name}"
            else:
                raise ValueError(f"unsupported workflow action: {action}")
        except Exception as exc:
            step_status = "FAILED"
            step_message = f"{type(exc).__name__}: {exc}"
            failure_path = device_root / f"{workflow_id}-step-{index:02d}-failed.png"
            failure_source_path = device_root / f"{workflow_id}-step-{index:02d}-failed.xml"
            try:
                capture_screenshot(server_url, session_id, failure_path)
                attachments.append((f"{name} failure", failure_path, "image/png"))
            except Exception:
                pass
            try:
                source_result = http_json(f"{server_url}/session/{session_id}/source")
                failure_source_path.write_text(
                    str(source_result.get("value") or ""), encoding="utf-8"
                )
                attachments.append(
                    (f"{name} failure page source", failure_source_path, "application/xml")
                )
            except Exception:
                pass

        stopped_ms = int(time.time() * 1000)
        results.append(
            {
                "name": name,
                "action": action,
                "category": str(raw_step.get("category") or workflow.get("category") or "business"),
                "risk_level": str(raw_step.get("risk_level") or "low"),
                "mutates_data": bool_value(raw_step.get("mutates_data")),
                "status": step_status,
                "message": step_message,
                "start": started_ms,
                "stop": stopped_ms,
                "details": step_details,
            }
        )
        if step_status == "FAILED":
            workflow_status = "FAILED"
            workflow_message = f"workflow failed at step {index}: {name}"
            break

    cleanup_errors: list[str] = []
    if call_active and adb_path and udid:
        try:
            run_adb(adb_path, udid, ["emu", "gsm", "cancel", call_phone])
        except Exception as exc:
            cleanup_errors.append(f"call cleanup failed: {exc}")
    if network_disabled and adb_path and udid:
        try:
            run_adb(
                adb_path,
                udid,
                ["shell", "cmd", "connectivity", "airplane-mode", "disable"],
            )
        except Exception as exc:
            cleanup_errors.append(f"network reconnect failed: {exc}")
    if network_profile_changed and adb_path and udid:
        try:
            run_adb(adb_path, udid, ["emu", "network", "speed", "full"])
            run_adb(adb_path, udid, ["emu", "network", "delay", "none"])
        except Exception as exc:
            cleanup_errors.append(f"network profile cleanup failed: {exc}")
    if cleanup_errors and workflow_status == "PASSED":
        workflow_status = "FAILED"
        workflow_message = "; ".join(cleanup_errors)
    if not workflow_message:
        workflow_message = f"workflow passed with {len(results)} steps"
    return workflow_status, workflow_message, results, attachments


def write_allure_result(
    results_dir: Path,
    status: str,
    message: str,
    started_ms: int,
    stopped_ms: int,
    device: dict[str, str] | None = None,
    attachments: list[tuple[str, Path, str]] | None = None,
    steps: list[dict[str, Any]] | None = None,
) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    result_id = str(uuid.uuid4())
    device = device or {"udid": "unassigned", "model": "Android", "kind": "unknown"}
    allure_attachments = []
    for name, path, mime_type in attachments or []:
        if not path.is_file():
            continue
        source = f"{uuid.uuid4()}-attachment{path.suffix}"
        shutil.copyfile(path, results_dir / source)
        allure_attachments.append({"name": name, "source": source, "type": mime_type})
    allure_status = "skipped" if status.lower() == "blocked" else status.lower()
    payload = {
        "uuid": result_id,
        "historyId": str(uuid.uuid5(uuid.NAMESPACE_URL, f"autotest-ai:android:{device['udid']}")),
        "testCaseId": str(uuid.uuid5(uuid.NAMESPACE_DNS, "autotest-ai:android-mobile-workflow")),
        "fullName": f"mobile.android.{safe_name(device['udid'])}.workflow",
        "name": f"Android Appium workflow [{device['model']}]",
        "status": allure_status,
        "stage": "finished",
        "statusDetails": {"message": message},
        "start": started_ms,
        "stop": stopped_ms,
        "labels": [
            {"name": "framework", "value": "appium"},
            {"name": "platform", "value": "android"},
            {"name": "suite", "value": "Mobile automation"},
            {"name": "device", "value": device["model"]},
            {"name": "device_udid", "value": device["udid"]},
            {"name": "device_type", "value": device["kind"]},
        ],
        "attachments": allure_attachments,
        "steps": [
            {
                "name": step["name"],
                "status": (
                    "skipped" if step["status"].lower() == "blocked" else step["status"].lower()
                ),
                "stage": "finished",
                "statusDetails": {"message": step["message"]},
                "start": step["start"],
                "stop": step["stop"],
            }
            for step in steps or []
        ],
    }
    (results_dir / f"{result_id}-result.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a local Android Appium CI session.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--report-root", type=Path, default=ROOT / "reports" / "mobile-ci")
    parser.add_argument("--scenario", action="append", default=[])
    parser.add_argument("--device", action="append", default=[])
    args = parser.parse_args(argv)

    config_path = args.config if args.config.is_absolute() else ROOT / args.config
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if str(config.get("schema_version") or "") != "1.0":
        raise SystemExit("mobile CI schema_version must be 1.0")
    config = load_mobile_assets(config, config_path, ROOT)

    run_id = f"mobile-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    report_root = args.report_root if args.report_root.is_absolute() else ROOT / args.report_root
    run_root = report_root / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    summary_path = run_root / "summary.json"
    coverage_path = run_root / "coverage-scope.json"
    started_at = utc_now()

    if config.get("enabled", False) is not True:
        summary = {
            "schema_version": "1.0",
            "report_type": "ANDROID_APPIUM_CI",
            "run_id": run_id,
            "status": "SKIPPED",
            "reason": "mobile CI is disabled",
            "started_at": started_at,
            "finished_at": utc_now(),
            "coverage": build_coverage_scope(
                config,
                config.get("workflows") or [],
                config.get("safety") or {},
            ),
        }
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Android Appium CI: SKIPPED\nSummary: {summary_path}")
        return 0

    environment = os.environ.copy()
    environment["APPIUM_HOME"] = str(ROOT / ".appium")
    environment["npm_config_cache"] = str(ROOT / ".npm-cache")
    environment["ANDROID_SDK_HOME"] = str(ROOT / ".android-home")
    environment["ANDROID_USER_HOME"] = str(ROOT / ".android-home" / ".android")
    environment["ANDROID_PREFS_ROOT"] = environment["ANDROID_USER_HOME"]
    appium = project_node_cli("appium")
    allure = project_node_cli("allure")
    log_path = run_root / "appium.log"
    apk_metadata_path = run_root / "apk-metadata.json"
    preflight_path = run_root / "device-preflight.json"
    results_dir = run_root / "allure-results"
    report_dir = run_root / "allure-report"
    started_ms = int(time.time() * 1000)
    appium_process: subprocess.Popen[str] | None = None
    log_handle: Any = None
    status = "FAILED"
    message = ""
    discovered_devices: list[dict[str, Any]] = []
    selected_devices: list[dict[str, Any]] = []
    device_results: list[dict[str, Any]] = []
    preflight_results: list[dict[str, Any]] = []
    apk_metadata: dict[str, Any] = {}

    try:
        expanded = expand(config, environment)
        server_mode = str(expanded.get("server_mode") or "managed").strip().lower()
        if server_mode not in {"managed", "external"}:
            raise ValueError(f"unsupported Appium server_mode: {server_mode}")
        host = str(expanded.get("server_host") or "127.0.0.1")
        preferred_port = int(expanded.get("server_port") or 4723)
        base_path = str(expanded.get("base_path") or "").strip("/")
        prefix = f"/{base_path}" if base_path else ""
        if server_mode == "managed":
            port = select_server_port(
                host,
                preferred_port,
                expanded.get("auto_select_port", True) is True,
            )
            server_url = f"http://{host}:{port}{prefix}"
        else:
            server_url = str(expanded.get("server_url") or "").strip().rstrip("/")
            if not server_url:
                raise ValueError("external Appium server requires server_url")
            port = preferred_port
        status_url = str(expanded.get("server_status_url") or "").strip()
        if not status_url:
            status_url = f"{server_url}/status"

        adb = find_adb(str(expanded.get("adb_path") or ""))
        if server_mode == "managed" and not appium.is_file():
            raise FileNotFoundError("Appium CLI is missing; run platform.cmd setup-mobile")
        if not allure.is_file():
            raise FileNotFoundError("Allure CLI is missing; run platform.cmd setup-ci")

        base_capabilities = expanded.get("capabilities") or {}
        if not isinstance(base_capabilities, dict) or not base_capabilities:
            raise ValueError("mobile CI capabilities are required")
        requested_udid = str(base_capabilities.get("appium:udid") or "").strip()
        device_pool = expanded.get("device_pool") or {}
        if not isinstance(device_pool, dict):
            raise ValueError("mobile CI device_pool must be an object")
        device_source = str(
            device_pool.get("source")
            or ("inventory" if server_mode == "external" else "adb")
        ).strip().lower()
        if device_source not in {"adb", "inventory", "hybrid"}:
            raise ValueError(f"unsupported mobile device source: {device_source}")

        adb_devices: list[dict[str, Any]] = []
        if device_source in {"adb", "hybrid"}:
            if not adb:
                raise FileNotFoundError("ADB was not found; install Android SDK Platform-Tools")
            sdk_root = sdk_root_from_adb(adb)
            if sdk_root:
                environment["ANDROID_HOME"] = sdk_root
                environment["ANDROID_SDK_ROOT"] = sdk_root
            adb_result = subprocess.run(
                [adb, "devices", "-l"],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                errors="replace",
                check=False,
            )
            if adb_result.returncode != 0:
                raise RuntimeError(f"ADB failed: {adb_result.stderr.strip()}")
            adb_devices = parse_adb_devices(adb_result.stdout)
            for device in adb_devices:
                device["source"] = "adb"

        inventory_value: Any = device_pool.get("inventory") or []
        if environment.get("AUTOTEST_MOBILE_DEVICE_INVENTORY", "").strip():
            inventory_value = environment["AUTOTEST_MOBILE_DEVICE_INVENTORY"]
        inventory_devices = (
            parse_device_inventory(inventory_value)
            if device_source in {"inventory", "hybrid"}
            else []
        )
        discovered_devices = merge_device_sources(adb_devices, inventory_devices)
        if not discovered_devices:
            raise RuntimeError(
                "No Android device was discovered from ADB or the configured Grid inventory"
            )
        if args.device:
            device_pool = {**device_pool, "mode": "listed", "include": args.device}
        selected_devices = select_devices(discovered_devices, device_pool, requested_udid)
        if not selected_devices:
            raise RuntimeError("No Android device matched the configured device pool")

        app_path = str(base_capabilities.get("appium:app") or "").strip()
        prepared_metadata_path = environment.get("AUTOTEST_ANDROID_APK_METADATA", "")
        if app_path:
            apk_file = Path(app_path)
            if apk_file.is_file():
                apk_file = apk_file.resolve()
                apk_metadata = {
                    "apk_path": str(apk_file),
                    "delivery": "local",
                    "size_bytes": apk_file.stat().st_size,
                    "sha256": sha256_path(apk_file),
                }
            elif server_mode == "external":
                apk_metadata = {
                    "app_reference": redact(app_path, environment),
                    "delivery": "external_grid",
                    "verification": "metadata_only_unless_a_prepared_APK_is_attached",
                }
            else:
                raise ValueError(f"APK does not exist: {app_path}")
            if prepared_metadata_path and Path(prepared_metadata_path).is_file():
                prepared_metadata = json.loads(
                    Path(prepared_metadata_path).read_text(encoding="utf-8")
                )
                apk_metadata = {**prepared_metadata, **apk_metadata}
            apk_metadata_path.write_text(
                json.dumps(apk_metadata, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        checks = expanded.get("checks") or {}
        if not isinstance(checks, dict):
            raise ValueError("mobile CI checks must be an object")
        preflight = expanded.get("device_preflight") or {}
        if not isinstance(preflight, dict):
            raise ValueError("mobile CI device_preflight must be an object")
        if preflight.get("enabled", True) is True and not adb:
            raise FileNotFoundError(
                "device preflight requires local ADB; disable it only when Grid nodes own ADB"
            )
        if adb:
            preflight_results = [
                collect_device_preflight(adb, device, preflight)
                for device in selected_devices
            ]
        else:
            preflight_results = [
                {
                    **report_device(device),
                    "status": "SKIPPED",
                    "reason": "external Grid owns the device-side ADB connection",
                    "checks": [],
                }
                for device in selected_devices
            ]
        preflight_path.write_text(
            json.dumps(preflight_results, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        failed_preflight = [
            result["udid"] for result in preflight_results if result["status"] == "FAIL"
        ]
        if preflight.get("enforce", True) is True and failed_preflight:
            raise RuntimeError(
                f"Android device preflight failed: {', '.join(failed_preflight)}"
            )
        configured_workflows = expanded.get("workflows")
        if configured_workflows is None:
            legacy_workflow = expanded.get("workflow") or {}
            if not isinstance(legacy_workflow, dict):
                raise ValueError("mobile CI workflow must be an object")
            configured_workflows = [legacy_workflow] if legacy_workflow else []
        if not isinstance(configured_workflows, list) or any(
            not isinstance(item, dict) for item in configured_workflows
        ):
            raise ValueError("mobile CI workflows must be a list of objects")
        configured_workflows = select_workflows(configured_workflows, args.scenario)
        startup_only_mode = bool(configured_workflows) and all(
            str(workflow.get("phase") or "").lower() == "startup"
            for workflow in configured_workflows
        )
        safety = expanded.get("safety") or {}
        if not isinstance(safety, dict):
            raise ValueError("mobile CI safety must be an object")
        environment_overrides = {
            "allow_mutations": "AUTOTEST_ALLOW_MUTATIONS",
            "allow_high_risk": "AUTOTEST_ALLOW_HIGH_RISK",
            "allow_network_changes": "AUTOTEST_MOBILE_ALLOW_NETWORK_CHANGES",
            "allow_system_events": "AUTOTEST_MOBILE_ALLOW_SYSTEM_EVENTS",
            "allow_monkey": "AUTOTEST_MOBILE_ALLOW_MONKEY",
        }
        for safety_name, environment_name in environment_overrides.items():
            if environment_name in environment:
                safety[safety_name] = bool_value(environment[environment_name])
        performance = expanded.get("performance") or {}
        if not isinstance(performance, dict):
            raise ValueError("mobile CI performance must be an object")
        if bool_value(performance.get("enabled")) and not adb:
            raise FileNotFoundError(
                "Android performance evidence requires ADB access from the runner"
            )
        coverage = build_coverage_scope(expanded, configured_workflows, safety)
        coverage_path.write_text(
            json.dumps(coverage, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        if server_mode == "managed":
            command = [str(appium), "--address", host, "--port", str(port)]
            if base_path:
                command.extend(["--base-path", f"/{base_path}"])
            log_handle = log_path.open("w", encoding="utf-8")
            appium_process = subprocess.Popen(
                command,
                cwd=ROOT,
                env=environment,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
            )
        wait_for_appium(status_url, int(expanded.get("startup_timeout_seconds") or 60))

        for device in selected_devices:
            device_started_ms = int(time.time() * 1000)
            device_root = run_root / "devices" / safe_name(device["udid"])
            device_root.mkdir(parents=True, exist_ok=False)
            session_path = device_root / "session.json"
            source_path = device_root / "page-source.xml"
            screenshot_path = device_root / "launch-screen.png"
            workflow_path = device_root / "workflow-result.json"
            performance_path = device_root / "performance.json"
            performance_interpretation_path = device_root / "performance-interpretation.md"
            runtime_log_path = device_root / "runtime-logcat.txt"
            result_path = device_root / "result.json"
            attachments: list[tuple[str, Path, str]] = [
                ("Mobile coverage scope", coverage_path, "application/json"),
                ("Device preflight", preflight_path, "application/json"),
            ]
            if apk_metadata_path.is_file():
                attachments.append(("APK metadata", apk_metadata_path, "application/json"))
            session_id = ""
            device_status = "FAILED"
            device_message = ""
            current_package = ""
            app_activity = ""
            page_source_chars = 0
            workflow_status = "SKIPPED"
            workflow_message = "mobile workflows were not run"
            workflow_steps: list[dict[str, Any]] = []
            workflow_results: list[dict[str, Any]] = []
            performance_result: dict[str, Any] = {}
            try:
                capabilities = dict(base_capabilities)
                device_capabilities = device.get("capabilities") or {}
                if not isinstance(device_capabilities, dict):
                    raise TypeError(
                        f"device capabilities for {device['udid']} must be an object"
                    )
                capabilities.update(device_capabilities)
                capabilities.setdefault("appium:udid", device["udid"])
                capabilities.setdefault("appium:deviceName", device["model"])
                session_launch_started_ms = int(time.time() * 1000)
                session = http_json(
                    f"{server_url}/session",
                    "POST",
                    {"capabilities": {"alwaysMatch": capabilities, "firstMatch": [{}]}},
                    int(expanded.get("session_timeout_seconds") or 300),
                )
                session_value = session.get("value", {})
                session_id = str(session_value.get("sessionId") or session.get("sessionId") or "")
                if not session_id:
                    raise RuntimeError(f"Appium session was not created: {session}")
                session_capabilities = session_value.get("capabilities") or {}
                session_path.write_text(
                    redact(json.dumps(session_capabilities, ensure_ascii=False, indent=2), environment),
                    encoding="utf-8",
                )
                attachments.append(("Appium session capabilities", session_path, "application/json"))

                expected_package = str(
                    checks.get("expected_package")
                    or session_capabilities.get("appPackage")
                    or capabilities.get("appium:appPackage")
                    or ""
                ).strip()
                if expected_package:
                    http_json(
                        f"{server_url}/session/{session_id}/appium/device/activate_app",
                        "POST",
                        {"appId": expected_package},
                    )
                current_package = wait_for_package(
                    server_url,
                    session_id,
                    expected_package,
                    int(checks.get("launch_timeout_seconds") or 15),
                )
                initial_foreground_ms = int(time.time() * 1000)
                activity_result = http_json(
                    f"{server_url}/session/{session_id}/appium/device/current_activity"
                )
                app_activity = str(activity_result.get("value") or "")

                source_result = http_json(f"{server_url}/session/{session_id}/source")
                page_source = str(source_result.get("value") or "")
                page_source_chars = len(page_source)
                source_path.write_text(page_source, encoding="utf-8")
                attachments.append(("Launch page source", source_path, "application/xml"))

                screenshot_result = http_json(f"{server_url}/session/{session_id}/screenshot")
                screenshot_value = str(screenshot_result.get("value") or "")
                if screenshot_value:
                    screenshot_path.write_bytes(base64.b64decode(screenshot_value))
                    attachments.append(("Launch screenshot", screenshot_path, "image/png"))

                if expected_package and current_package != expected_package:
                    raise AssertionError(
                        f"foreground package is {current_package!r}, expected {expected_package!r}"
                    )
                minimum_source_chars = int(checks.get("min_page_source_chars") or 100)
                if page_source_chars < minimum_source_chars:
                    raise AssertionError(
                        f"page source has {page_source_chars} characters, expected at least {minimum_source_chars}"
                    )
                if checks.get("capture_screenshot", True) and not screenshot_path.is_file():
                    raise AssertionError("launch screenshot was not captured")

                performance_enabled = bool_value(performance.get("enabled")) and not startup_only_mode
                startup_metrics: dict[str, Any] = {
                    "appium_session_to_foreground_ms": (
                        initial_foreground_ms - session_launch_started_ms
                    )
                }
                performance_before: dict[str, Any] = {}
                if performance_enabled:
                    startup_config = performance.get("startup") or {}
                    if not isinstance(startup_config, dict):
                        raise ValueError("mobile performance.startup must be an object")
                    if performance.get("capture_runtime_logcat", True) is not False:
                        run_adb(adb, device["udid"], ["logcat", "-c"], check=False)
                    component = str(startup_config.get("component") or "").strip()
                    if not component:
                        component = resolve_launcher_component(adb, device["udid"], expected_package)
                    settle_seconds = float(startup_config.get("settle_seconds") or 1)
                    if startup_config.get("measure_cold", True) is not False:
                        startup_metrics["cold"] = measure_app_start(
                            adb,
                            device["udid"],
                            expected_package,
                            component,
                            cold=True,
                            settle_seconds=settle_seconds,
                        )
                    if startup_config.get("measure_warm", True) is not False:
                        startup_metrics["warm"] = measure_app_start(
                            adb,
                            device["udid"],
                            expected_package,
                            component,
                            cold=False,
                            settle_seconds=settle_seconds,
                        )
                    wait_for_package(
                        server_url,
                        session_id,
                        expected_package,
                        int(checks.get("launch_timeout_seconds") or 15),
                    )
                    reset_graphics(adb, device["udid"], expected_package)
                    performance_before = collect_device_metrics(
                        adb, device["udid"], expected_package
                    )

                runtime = {
                    "adb_path": adb or "",
                    "udid": device["udid"],
                    "device_kind": device["kind"],
                    "app_package": expected_package,
                    "app_activity": app_activity,
                }
                for workflow in configured_workflows:
                    (
                        current_workflow_status,
                        current_workflow_message,
                        current_workflow_steps,
                        workflow_attachments,
                    ) = run_workflow(
                        server_url,
                        session_id,
                        workflow,
                        device_root,
                        runtime,
                        safety,
                    )
                    workflow_id = str(workflow.get("id") or "mobile-workflow")
                    for step in current_workflow_steps:
                        step["workflow_id"] = workflow_id
                    workflow_steps.extend(current_workflow_steps)
                    attachments.extend(workflow_attachments)
                    workflow_results.append(
                        {
                            "id": workflow_id,
                            "category": str(workflow.get("category") or "business"),
                            "status": current_workflow_status,
                            "message": current_workflow_message,
                            "steps": current_workflow_steps,
                        }
                    )
                    if current_workflow_status in {"FAILED", "BLOCKED"}:
                        break

                workflow_statuses = [item["status"] for item in workflow_results]
                if "FAILED" in workflow_statuses:
                    workflow_status = "FAILED"
                elif "BLOCKED" in workflow_statuses:
                    workflow_status = "BLOCKED"
                elif "PASSED" in workflow_statuses:
                    workflow_status = "PASSED"
                else:
                    workflow_status = "SKIPPED"
                workflow_message = "; ".join(
                    item["message"] for item in workflow_results if item["message"]
                ) or "no mobile workflow was enabled"
                workflow_path.write_text(
                    json.dumps(
                        {
                            "status": workflow_status,
                            "message": workflow_message,
                            "workflows": workflow_results,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                attachments.append(("Workflow result", workflow_path, "application/json"))
                workflow_failed = workflow_status == "FAILED"

                if performance_enabled:
                    frame_budget_ms = float(performance.get("frame_budget_ms") or 16.67)
                    performance_after = collect_device_metrics(
                        adb,
                        device["udid"],
                        expected_package,
                        include_graphics=True,
                        frame_budget_ms=frame_budget_ms,
                    )
                    rendering_samples = [
                        step.get("details", {}).get("performance")
                        for step in workflow_steps
                        if step.get("details", {}).get("performance")
                    ]
                    if rendering_samples:
                        performance_after["graphics"] = dict(
                            rendering_samples[-1].get("graphics") or {}
                        )
                        performance_after["graphics"]["source"] = "workflow_swipe_step"
                    lifecycle_samples: list[dict[str, Any]] = []
                    lifecycle_cycles = max(0, int(performance.get("memory_lifecycle_cycles") or 0))
                    for cycle in range(1, lifecycle_cycles + 1):
                        http_json(
                            f"{server_url}/session/{session_id}/appium/device/terminate_app",
                            "POST",
                            {"appId": expected_package},
                        )
                        http_json(
                            f"{server_url}/session/{session_id}/appium/device/activate_app",
                            "POST",
                            {"appId": expected_package},
                        )
                        time.sleep(float(performance.get("lifecycle_settle_seconds") or 2))
                        sample = collect_device_metrics(adb, device["udid"], expected_package)
                        sample["cycle"] = cycle
                        lifecycle_samples.append(sample)
                    thresholds = performance.get("thresholds") or {}
                    if not isinstance(thresholds, dict):
                        raise ValueError("mobile performance.thresholds must be an object")
                    diagnosis = evaluate_performance(
                        startup_metrics,
                        performance_before,
                        performance_after,
                        thresholds,
                    )
                    runtime_health: dict[str, Any] = {
                        "status": "SKIPPED",
                        "signal_count": 0,
                        "signals": [],
                    }
                    if performance.get("capture_runtime_logcat", True) is not False:
                        raw_logcat = run_adb(
                            adb,
                            device["udid"],
                            ["logcat", "-d", "-v", "threadtime", "-t", "2000"],
                            timeout_seconds=60,
                        )
                        relevant_logcat = "\n".join(
                            line
                            for line in raw_logcat.splitlines()
                            if expected_package in line
                            or "OutOfMemoryError" in line
                            or "FATAL EXCEPTION" in line
                            or "ANR in" in line
                        )
                        runtime_log_path.write_text(
                            redact(relevant_logcat, environment), encoding="utf-8"
                        )
                        attachments.append(
                            ("Android runtime log", runtime_log_path, "text/plain")
                        )
                        runtime_health = parse_runtime_health(raw_logcat, expected_package)
                        diagnosis["runtime_health"] = runtime_health
                        diagnosis["checks"].append(
                            {
                                "name": "runtime_crash_or_oom_signals",
                                "actual": runtime_health["signal_count"],
                                "limit": 0,
                                "status": runtime_health["status"],
                            }
                        )
                        if runtime_health["status"] == "FAIL":
                            diagnosis["status"] = "FAIL"
                    if len(lifecycle_samples) >= 2:
                        first_pss = lifecycle_samples[0].get("total_pss_kb")
                        last_pss = lifecycle_samples[-1].get("total_pss_kb")
                        if first_pss is not None and last_pss is not None:
                            cycle_growth = last_pss - first_pss
                            diagnosis["lifecycle_memory_growth_kb"] = cycle_growth
                            diagnosis["memory_leak_assessment"] = (
                                "SUSPECTED_TREND"
                                if len(lifecycle_samples) >= 3 and cycle_growth > 0
                                else "NOT_OBSERVED"
                                if len(lifecycle_samples) >= 3
                                else "INSUFFICIENT_EVIDENCE"
                            )
                            growth_limit = thresholds.get("max_memory_growth_kb")
                            if growth_limit is not None:
                                cycle_check = {
                                    "name": "lifecycle_memory_growth_kb",
                                    "actual": cycle_growth,
                                    "limit": growth_limit,
                                    "status": "PASS" if cycle_growth <= growth_limit else "FAIL",
                                }
                                diagnosis["checks"].append(cycle_check)
                                if cycle_check["status"] == "FAIL":
                                    diagnosis["status"] = "FAIL"
                    else:
                        diagnosis["memory_leak_assessment"] = "INSUFFICIENT_EVIDENCE"
                    performance_result = {
                        "startup": startup_metrics,
                        "before_workflows": performance_before,
                        "after_workflows": performance_after,
                        "lifecycle_samples": lifecycle_samples,
                        "runtime_health": runtime_health,
                        "diagnosis": diagnosis,
                    }
                    performance_path.write_text(
                        json.dumps(performance_result, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    interpretation = build_performance_interpretation(performance_result)
                    performance_interpretation_path.write_text(
                        render_performance_interpretation(interpretation),
                        encoding="utf-8",
                    )
                    attachments.append(
                        ("Android performance metrics", performance_path, "application/json")
                    )
                    attachments.append(
                        (
                            "Android performance interpretation",
                            performance_interpretation_path,
                            "text/markdown",
                        )
                    )
                    if bool_value(performance.get("enforce_thresholds")) and diagnosis["status"] == "FAIL":
                        raise AssertionError("Android performance thresholds were not met")
                if workflow_failed:
                    raise AssertionError(workflow_message)

                current_package = wait_for_package(
                    server_url,
                    session_id,
                    expected_package,
                    int(checks.get("launch_timeout_seconds") or 15),
                )
                activity_result = http_json(
                    f"{server_url}/session/{session_id}/appium/device/current_activity"
                )
                app_activity = str(activity_result.get("value") or "")
                device_status = "BLOCKED" if workflow_status == "BLOCKED" else "PASSED"
                device_message = (
                    f"App launched on {device['model']}; package={current_package}; "
                    f"activity={app_activity}; {workflow_message}"
                )
            except Exception as exc:
                device_message = f"{type(exc).__name__}: {exc}"
            finally:
                if session_id:
                    try:
                        http_json(f"{server_url}/session/{session_id}", "DELETE")
                    except Exception as exc:
                        if device_status == "PASSED":
                            device_status = "FAILED"
                            device_message = f"session cleanup failed: {type(exc).__name__}: {exc}"

            device_stopped_ms = int(time.time() * 1000)
            device_result = {
                **report_device(device),
                "status": device_status,
                "message": device_message,
                "current_package": current_package,
                "app_activity": app_activity,
                "page_source_chars": page_source_chars,
                "workflow_status": workflow_status,
                "workflow_steps": workflow_steps,
                "workflow_results": workflow_results,
                "performance": performance_result,
                "artifacts": {
                    "session": str(session_path),
                    "page_source": str(source_path),
                    "screenshot": str(screenshot_path),
                    "workflow": str(workflow_path),
                    "performance": str(performance_path),
                    "performance_interpretation": str(performance_interpretation_path),
                    "runtime_logcat": str(runtime_log_path),
                },
            }
            result_path.write_text(
                json.dumps(device_result, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            attachments.append(("Device result", result_path, "application/json"))
            write_allure_result(
                results_dir,
                device_status.lower(),
                device_message,
                device_started_ms,
                device_stopped_ms,
                device,
                attachments,
                workflow_steps,
            )
            device_results.append(device_result)

        passed_count = sum(result["status"] == "PASSED" for result in device_results)
        status = "PASSED" if passed_count == len(device_results) else "FAILED"
        message = f"Android mobile workflow passed on {passed_count}/{len(device_results)} devices"
    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"
        write_allure_result(results_dir, "failed", message, started_ms, int(time.time() * 1000))
    finally:
        if appium_process is not None:
            appium_process.terminate()
            try:
                appium_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                appium_process.kill()
        if log_handle is not None:
            log_handle.close()
        if log_path.is_file():
            log_path.write_text(redact(log_path.read_text(encoding="utf-8"), environment), encoding="utf-8")

    coverage = build_coverage_scope(
        locals().get("expanded", config),
        locals().get("configured_workflows", config.get("workflows") or []),
        locals().get("safety", config.get("safety") or {}),
        device_results,
    )
    coverage_path.write_text(json.dumps(coverage, ensure_ascii=False, indent=2), encoding="utf-8")
    if device_results:
        write_allure_result(
            results_dir,
            "passed" if status == "PASSED" else "failed",
            "实际验证范围与平台通用能力已分开记录。",
            started_ms,
            int(time.time() * 1000),
            {
                "udid": "run-scope",
                "model": str((coverage.get("current_project") or {}).get("name") or "Mobile scope"),
                "kind": "scope",
            },
            [("Coverage scope", coverage_path, "application/json")],
        )

    allure_process = subprocess.run(
        [str(allure), "generate", str(results_dir), "--clean", "-o", str(report_dir)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    ) if allure.is_file() else None
    if allure_process is not None and allure_process.returncode != 0:
        status = "FAILED"
        message = f"{message}; Allure generation failed: {allure_process.stderr.strip()}"

    summary = {
        "schema_version": "1.0",
        "report_type": "ANDROID_APPIUM_CI",
        "run_id": run_id,
        "status": status,
        "message": message,
        "server": {
            "mode": locals().get("server_mode", "managed"),
            "url": redact(str(locals().get("server_url", "")), environment),
            "status_url": redact(str(locals().get("status_url", "")), environment),
            "device_source": locals().get("device_source", "adb"),
        },
        "devices": [device["udid"] for device in selected_devices],
        "discovered_devices": [report_device(device) for device in discovered_devices],
        "device_results": device_results,
        "device_preflight": preflight_results,
        "apk": apk_metadata,
        "coverage": coverage,
        "started_at": started_at,
        "finished_at": utc_now(),
        "artifacts": {
            "appium_log": str(log_path) if log_path.is_file() else "",
            "allure_report": str(report_dir / "index.html"),
            "coverage_scope": str(coverage_path),
            "device_preflight": str(preflight_path),
            "apk_metadata": str(apk_metadata_path) if apk_metadata_path.is_file() else "",
        },
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Android Appium CI: {status}\nSummary: {summary_path}")
    return 0 if status == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
