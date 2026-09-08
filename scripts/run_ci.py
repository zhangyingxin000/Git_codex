from __future__ import annotations

import argparse
import importlib
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_ROOT = ROOT / "reports" / "ci"
REQUIRED_MODULES = (
    "fastapi",
    "uvicorn",
    "pydantic",
    "yaml",
    "sqlalchemy",
    "httpx",
    "redis",
    "pymysql",
    "pytest",
)
COMPILE_TARGETS = (
    ROOT / "app.py",
    ROOT / "quality_hub_backend" / "api" / "fastapi_app.py",
    ROOT / "quality_hub_backend" / "adapters" / "jmeter_mcp.py",
    ROOT / "quality_hub_backend" / "demo" / "salary_trade.py",
)
RUFF_TARGETS = ("quality_hub_backend", "scripts", "tests")


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def passed_count(output: str) -> int:
    matches = re.findall(r"(\d+) passed", output)
    return int(matches[-1]) if matches else 0


def cleanup_pytest_temp(path: Path, run_root: Path) -> None:
    resolved = path.resolve()
    resolved.relative_to(run_root.resolve())
    if resolved.name in {"pytest-work", "demo-pytest-work"}:
        shutil.rmtree(resolved, ignore_errors=True)


def local_executable(name: str) -> str | None:
    candidates = (
        ROOT / ".venv" / "Scripts" / f"{name}.exe",
        ROOT / "node_modules" / ".bin" / f"{name}.cmd",
    )
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return shutil.which(name)


def failed_tool_step(name: str, message: str, log_path: Path) -> dict[str, Any]:
    log_path.write_text(message + "\n", encoding="utf-8")
    print(message)
    return {
        "name": name,
        "status": "FAILED",
        "exit_code": 1,
        "duration_seconds": 0,
        "message": message,
        "log": relative(log_path),
    }


def secret_fingerprints(payload: dict[str, Any]) -> set[tuple[str, str, str]]:
    fingerprints = set()
    for filename, findings in (payload.get("results") or {}).items():
        for finding in findings or []:
            fingerprints.add(
                (
                    str(filename).replace("\\", "/"),
                    str(finding.get("type") or ""),
                    str(finding.get("hashed_secret") or ""),
                )
            )
    return fingerprints


