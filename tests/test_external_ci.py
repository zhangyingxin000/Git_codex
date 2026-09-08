from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_external_cli_pipeline_reports_disabled_stages_as_skipped(tmp_path: Path) -> None:
    config = tmp_path / "ci-tools.yaml"
    config.write_text(
        """schema_version: \"1.0\"
stages:
  - name: disabled-newman
    tool: newman
    enabled: false
    required: true
""",
        encoding="utf-8",
    )
    report_root = tmp_path / "reports"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_external_ci.py"),
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
    assert summary["steps"][0]["status"] == "SKIPPED"


def test_external_cli_pipeline_blocks_missing_required_inputs(tmp_path: Path) -> None:
    config = tmp_path / "ci-tools.yaml"
    config.write_text(
        """schema_version: \"1.0\"
stages:
  - name: missing-collection
    tool: newman
    enabled: true
    required: true
    collection: missing.json
""",
        encoding="utf-8",
    )
    report_root = tmp_path / "reports"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_external_ci.py"),
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

    assert completed.returncode == 1
    summary_path = next(report_root.glob("*/summary.json"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "FAILED"
    assert summary["steps"][0]["status"] == "FAILED"
    assert "does not exist" in summary["steps"][0]["reason"]
