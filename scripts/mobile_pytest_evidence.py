from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from scripts.generate_allure_report import convert_junit, generate_report
except ModuleNotFoundError:
    from generate_allure_report import convert_junit, generate_report  # type: ignore[no-redef]


SUMMARY_PATTERN = re.compile(r"Summary:\s*(.+summary\.json)")


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _inside(path: Path, parent: Path) -> Path:
    resolved = path.resolve()
    resolved.relative_to(parent.resolve())
    return resolved


def summary_from_console(console: str, report_root: Path) -> Path:
    matches = SUMMARY_PATTERN.findall(console)
    if not matches:
        raise ValueError("pytest output did not contain a mobile summary path")
    return _inside(Path(matches[-1].strip()), report_root)


def finalize_mobile_pytest_run(
    report_root: Path,
    console_path: Path,
    junit_path: Path,
    exit_code: int,
) -> dict[str, Any]:
    report_root = report_root.resolve()
    console_path = console_path.resolve()
    junit_path = junit_path.resolve()
    console = console_path.read_text(encoding="utf-8", errors="replace")
    summary_path = summary_from_console(console, report_root)
    run_root = summary_path.parent

    archived_console = run_root / "pytest-console.log"
    archived_junit = run_root / "pytest-junit.xml"
    if console_path != archived_console:
        shutil.copy2(console_path, archived_console)
    if junit_path.is_file() and junit_path != archived_junit:
        shutil.copy2(junit_path, archived_junit)

    allure_status = "SKIPPED"
    allure_detail = "pytest JUnit evidence was not available"
    if archived_junit.is_file():
        converted = convert_junit([archived_junit], run_root / "allure-results")
        allure_process = generate_report(run_root / "allure-results", run_root / "allure-report")
        allure_status = "PASSED" if allure_process.returncode == 0 else "FAILED"
        allure_detail = (
            f"merged {converted['converted']} pytest case(s) into Allure"
            if allure_process.returncode == 0
            else allure_process.stderr.strip() or "Allure regeneration failed"
        )

    evidence_path = run_root / "pytest-evidence.json"
    evidence = {
        "schema_version": "1.0",
        "framework": "pytest",
        "role": "top_level_mobile_runner",
        "status": "PASSED" if exit_code == 0 else "FAILED",
        "exit_code": exit_code,
        "recorded_at": utc_now(),
        "console_log": str(archived_console),
        "junit_xml": str(archived_junit) if archived_junit.is_file() else "",
        "mobile_summary": str(summary_path),
        "allure_merge": {"status": allure_status, "detail": allure_detail},
        "execution_chain": ["pytest", "Appium", "Android device/emulator", "Allure"],
    }
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    artifacts = summary.setdefault("artifacts", {})
    artifacts.update(
        {
            "pytest_console": str(archived_console),
            "pytest_junit": str(archived_junit) if archived_junit.is_file() else "",
            "pytest_evidence": str(evidence_path),
        }
    )
    summary["pytest"] = evidence
    summary["execution_chain"] = evidence["execution_chain"]
    if allure_status == "FAILED":
        summary["status"] = "FAILED"
        summary["message"] = f"{summary.get('message') or ''}; {allure_detail}".strip("; ")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "summary_path": str(summary_path),
        "run_root": str(run_root),
        "evidence_path": str(evidence_path),
        "allure_status": allure_status,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive pytest evidence for a mobile CI run.")
    parser.add_argument("--report-root", required=True, type=Path)
    parser.add_argument("--console", required=True, type=Path)
    parser.add_argument("--junit", required=True, type=Path)
    parser.add_argument("--exit-code", required=True, type=int)
    args = parser.parse_args()

    result = finalize_mobile_pytest_run(
        args.report_root,
        args.console,
        args.junit,
        args.exit_code,
    )
    print(f"Pytest evidence: {result['evidence_path']}")
    print(f"Summary: {result['summary_path']}")
    return 0 if args.exit_code == 0 and result["allure_status"] != "FAILED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
