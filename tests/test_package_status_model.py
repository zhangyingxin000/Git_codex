import json
import os
import sys
import zipfile
from pathlib import Path

import app


def test_static_index_uses_backend_generated_build_id():
    html = app.render_static_index()

    assert "__BUILD_ID__" not in html
    assert f'data-build="{app.BUILD_ID}"' in html
    assert f"/app.js?v={app.BUILD_ID}" in html


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
    context_path = tmp_path / "runs" / "run-status" / "run-context.json"
    context_path.parent.mkdir(parents=True)
    context_path.write_text(
        json.dumps(
            {
                "run_id": "run-status",
                "created_at": "2026-09-02T10:00:00+08:00",
                "tools": {},
            }
        ),
        encoding="utf-8",
    )
    for report in (old_jmeter, new_jmeter, newman):
        payload = json.loads(report.read_text(encoding="utf-8"))
        payload["run_id"] = "run-status"
        report.write_text(json.dumps(payload), encoding="utf-8")
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


def test_scenario_preflight_does_not_block_planned_review_scenario_without_cases(
    tmp_path,
):
    output_root = tmp_path / "outputs"
    output_root.mkdir(parents=True)
    (output_root / "execution-plan.json").write_text(
        json.dumps(
            {
                "scenarios": [
                    {
                        "scenario_id": "planned_review",
                        "name": "待补充场景",
                        "status": "NEEDS_REVIEW",
                        "cases": [],
                        "tool_tasks": [
                            {
                                "tool": "manual",
                                "cases": [],
                                "blockers": ["待确认覆盖范围"],
                            }
                        ],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = app._scenario_data_preflight("wealth-level", tmp_path, {})

    assert result["status"] == "READY_WITH_WARNINGS"
    assert result["summary"]["blocked"] == 0
    assert result["summary"]["warnings"] == 1
    assert result["scenarios"][0]["blockers"] == []
    assert "暂未绑定测试用例" in " ".join(result["scenarios"][0]["attentions"])


def test_negative_case_query_variant_preserves_missing_and_invalid_uid():
    base = "/level/exeperience/v2/get?ticket=abc&uid=123&language=en"

    missing = app._apply_case_query_variant({"title": "缺失UID参数"}, base)
    invalid = app._apply_case_query_variant({"title": "非法UID类型"}, base)
    generic_missing = app._apply_case_query_variant({"title": "缺失必填参数"}, base)
    generic_invalid = app._apply_case_query_variant(
        {"title": "字段边界与类型错误"}, base
    )

    assert "uid=" not in missing.lower()
    assert "ticket=abc" in missing
    assert "uid=not-a-number" in invalid
    assert "uid=" not in generic_missing.lower()
    assert "uid=not-a-number" in generic_invalid


def test_generated_pytest_separates_http_and_business_code_contracts():
    script = app.build_pytest_script(
        {"base_url": "https://example.test"},
        [
            {
                "id": "negative-case",
                "title": "缺失UID参数",
                "method": "GET",
                "path": "/level/get",
                "expected_status": 400,
            }
        ],
    )

    assert "def http_case_passed(result):" in script
    assert "if 200 <= expected_status < 300:" in script
    assert (
        "http_failed = sum(1 for x in http_results if not http_case_passed(x))"
        in script
    )
    compile(script, "pytest_api_cases.py", "exec")


def test_postman_collection_uses_role_specific_salary_credentials():
    runtime = {
        "applicant_uid": "1001",
        "applicant_ticket": "applicant-token",
        "proxy_uid": "2002",
        "proxy_ticket": "proxy-token",
    }
    cases = [
        {
            "title": "申请人查询额度",
            "method": "GET",
            "path": "/userserv/salary/trade/quota",
            "headers": "{}",
            "payload": "",
            "expected_status": 200,
        },
        {
            "title": "代理查询订单",
            "method": "GET",
            "path": "/userserv/salary/trade/agent/order/page",
            "headers": "{}",
            "payload": "",
            "expected_status": 200,
        },
    ]

    collection = app.build_postman_collection(
        {"name": "salary", "base_url": "https://example.test"}, cases, runtime, False
    )
    applicant_url = collection["item"][0]["request"]["url"]
    proxy_url = collection["item"][1]["request"]["url"]

    assert "uid=1001" in applicant_url and "ticket=applicant-token" in applicant_url
    assert "uid=2002" in proxy_url and "ticket=proxy-token" in proxy_url


def test_quality_cannot_pass_when_real_execution_failed():
    quality = app._package_quality_status(
        {"status": "READY"},
        {"status": "READY"},
        {"status": "FAILED"},
        {"status": "PASSED"},
    )

    assert quality["status"] == "FAILED"


def test_salary_and_wealth_resource_manifests_remain_isolated():
    salary = app._load_yaml_file(
        app.REQUIREMENT_PACKAGE_ROOT / "salary-trade" / "resource_manifest.yaml"
    )
    wealth = app._load_yaml_file(
        app.REQUIREMENT_PACKAGE_ROOT / "wealth-level" / "resource_manifest.yaml"
    )
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
    assert (
        "/api/projects/{project_id}/requirement-packages/{package_id}/resource-preflight"
        in paths
    )
    assert (
        "/api/projects/{project_id}/requirement-packages/{package_id}/scenario-report"
        in paths
    )
    assert (
        "/api/projects/{project_id}/requirement-packages/{package_id}/pipeline/run"
        in paths
    )
    assert (
        "/api/projects/{project_id}/requirement-packages/{package_id}/report-index"
        in paths
    )
    assert "/api/projects/{project_id}/requirement-packages/{package_id}/runs" in paths
    assert (
        "/api/projects/{project_id}/requirement-packages/{package_id}/runs/{run_id}"
        in paths
    )
    assert (
        "/api/projects/{project_id}/requirement-packages/{package_id}/schema-audit"
        in paths
    )
    assert (
        "/api/projects/{project_id}/requirement-packages/{package_id}/apifox-export"
        in paths
    )
    assert (
        "/api/projects/{project_id}/requirement-packages/{package_id}/apifox/openapi/import"
        in paths
    )
    assert (
        "/api/projects/{project_id}/requirement-packages/{package_id}/apifox-cli/run"
        in paths
    )
    assert not any(path.endswith("/api" + "post-package") for path in paths)


def test_apifox_export_is_package_scoped_importable_and_secret_free(
    monkeypatch, tmp_path
):
    package_root = tmp_path / "salary-trade"
    package_root.mkdir()
    token = "eyJhbGciOiJIUzI1NiJ9.eyJ1aWQiOjEwMDF9.signature"
    cases = [
        {
            "id": "case-salary-quota",
            "title": "申请人查询工资额度",
            "module": "工资交易",
            "method": "GET",
            "path": f"/userserv/salary/trade/quota?uid=1001&ticket={token}&currency=USD",
            "headers": json.dumps({"Authorization": token}),
            "payload": "",
            "expected_status": 200,
            "expected": "返回额度信息",
        }
    ]
    monkeypatch.setattr(
        app,
        "row",
        lambda *_args, **_kwargs: {
            "id": "project",
            "name": "质量中枢",
            "base_url": "https://test.example.com",
        },
    )
    monkeypatch.setattr(
        app,
        "requirement_package_by_id",
        lambda *_args, **_kwargs: {
            "package_id": "salary-trade",
            "name": "工资交易",
            "root": str(package_root),
        },
    )
    monkeypatch.setattr(
        app, "_requirement_package_cases", lambda *_args, **_kwargs: cases
    )
    monkeypatch.setattr(app, "REQUIREMENT_PACKAGE_ROOT", tmp_path)
    monkeypatch.setattr(
        app,
        "build_project_interface_document",
        lambda *_args, **_kwargs: {
            "openapi": "3.0.3",
            "info": {"title": "project", "version": "1"},
            "servers": [{"url": "https://test.example.com"}],
            "paths": {
                "/another-package/path": {
                    "get": {"responses": {"200": {"description": "ok"}}}
                }
            },
        },
    )

    result = app.build_apifox_collaboration_package("project", "salary-trade")
    output = package_root / "outputs" / "apifox"
    openapi_doc = json.loads((output / "openapi.json").read_text(encoding="utf-8"))
    collection = json.loads(
        (output / "postman-collection.json").read_text(encoding="utf-8")
    )
    environment = json.loads(
        (output / "postman-environment.json").read_text(encoding="utf-8")
    )
    mapping = json.loads((output / "case-api-mapping.json").read_text(encoding="utf-8"))
    exported_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in output.rglob("*")
        if path.is_file() and path.suffix in {".json", ".curl", ".md"}
    )

    assert result["package_id"] == "salary-trade"
    assert set(openapi_doc["paths"]) == {"/userserv/salary/trade/quota"}
    assert collection["info"]["schema"].endswith("collection.json")
    first_request = collection["item"][0]["item"][0]["request"]
    assert first_request["url"].startswith("{{baseUrl}}/")
    assert "{{applicant_ticket}}" in first_request["url"]
    assert {item["key"] for item in environment["values"]} >= {
        "baseUrl",
        "mockBaseUrl",
        "applicant_uid",
        "proxy_uid",
    }
    assert {item["key"] for item in environment["values"]}.isdisjoint({"uid", "ticket"})
    assert mapping["mappings"][0]["case_id"] == "case-salary-quota"
    assert mapping["mappings"][0]["curl_file"].endswith(".curl")
    assert token not in exported_text
    with zipfile.ZipFile(result["zip_path"]) as archive:
        names = set(archive.namelist())
    assert {
        "openapi.json",
        "postman-collection.json",
        "postman-environment.json",
        "case-api-mapping.json",
    } <= names


def test_apifox_openapi_generates_scoped_pytest_without_overwriting_business(
    monkeypatch, tmp_path
):
    package_root = tmp_path / "pkg"
    package_root.mkdir()
    monkeypatch.setattr(app, "REQUIREMENT_PACKAGE_ROOT", tmp_path)
    monkeypatch.setattr(
        app,
        "requirement_package_by_id",
        lambda *_args, **_kwargs: {
            "package_id": "pkg",
            "name": "接口需求",
            "root": str(package_root),
        },
    )
    monkeypatch.setattr(
        app,
        "row",
        lambda *_args, **_kwargs: {
            "id": "project",
            "name": "项目",
            "base_url": "https://example.test",
        },
    )
    monkeypatch.setattr(
        app,
        "_requirement_package_cases",
        lambda *_args, **_kwargs: [
            {
                "id": "case-one",
                "method": "GET",
                "path": "/users/{uid}",
            }
        ],
    )
    document = {
        "openapi": "3.0.3",
        "info": {"title": "Apifox", "version": "1.0"},
        "paths": {
            "/users/{uid}": {
                "get": {
                    "operationId": "get_user",
                    "parameters": [
                        {
                            "name": "uid",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {"schema": {"type": "object"}}
                            },
                        }
                    },
                }
            },
            "/other": {"get": {"responses": {"200": {"description": "ok"}}}},
        },
    }

    first = app.import_apifox_openapi_to_package(
        "project", "pkg", {"content": json.dumps(document)}
    )
    business_file = package_root / "outputs" / "pytest" / "business" / "test_manual.py"
    business_file.write_text("MANUAL = True\n", encoding="utf-8")
    second = app.import_apifox_openapi_to_package(
        "project", "pkg", {"content": json.dumps(document)}
    )
    generated = (
        package_root / "outputs" / "pytest" / "generated" / "test_openapi_contract.py"
    )

    assert first["selection_mode"] == "full_openapi_with_case_mapping"
    assert first["summary"]["pytest_operations"] == 2
    assert second["source_changed"] is False
    assert business_file.read_text(encoding="utf-8") == "MANUAL = True\n"
    compile(generated.read_text(encoding="utf-8"), str(generated), "exec")


def test_apifox_cli_run_is_attached_to_requirement_run(monkeypatch, tmp_path):
    package_root = tmp_path / "pkg"
    package_root.mkdir()
    monkeypatch.setattr(app, "REQUIREMENT_PACKAGE_ROOT", tmp_path)
    monkeypatch.setattr(
        app,
        "requirement_package_by_id",
        lambda *_args, **_kwargs: {
            "package_id": "pkg",
            "name": "接口需求",
            "root": str(package_root),
        },
    )
    monkeypatch.setattr(app, "load_environment_config", lambda *_args, **_kwargs: {})
    result = app.run_requirement_package_apifox_cli(
        "project",
        "pkg",
        {
            "run_id": "run-apifox",
            "profile": {
                "enabled": True,
                "command": [sys.executable, "-c", "print('requests: 3\\nfailures: 0')"],
                "required_env": [],
            },
        },
    )
    context = app.get_requirement_run_context("project", "pkg", "run-apifox")

    assert result["status"] == "PASSED"
    assert result["summary"]["requests"] == 3
    assert result["summary"]["failures"] == 0
    assert context["tools"]["apifox"]["status"] == "PASSED"


def test_apifox_cli_redacts_token_and_flows_into_reviews(monkeypatch, tmp_path):
    package_root = tmp_path / "pkg"
    (package_root / "outputs").mkdir(parents=True)
    (package_root / "outputs" / "execution-plan.json").write_text(
        json.dumps(
            {
                "scenarios": [
                    {
                        "scenario_id": "smoke-main",
                        "name": "核心发布链路",
                        "tool_tasks": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(app, "REQUIREMENT_PACKAGE_ROOT", tmp_path)
    monkeypatch.setattr(
        app,
        "requirement_package_by_id",
        lambda *_args, **_kwargs: {
            "package_id": "pkg",
            "name": "接口需求",
            "root": str(package_root),
            "status": "READY",
        },
    )
    monkeypatch.setattr(app, "load_environment_config", lambda *_args, **_kwargs: {})
    monkeypatch.setenv("APIFOX_ACCESS_TOKEN", "secret-apifox-token")

    cli_result = app.run_requirement_package_apifox_cli(
        "project",
        "pkg",
        {
            "run_id": "run-apifox-review",
            "profile": {
                "enabled": True,
                "command": [
                    sys.executable,
                    "-c",
                    "import pathlib, sys; pathlib.Path('apifox-result.json').write_text('{\"token\": \"' + sys.argv[1] + '\"}', encoding='utf-8'); print('requests: 2\\nfailures: 0\\ntoken=' + sys.argv[1])",
                    "${APIFOX_ACCESS_TOKEN}",
                ],
                "required_env": ["APIFOX_ACCESS_TOKEN"],
                "report_globs": ["apifox-result.json"],
            },
        },
    )
    unified = app.generate_requirement_package_unified_scenario_report(
        "project", "pkg", {"run_id": "run-apifox-review"}
    )
    review = app.generate_requirement_package_ai_review(
        "project", "pkg", {"run_id": "run-apifox-review", "use_model": False}
    )

    stdout = Path(cli_result["raw"]["stdout"]).read_text(encoding="utf-8")
    assert "secret-apifox-token" not in stdout
    assert "***REDACTED***" in stdout
    assert "secret-apifox-token" not in json.dumps(cli_result)
    assert len(cli_result["raw"]["artifacts"]) == 1
    archived_artifact = Path(cli_result["raw"]["artifacts"][0]).read_text(
        encoding="utf-8"
    )
    assert "secret-apifox-token" not in archived_artifact
    assert "***REDACTED***" in archived_artifact
    assert unified["tools"]["apifox"]["status"] == "PASSED"
    assert unified["summary"]["apifox_status"] == "PASSED"
    assert review["execution_signals"]["apifox_reports"] == 1


def test_report_index_tracks_latest_report_per_type(monkeypatch, tmp_path):
    monkeypatch.setattr(
        app,
        "requirement_package_by_id",
        lambda _project, package_id: {
            "package_id": package_id,
            "name": "测试需求包",
            "root": str(tmp_path),
        },
    )
    run = app.create_requirement_run_context("project", "pkg", {"run_id": "run-index"})
    first = write_report(
        tmp_path, "newman-old", "REQUIREMENT_PACKAGE_NEWMAN_RUN", "FAILED"
    )
    second = write_report(
        tmp_path, "newman-new", "REQUIREMENT_PACKAGE_NEWMAN_RUN", "PASSED"
    )
    pytest_report = write_report(
        tmp_path, "pytest-new", "REQUIREMENT_PACKAGE_PYTEST_EVIDENCE_RUN", "BLOCKED"
    )
    for report in (first, second, pytest_report):
        payload = json.loads(report.read_text(encoding="utf-8"))
        payload["run_id"] = run["run_id"]
        report.write_text(json.dumps(payload), encoding="utf-8")
    now_ts = 2_000_000_000
    os.utime(first, (now_ts - 300, now_ts - 300))
    os.utime(second, (now_ts - 200, now_ts - 200))
    os.utime(pytest_report, (now_ts - 100, now_ts - 100))

    index = app.requirement_package_report_index("project", "pkg", persist=False)
    latest = {item["report_type"]: item for item in index["latest_reports"]}

    assert index["summary"]["batches"] == 3
    assert latest["REQUIREMENT_PACKAGE_NEWMAN_RUN"]["batch_id"] == "newman-new"
    assert latest["REQUIREMENT_PACKAGE_PYTEST_EVIDENCE_RUN"]["status"] == "BLOCKED"


def test_run_context_groups_reports_without_mixing_batches(monkeypatch, tmp_path):
    monkeypatch.setattr(
        app,
        "requirement_package_by_id",
        lambda _project, package_id: {
            "package_id": package_id,
            "name": "测试需求包",
            "root": str(tmp_path),
        },
    )
    run = app.create_requirement_run_context("project", "pkg", {"run_id": "run-one"})
    first = write_report(
        tmp_path, "newman-one", "REQUIREMENT_PACKAGE_NEWMAN_RUN", "PASSED"
    )
    first_payload = json.loads(first.read_text(encoding="utf-8"))
    first_payload.update(
        {"run_id": run["run_id"], "package_id": "pkg", "summary": {"requests": 3}}
    )
    first.write_text(json.dumps(first_payload), encoding="utf-8")
    second = write_report(
        tmp_path, "newman-two", "REQUIREMENT_PACKAGE_NEWMAN_RUN", "FAILED"
    )
    second_payload = json.loads(second.read_text(encoding="utf-8"))
    second_payload.update({"run_id": "run-two", "package_id": "pkg"})
    second.write_text(json.dumps(second_payload), encoding="utf-8")
    app.update_requirement_run_context(
        "project",
        "pkg",
        run["run_id"],
        "newman",
        "PASSED",
        {
            "report_type": "REQUIREMENT_PACKAGE_NEWMAN_RUN",
            "status": "PASSED",
            "summary_path": str(first),
        },
    )

    index = app.requirement_package_report_index("project", "pkg", persist=False)
    indexed_run = next(item for item in index["runs"] if item["run_id"] == "run-one")

    assert indexed_run["report_count"] == 1
    assert indexed_run["reports"][0]["status"] == "PASSED"
    assert all(item["run_id"] == "run-one" for item in indexed_run["reports"])
    assert index["summary"]["ignored_legacy_reports"] == 1


def test_frontend_uses_package_report_center_without_legacy_fallback():
    script = (app.STATIC / "app.js").read_text(encoding="utf-8")

    assert "innerHTML=professionalReportCenter" not in script
    assert "innerHTML=packageReportCenter" in script
    assert "function packageReportCenter()" in script


def test_schema_audit_allows_compatible_old_versions(monkeypatch, tmp_path):
    monkeypatch.setattr(
        app,
        "requirement_package_by_id",
        lambda _project, package_id: {
            "package_id": package_id,
            "name": "测试需求包",
            "root": str(tmp_path),
        },
    )
    (tmp_path / "outputs").mkdir()
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "package_id": "pkg",
                "name": "测试需求包",
                "artifacts": {},
                "workflow": [],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "resource_manifest.yaml").write_text(
        "schema_version: '1.0'\npackage_id: pkg\ncredentials: []\ndatasets: []\nmysql_tables: []\nredis_patterns: []\n",
        encoding="utf-8",
    )
    (tmp_path / "account_model.yaml").write_text(
        "schema_version: '1.0'\npackage_id: pkg\nmode: single_account\nroles: []\ncredential_resolution_order: []\n",
        encoding="utf-8",
    )
    (tmp_path / "outputs" / "structured-test-cases.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "package_id": "pkg",
                "summary": {},
                "cases": [],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "outputs" / "case-jmeter-mapping.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "package_id": "pkg",
                "summary": {},
                "mappings": [],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "outputs" / "execution-plan.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "package_id": "pkg",
                "summary": {},
                "scenarios": [],
            }
        ),
        encoding="utf-8",
    )

    audit = app.validate_requirement_package_schemas("project", "pkg", persist=False)

    assert audit["status"] == "READY_WITH_WARNINGS"
    assert audit["summary"]["failed"] == 0
    assert audit["summary"]["warnings"] == 6


def test_schema_upgrade_backs_up_assets_before_writing(monkeypatch, tmp_path):
    monkeypatch.setattr(
        app,
        "requirement_package_by_id",
        lambda _project, package_id: {
            "package_id": package_id,
            "name": "测试需求包",
            "root": str(tmp_path),
        },
    )
    (tmp_path / "outputs").mkdir()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "package_id": "pkg",
                "name": "测试需求包",
                "artifacts": {},
                "workflow": [],
            }
        ),
        encoding="utf-8",
    )

    result = app.upgrade_requirement_package_schemas("project", "pkg")
    manifest_change = next(
        item for item in result["changed"] if item["asset"] == "manifest"
    )
    backup_path = Path(manifest_change["backup_path"])

    assert (
        json.loads(manifest_path.read_text(encoding="utf-8"))["schema_version"]
        == app.ASSET_SCHEMA_VERSION
    )
    assert backup_path.is_file()
    assert (
        json.loads(backup_path.read_text(encoding="utf-8"))["schema_version"] == "1.0"
    )
    assert "schema-upgrade-backups" in str(backup_path)
