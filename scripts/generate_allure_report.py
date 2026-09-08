from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]


def local_executable(name: str) -> str | None:
    candidates = (
        ROOT / "node_modules" / ".bin" / f"{name}.cmd",
        ROOT / ".venv" / "Scripts" / f"{name}.exe",
    )
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return shutil.which(name)


def child_by_name(element: ET.Element, name: str) -> ET.Element | None:
    return next((child for child in element if child.tag.rsplit("}", 1)[-1] == name), None)


def testcase_status(testcase: ET.Element) -> tuple[str, dict[str, str]]:
    failure = child_by_name(testcase, "failure")
    if failure is not None:
        return "failed", {
            "message": failure.attrib.get("message", "Assertion failed"),
            "trace": failure.text or "",
        }
    error = child_by_name(testcase, "error")
    if error is not None:
        return "broken", {
            "message": error.attrib.get("message", "Test execution error"),
            "trace": error.text or "",
        }
    skipped = child_by_name(testcase, "skipped")
    if skipped is not None:
        return "skipped", {"message": skipped.attrib.get("message", "Skipped")}
    return "passed", {}


def iter_testcases(path: Path) -> Iterable[ET.Element]:
    root = ET.parse(path).getroot()
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] == "testcase":
            yield element


def convert_junit(junit_files: list[Path], results_dir: Path) -> dict[str, Any]:
    results_dir.mkdir(parents=True, exist_ok=True)
    converted = 0
    status_counts: dict[str, int] = {}
    clock_ms = int(time.time() * 1000)

    for junit_path in junit_files:
        for testcase in iter_testcases(junit_path):
            status, details = testcase_status(testcase)
            duration_ms = max(0, int(float(testcase.attrib.get("time", "0") or 0) * 1000))
            case_uuid = str(uuid.uuid4())
            class_name = testcase.attrib.get("classname", junit_path.stem)
            case_name = testcase.attrib.get("name", "unnamed test")
            result = {
                "uuid": case_uuid,
                "historyId": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{class_name}:{case_name}")),
                "testCaseId": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{class_name}:{case_name}")),
                "fullName": f"{class_name}.{case_name}",
                "name": case_name,
                "status": status,
                "stage": "finished",
                "statusDetails": details,
                "start": clock_ms,
                "stop": clock_ms + duration_ms,
                "labels": [
                    {"name": "framework", "value": "junit"},
                    {"name": "suite", "value": class_name},
                    {"name": "source", "value": junit_path.name},
                ],
            }
            (results_dir / f"{case_uuid}-result.json").write_text(
                json.dumps(result, ensure_ascii=False), encoding="utf-8"
            )
            converted += 1
            status_counts[status] = status_counts.get(status, 0) + 1
            clock_ms += max(1, duration_ms)

    (results_dir / "executor.json").write_text(
        json.dumps(
            {
                "name": "AutoTest AI CLI",
                "type": "jenkins",
                "buildName": "AutoTest AI quality gate",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return {"converted": converted, "status_counts": status_counts}


def generate_report(results_dir: Path, report_dir: Path) -> subprocess.CompletedProcess[str]:
    allure = local_executable("allure")
    if not allure:
        raise FileNotFoundError("Allure CLI was not found; run platform.cmd setup-ci")
    return subprocess.run(
        [allure, "generate", str(results_dir), "--clean", "-o", str(report_dir)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert JUnit XML files and generate Allure HTML.")
    parser.add_argument("--junit", action="append", type=Path, required=True)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    junit_files = [path if path.is_absolute() else ROOT / path for path in args.junit]
    missing = [str(path) for path in junit_files if not path.is_file()]
    if missing:
        raise SystemExit(f"JUnit files do not exist: {', '.join(missing)}")

    results_dir = args.results_dir if args.results_dir.is_absolute() else ROOT / args.results_dir
    report_dir = args.report_dir if args.report_dir.is_absolute() else ROOT / args.report_dir
    summary_path = args.summary if args.summary.is_absolute() else ROOT / args.summary
    converted = convert_junit(junit_files, results_dir)
    process = generate_report(results_dir, report_dir)
    summary = {
        "schema_version": "1.0",
        "report_type": "ALLURE_CLI_REPORT",
        "status": "PASSED" if process.returncode == 0 else "FAILED",
        **converted,
        "junit_files": [str(path) for path in junit_files],
        "results_dir": str(results_dir),
        "report_index": str(report_dir / "index.html"),
        "stdout": process.stdout,
        "stderr": process.stderr,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(process.stdout, end="")
    if process.stderr:
        print(process.stderr, end="")
    print(f"Allure cases: {converted['converted']}")
    print(f"Allure report: {report_dir / 'index.html'}")
    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