def run_secret_scan(report_path: Path, log_path: Path) -> dict[str, Any]:
    started = time.monotonic()
    detector = local_executable("detect-secrets")
    baseline_path = ROOT / ".secrets.baseline"
    if not detector:
        return failed_tool_step("secret_scan", "detect-secrets is missing; run platform.cmd setup-ci", log_path)
    if not baseline_path.is_file():
        return failed_tool_step("secret_scan", ".secrets.baseline is missing", log_path)

    process = subprocess.run(
        [
            detector,
            "scan",
            "-n",
            "--exclude-files",
            r"(^|[\\/])\.secrets\.baseline$",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    report_path.write_text(process.stdout, encoding="utf-8")
    errors: list[str] = []
    new_findings: list[dict[str, str]] = []
    if process.returncode != 0:
        errors.append(process.stderr.strip() or "detect-secrets scan failed")
    else:
        try:
            baseline = json.loads(baseline_path.read_text(encoding="utf-8-sig"))
            current = json.loads(process.stdout)
            known = secret_fingerprints(baseline)
            for filename, secret_type, hashed_secret in sorted(secret_fingerprints(current) - known):
                new_findings.append(
                    {"filename": filename, "type": secret_type, "hashed_secret": hashed_secret}
                )
        except Exception as exc:
            errors.append(f"Unable to parse secret scan output: {type(exc).__name__}: {exc}")
    if new_findings:
        errors.append(f"Found {len(new_findings)} new potential secret(s)")
    lines = errors or ["No new secrets were found."]
    if new_findings:
        lines.extend(f"{item['filename']}: {item['type']}" for item in new_findings)
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return {
        "name": "secret_scan",
        "status": "FAILED" if errors else "PASSED",
        "exit_code": 1 if errors else 0,
        "duration_seconds": round(time.monotonic() - started, 2),
        "new_findings": new_findings,
        "report": relative(report_path),
        "log": relative(log_path),
    }


def run_process(
    name: str,
    command: list[str],
    log_path: Path,
    *,
    environment: dict[str, str] | None = None,
) -> tuple[dict[str, Any], str]:
    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    output = "".join(part for part in (result.stdout, result.stderr) if part)
    log_path.write_text(output, encoding="utf-8")
    if output:
        print(output, end="" if output.endswith("\n") else "\n")
    return (
        {
            "name": name,
            "status": "PASSED" if result.returncode == 0 else "FAILED",
            "exit_code": result.returncode,
            "duration_seconds": round(time.monotonic() - started, 2),
            "passed_tests": passed_count(output),
            "log": relative(log_path),
        },
        output,
    )


def runtime_check(log_path: Path) -> dict[str, Any]:
    started = time.monotonic()
    errors: list[str] = []
    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
        except Exception as exc:  # pragma: no cover - exercised by incomplete CI images
            errors.append(f"import {module}: {type(exc).__name__}: {exc}")
    for path in COMPILE_TARGETS:
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:  # pragma: no cover - exercised by invalid source files
            errors.append(f"compile {relative(path)}: {type(exc).__name__}: {exc}")
    output = "Runtime and import checks passed.\n" if not errors else "\n".join(errors) + "\n"
    log_path.write_text(output, encoding="utf-8")
    print(output, end="")
    return {
        "name": "runtime_check",
        "status": "PASSED" if not errors else "FAILED",
        "exit_code": 0 if not errors else 1,
        "duration_seconds": round(time.monotonic() - started, 2),
        "errors": errors,
        "log": relative(log_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the portable AutoTest AI CI quality gate.")
    parser.add_argument("--skip-demo", action="store_true", help="Skip the safe local demo acceptance stage.")
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    args = parser.parse_args()

    run_id = f"ci-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    report_root = args.report_root if args.report_root.is_absolute() else ROOT / args.report_root
    run_root = report_root / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    summary_path = run_root / "summary.json"
    started_at = utc_now()
    steps: list[dict[str, Any]] = []

    runtime = runtime_check(run_root / "runtime-check.log")
    steps.append(runtime)

    if runtime["status"] == "PASSED":
        ruff = local_executable("ruff")
        if ruff:
            ruff_step, _ = run_process(
                "ruff_critical_lint",
                [
                    ruff,
                    "check",
                    *RUFF_TARGETS,
                    "--select",
                    "E9,F63,F7,F82",
                    "--output-format",
                    "concise",
                ],
                run_root / "ruff.log",
            )
        else:
            ruff_step = failed_tool_step(
                "ruff_critical_lint",
                "Ruff is missing; run platform.cmd setup-ci",
                run_root / "ruff.log",
            )
        steps.append(ruff_step)
        steps.append(run_secret_scan(run_root / "secret-scan.json", run_root / "secret-scan.log"))

        test_temp = run_root / "pytest-work"
        try:
            pytest_step, _ = run_process(
                "platform_tests",
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "--basetemp",
                    str(test_temp),
                    "--junitxml",
                    str(run_root / "pytest-junit.xml"),
                ],
                run_root / "pytest.log",
            )
        finally:
            cleanup_pytest_temp(test_temp, run_root)
        steps.append(pytest_step)

        if pytest_step["status"] == "PASSED" and not args.skip_demo:
            demo_environment = os.environ.copy()
            demo_environment.update(
                {
                    "AUTOTEST_DEMO_MODE": "true",
                    "AUTOTEST_ALLOW_MUTATIONS": "false",
                    "AUTOTEST_ALLOW_HIGH_RISK": "false",
                    "AUTOTEST_ALLOWED_HOSTS": "127.0.0.1,localhost",
                    "PYTHONUTF8": "1",
                }
            )
            demo_generation, _ = run_process(
                "demo_generation",
                [sys.executable, "-m", "quality_hub_backend.demo.salary_trade"],
                run_root / "demo-generation.log",
                environment=demo_environment,
            )
            steps.append(demo_generation)

            if demo_generation["status"] == "PASSED":
                demo_temp = run_root / "demo-pytest-work"
                try:
                    demo_tests, _ = run_process(
                        "demo_tests",
                        [
                            sys.executable,
                            "-m",
                            "pytest",
                            "-q",
                            "--basetemp",
                            str(demo_temp),
                            "--junitxml",
                            str(run_root / "demo-junit.xml"),
                            "tests/test_demo_salary_trade.py",
                            "tests/test_jmeter_mcp_adapter.py",
                            "tests/test_dependency_consistency.py",
                        ],
                        run_root / "demo-tests.log",
                        environment=demo_environment,
                    )
                finally:
                    cleanup_pytest_temp(demo_temp, run_root)
                steps.append(demo_tests)

        junit_files = [
            path
            for path in (run_root / "pytest-junit.xml", run_root / "demo-junit.xml")
            if path.is_file()
        ]
        if junit_files:
            command = [sys.executable, "scripts/generate_allure_report.py"]
            for junit_file in junit_files:
                command.extend(["--junit", str(junit_file)])
            command.extend(
                [
                    "--results-dir",
                    str(run_root / "allure-results"),
                    "--report-dir",
                    str(run_root / "allure-report"),
                    "--summary",
                    str(run_root / "allure-summary.json"),
                ]
            )
            allure_step, _ = run_process(
                "allure_report",
                command,
                run_root / "allure.log",
            )
            steps.append(allure_step)

    status = "PASSED" if steps and all(step["status"] == "PASSED" for step in steps) else "FAILED"
    summary = {
        "schema_version": "1.0",
        "report_type": "PLATFORM_CI_QUALITY_GATE",
        "run_id": run_id,
        "status": status,
        "started_at": started_at,
        "finished_at": utc_now(),
        "git_commit": git_commit(),
        "python": sys.version.split()[0],
        "steps": steps,
        "artifacts": sorted(
            relative(path)
            for path in [*run_root.iterdir(), run_root / "allure-report" / "index.html"]
            if path.is_file()
        ),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"CI quality gate: {status}")
    print(f"Summary: {relative(summary_path)}")
    return 0 if status == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
