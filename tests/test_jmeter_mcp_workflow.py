import pytest
import json

from quality_hub_backend.services.jmeter_mcp_workflow import (
    build_jmeter_mcp_import_workflow,
    build_jmeter_mcp_workflow,
    read_jmeter_execution_progress,
)


def test_build_jmeter_mcp_import_workflow_records_skill_gate_and_execution_boundary() -> None:
    workflow = build_jmeter_mcp_import_workflow(
        project_id="project-1",
        package_id="salary-trade",
        project_name="Salary Trade",
        source_jmx="requirements/salary-trade/outputs/jmeter/jmeter-plan.jmx",
        max_error_rate_pct=2,
        max_p95_ms=2500,
        max_p99_ms=4000,
        auto_stop={"min_samples": 25, "grace_period_seconds": 15},
        generation_skill={"name": "jmeter-ai-generator"},
        correction_skill={"name": "Smart-GenAI-Powered-JMeter"},
        preflight_path="requirements/salary-trade/outputs/jmeter/jmeter-plan.preflight.json",
        preflight_status="PASS_WITH_WARNINGS",
    )

    assert workflow["schema_version"] == "2.0"
    assert workflow["source_jmx"] == "requirements/salary-trade/outputs/jmeter/jmeter-plan.jmx"
    assert workflow["metadata"]["generation_skill"]["name"] == "jmeter-ai-generator"
    assert workflow["metadata"]["correction_skill"]["name"] == "Smart-GenAI-Powered-JMeter"
    assert workflow["metadata"]["execution_engine"] == "jmeter-mcp-server@0.3.1"
    assert workflow["metadata"]["execution_mode"] == "import_only"
    assert workflow["metadata"]["preflight_status"] == "PASS_WITH_WARNINGS"
    assert workflow["thresholds"] == {
        "max_error_rate_pct": 2.0,
        "max_p95_ms": 2500,
        "max_p99_ms": 4000,
    }
    assert workflow["auto_stop"]["enabled"] is True
    assert workflow["auto_stop"]["min_samples"] == 25
    assert workflow["auto_stop"]["grace_period_seconds"] == 15
    assert workflow["auto_stop"]["latency_consecutive_windows"] == 2
    assert "thread_groups" not in workflow
    assert "variables" not in workflow


def test_typed_mcp_generation_is_retired() -> None:
    with pytest.raises(RuntimeError, match="Typed MCP JMX generation has been retired"):
        build_jmeter_mcp_workflow(project_id="project-1")


def test_execution_progress_merges_bridge_phase_and_clamps_percent(tmp_path) -> None:
    progress_path = tmp_path / "execution-progress.json"
    progress_path.write_text(json.dumps({
        "phase": "html_report",
        "percent": 180,
        "message": "HTML report",
    }), encoding="utf-8")

    progress = read_jmeter_execution_progress(
        progress_path,
        {"elapsed_seconds": 32.5, "phase": "fallback"},
    )

    assert progress["phase"] == "html_report"
    assert progress["percent"] == 100
    assert progress["message"] == "HTML report"
    assert progress["elapsed_seconds"] == 32.5


def test_execution_progress_uses_fallback_when_file_is_incomplete(tmp_path) -> None:
    progress_path = tmp_path / "execution-progress.json"
    progress_path.write_text("{", encoding="utf-8")

    assert read_jmeter_execution_progress(
        progress_path,
        {"phase": "jmeter_execution", "percent": 40},
    ) == {"phase": "jmeter_execution", "percent": 40}
