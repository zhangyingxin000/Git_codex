from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_ROOT = ROOT / "reports" / "ci-tools"
SUPPORTED_TOOLS = {"newman", "jmeter", "apifox", "command"}
ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
SENSITIVE_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "TICKET", "KEY")


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-.")
    return cleaned or "stage"


def find_executable(name: str) -> str | None:
    local_scripts = ROOT / ".venv" / "Scripts"
    candidates = [
        local_scripts / f"{name}.exe",
        local_scripts / f"{name}.cmd",
        local_scripts / f"{name}.bat",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return shutil.which(name)


def expand_environment(value: str, environment: dict[str, str]) -> str:
    missing: list[str] = []

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in environment or environment[name] == "":
            missing.append(name)
            return match.group(0)
        return environment[name]

    expanded = ENV_PATTERN.sub(replace, value)
    if missing:
        raise ValueError(f"missing environment variables: {', '.join(sorted(set(missing)))}")
    return expanded.replace("{root}", str(ROOT))


def redaction_values(environment: dict[str, str]) -> list[str]:
    values = []
    for name, value in environment.items():
        if value and len(value) >= 4 and any(marker in name.upper() for marker in SENSITIVE_MARKERS):
            values.append(value)
    return sorted(set(values), key=len, reverse=True)


def redact(value: str, secrets: list[str]) -> str:
    for secret in secrets:
        value = value.replace(secret, "***")
    return value


def primary_artifacts(stage_dir: Path, stage: dict[str, Any]) -> list[str]:
    candidates = [
        stage_dir / "execution.log",
        stage_dir / "newman-report.json",
        stage_dir / "newman-junit.xml",
        stage_dir / "result.jtl",
        stage_dir / "jmeter-html" / "index.html",
    ]
    configured = stage.get("artifacts") or []
    if not isinstance(configured, list):
        raise ValueError("stage artifacts must be a YAML list")
    candidates.extend(resolve_path(str(value)) for value in configured)
    return sorted({relative(path) for path in candidates if path.is_file()})


def load_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"CLI pipeline config does not exist: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("CLI pipeline config must be a YAML object")
    if str(payload.get("schema_version") or "") != "1.0":
        raise ValueError("CLI pipeline schema_version must be 1.0")
    stages = payload.get("stages")
    if not isinstance(stages, list) or not stages:
        raise ValueError("CLI pipeline config must contain at least one stage")
    return payload


def command_for_stage(stage: dict[str, Any], stage_dir: Path, environment: dict[str, str]) -> list[str]:
    tool = str(stage.get("tool") or "").strip().lower()
    if tool not in SUPPORTED_TOOLS:
        raise ValueError(f"unsupported CLI tool: {tool or '<empty>'}")

    if tool == "newman":
        executable = find_executable(str(stage.get("executable") or "newman"))
        if not executable:
            raise FileNotFoundError("Newman CLI was not found")
        collection = resolve_path(expand_environment(str(stage.get("collection") or ""), environment))
        if not collection.is_file():
            raise ValueError(f"Newman collection does not exist: {collection}")
        command = [
            executable,
            "run",
            str(collection),
            "-r",
            "cli,json,junit",
            "--reporter-json-export",
            str(stage_dir / "newman-report.json"),
            "--reporter-junit-export",
            str(stage_dir / "newman-junit.xml"),
        ]
        environment_file = str(stage.get("environment") or "").strip()
        if environment_file:
            resolved_environment = resolve_path(expand_environment(environment_file, environment))
            if not resolved_environment.is_file():
                raise ValueError(f"Newman environment does not exist: {resolved_environment}")
            command.extend(["-e", str(resolved_environment)])
    elif tool == "jmeter":
        executable = find_executable(str(stage.get("executable") or "jmeter"))
        if not executable:
            raise FileNotFoundError("JMeter CLI was not found")
        jmx = resolve_path(expand_environment(str(stage.get("jmx") or ""), environment))
        if not jmx.is_file():
            raise ValueError(f"JMeter JMX does not exist: {jmx}")
        command = [
            executable,
            "-n",
            "-t",
            str(jmx),
            "-l",
            str(stage_dir / "result.jtl"),
            "-e",
            "-o",
            str(stage_dir / "jmeter-html"),
        ]
    else:
        executable_name = str(stage.get("executable") or ("apifox" if tool == "apifox" else "")).strip()
        if not executable_name:
            raise ValueError(f"{tool} stage requires executable")
        executable = find_executable(executable_name)
        if not executable:
            raise FileNotFoundError(f"CLI executable was not found: {executable_name}")
        command = [executable]

    extra_args = stage.get("args") or []
    if not isinstance(extra_args, list):
        raise ValueError("stage args must be a YAML list")
    command.extend(expand_environment(str(value), environment) for value in extra_args)
    return command


def run_stage(stage: dict[str, Any], output_root: Path, environment: dict[str, str]) -> dict[str, Any]:
    name = str(stage.get("name") or stage.get("tool") or "stage")
    required = bool(stage.get("required", True))
    result: dict[str, Any] = {
        "name": name,
        "tool": str(stage.get("tool") or "").lower(),
        "required": required,
    }
    if stage.get("enabled", False) is not True:
        result.update({"status": "SKIPPED", "reason": "stage is disabled"})
        return result

    stage_dir = output_root / safe_name(name)
    stage_dir.mkdir(parents=True, exist_ok=False)
    log_path = stage_dir / "execution.log"
    started = time.monotonic()
    secrets = redaction_values(environment)
    try:
        command = command_for_stage(stage, stage_dir, environment)
        timeout_seconds = max(1, int(stage.get("timeout_seconds") or 600))
        process = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
        output = "".join(part for part in (process.stdout, process.stderr) if part)
        output = redact(output, secrets)
        log_path.write_text(output, encoding="utf-8")
        result.update(
            {
                "status": "PASSED" if process.returncode == 0 else "FAILED",
                "exit_code": process.returncode,
                "duration_seconds": round(time.monotonic() - started, 2),
                "log": relative(log_path),
                "artifacts": primary_artifacts(stage_dir, stage),
            }
        )
    except subprocess.TimeoutExpired as exc:
        output = redact(f"CLI stage timed out after {exc.timeout} seconds.\n", secrets)
        log_path.write_text(output, encoding="utf-8")
        result.update(
            {
                "status": "FAILED" if required else "SKIPPED",
                "reason": output.strip(),
                "duration_seconds": round(time.monotonic() - started, 2),
                "log": relative(log_path),
            }
        )
    except Exception as exc:
        output = redact(f"{type(exc).__name__}: {exc}\n", secrets)
        log_path.write_text(output, encoding="utf-8")
        result.update(
            {
                "status": "FAILED" if required else "SKIPPED",
                "reason": output.strip(),
                "duration_seconds": round(time.monotonic() - started, 2),
                "log": relative(log_path),
            }
        )
    return result


def run_allure_stage(output_root: Path) -> dict[str, Any]:
    junit_files = sorted(output_root.rglob("*-junit.xml"))
    if not junit_files:
        return {
            "name": "allure_report",
            "tool": "allure",
            "required": False,
            "status": "SKIPPED",
            "reason": "no JUnit files were produced",
        }
    command = [sys.executable, "scripts/generate_allure_report.py"]
    for junit_file in junit_files:
        command.extend(["--junit", str(junit_file)])
    command.extend(
        [
            "--results-dir",
            str(output_root / "allure-results"),
            "--report-dir",
            str(output_root / "allure-report"),
            "--summary",
            str(output_root / "allure-summary.json"),
        ]
    )
    started = time.monotonic()
    process = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    log_path = output_root / "allure.log"
    log_path.write_text(
        "".join(part for part in (process.stdout, process.stderr) if part), encoding="utf-8"
    )
    return {
        "name": "allure_report",
        "tool": "allure",
        "required": True,
        "status": "PASSED" if process.returncode == 0 else "FAILED",
        "exit_code": process.returncode,
        "duration_seconds": round(time.monotonic() - started, 2),
        "log": relative(log_path),
        "artifacts": [
            relative(path)
            for path in (output_root / "allure-summary.json", output_root / "allure-report" / "index.html")
            if path.is_file()
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run configured external test CLIs for CI.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    args = parser.parse_args()

    config_path = resolve_path(args.config)
    report_root = resolve_path(args.report_root)
    run_id = f"cli-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    run_root = report_root / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    started_at = utc_now()

    try:
        config = load_config(config_path)
        environment = os.environ.copy()
        steps = [run_stage(stage, run_root, environment) for stage in config["stages"]]
        steps.append(run_allure_stage(run_root))
        required_failures = [step for step in steps if step.get("required") and step["status"] == "FAILED"]
        optional_failures = [step for step in steps if not step.get("required") and step["status"] == "FAILED"]
        executed = [step for step in steps if step["status"] != "SKIPPED"]
        status = (
            "FAILED"
            if required_failures
            else "WARN"
            if optional_failures
            else "PASSED"
            if executed
            else "SKIPPED"
        )
        error = ""
    except Exception as exc:
        steps = []
        status = "FAILED"
        error = f"{type(exc).__name__}: {exc}"

    summary = {
        "schema_version": "1.0",
        "report_type": "EXTERNAL_CLI_PIPELINE",
        "run_id": run_id,
        "status": status,
        "config": relative(config_path),
        "started_at": started_at,
        "finished_at": utc_now(),
        "steps": steps,
        "error": error,
    }
    summary_path = run_root / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"External CLI pipeline: {status}")
    print(f"Summary: {relative(summary_path)}")
    if error:
        print(error, file=sys.stderr)
    return 1 if status == "FAILED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
