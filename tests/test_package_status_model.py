import json
import os
from pathlib import Path

import app


def write_report(root: Path, folder: str, report_type: str, status: str) -> Path:
    target = root / "reports" / folder / "summary.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps({"report_type": report_type, "status": status}),
        encoding="utf-8",
    )
    return target


def ready_assets():
    return {
        "account_model": {"exists": True},
        "jmeter": {"exists": True},
    }


def test_asset_status_describes_assets_only():
    ready = app._package_asset_status(
        {"sources": 2, "test_points": 5, "test_cases": 8},
        ready_assets(),
    )
    draft = app._package_asset_status(
        {"sources": 1, "test_points": 0, "test_cases": 0},
        ready_assets(),
    )

    assert ready["status"] == "READY"
    assert draft["status"] == "DRAFT"


def test_generated_and_review_reports_do_not_count_as_execution(tmp_path):
    write_report(
        tmp_path,
        "scenario-plan",
        "REQUIREMENT_PACKAGE_SCENARIO_EXECUTION_PLAN",
        "READY",
    )
    write_report(
        tmp_path,
        "ai-review",
        "REQUIREMENT_PACKAGE_AI_REVIEW",
        "FAILED",
    )

    execution = app._package_execution_status(tmp_path)

    assert execution["status"] == "NOT_RUN"
    assert execution["count"] == 0


def test_execution_status_uses_latest_result_per_tool(tmp_path):
    old_jmeter = write_report(
        tmp_path,
        "jmeter-old",
        "REQUIREMENT_PACKAGE_JMETER_RUN",
        "FAILED",
    )
    new_jmeter = write_report(
        tmp_path,
        "jmeter-new",
        "REQUIREMENT_PACKAGE_JMETER_RUN",
        "PASSED",
    )
    newman = write_report(
        tmp_path,
        "newman-new",
        "REQUIREMENT_PACKAGE_NEWMAN_RUN",
        "FAILED",
    )
    os.utime(old_jmeter, (100, 100))
    os.utime(new_jmeter, (200, 200))
    os.utime(newman, (300, 300))

    execution = app._package_execution_status(tmp_path)
    tools = {item["tool"]: item["status"] for item in execution["tools"]}

    assert tools["jmeter"] == "PASSED"
    assert tools["newman"] == "FAILED"
    assert execution["status"] == "FAILED"


def test_preflight_combines_resource_and_data_checks(tmp_path):
    output_root = tmp_path / "outputs"
    output_root.mkdir()
    (output_root / "resource-preflight-check.json").write_text(
        json.dumps({"status": "READY_WITH_WARNINGS", "summary": {"suggestions": 1}}),
        encoding="utf-8",
    )
    (output_root / "data-preflight-check.json").write_text(
        json.dumps({"status": "READY"}),
        encoding="utf-8",
    )

    preflight = app._package_preflight_status(tmp_path)

    assert preflight["status"] == "READY_WITH_WARNINGS"
    assert {item["name"] for item in preflight["checks"]} == {"resource", "data"}


def test_quality_cannot_pass_when_real_execution_failed():
    quality = app._package_quality_status(
        {"status": "READY"},
        {"status": "READY"},
        {"status": "FAILED"},
        {"status": "PASSED"},
    )

    assert quality["status"] == "FAILED"


def test_salary_and_wealth_resource_manifests_remain_isolated():
    salary = app._load_yaml_file(app.REQUIREMENT_PACKAGE_ROOT / "salary-trade" / "resource_manifest.yaml")
    wealth = app._load_yaml_file(app.REQUIREMENT_PACKAGE_ROOT / "wealth-level" / "resource_manifest.yaml")
    salary_tables = {item["name"] for item in salary.get("mysql_tables") or []}

    assert salary.get("package_id") == "salary-trade"
    assert wealth.get("package_id") == "wealth-level"
    assert salary_tables == {
        "anchor_salary_trade_agent_whitelist",
        "anchor_salary_trade_order",
        "anchor_salary_trade_order_log",
        "anchor_salary_trade_evidence",
    }
    assert not salary.get("redis_patterns")
    assert salary != wealth


def test_fastapi_registers_package_status_sources():
    pytest = __import__("pytest")
    pytest.importorskip("fastapi")
    from quality_hub_backend.api.fastapi_app import create_app

    api = create_app()
    paths = {route.path for route in api.routes}

    assert "/api/projects/{project_id}/requirement-packages" in paths
    assert "/api/projects/{project_id}/requirement-packages/{package_id}/resource-preflight" in paths
    assert "/api/projects/{project_id}/requirement-packages/{package_id}/scenario-report" in paths
