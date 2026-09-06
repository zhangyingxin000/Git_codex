import base64
import json
from pathlib import Path

import app


def _case(path="/union/getAnchorApplyRecord"):
    return {
        "title": "正常请求",
        "method": "GET",
        "path": path,
        "headers": "{}",
        "payload": "",
        "expected_status": 200,
    }


def test_jmeter_load_jmx_uses_runtime_properties_without_embedding_ticket():
    runtime = {
        "uid": "1455113",
        "ticket": "real-secret-ticket",
        "appCode": "100156",
        "appVersion": "100.1.5.6",
        "version": "100.1.5.6",
        "os": "android",
    }
    placeholders = app._runtime_placeholder_context(runtime, "jmeter_vars")
    jmx = app.build_jmeter_jmx(
        {"name": "test", "base_url": "https://example.test"},
        [_case()],
        placeholders,
        False,
        {"_jmeter_runtime_defaults": runtime, "_jmeter_non_gui_plan": True},
    )

    assert "real-secret-ticket" not in jmx
    assert '<stringProp name="Argument.value">***REDACTED***</stringProp>' not in jmx
    assert "ticket=${ticket}" in jmx
    assert "uid=${uid}" in jmx
    assert "appCode=${appCode}" in jmx
    assert "100156" in jmx
    assert "1454694" not in jmx


def test_jmeter_load_jmx_replaces_stale_query_credentials_with_runtime_variables():
    runtime = {"uid": "1455113", "ticket": "fresh-ticket", "appCode": "100156"}
    case = _case("/union/getAnchorApplyRecord?uid=1454696&ticket=expired-ticket&appCode=999")

    jmx = app.build_jmeter_jmx(
        {"name": "test", "base_url": "https://example.test"},
        [case],
        runtime,
        True,
        {"_jmeter_runtime_defaults": runtime, "_jmeter_non_gui_plan": True},
    )

    assert "1454696" not in jmx
    assert "expired-ticket" not in jmx
    assert "appCode=999" not in jmx
    assert "uid=${uid}" in jmx
    assert "ticket=${ticket}" in jmx
    assert "appCode=${appCode}" in jmx


def test_preflight_resolved_performance_case_does_not_append_unrelated_runtime_query_fields():
    runtime = {
        "uid": "1001",
        "ticket": "secret-ticket",
        "countryCode": "SA",
        "currency": "SAR",
        "pageSize": "20",
        "agentUid": "should-not-be-added",
        "proxyUid": "should-not-be-added",
        "appsflyerId": "should-not-be-added",
    }
    case = {
        **_case("/userserv/salary/trade/agents?uid={{uid}}&ticket={{ticket}}&countryCode={{countryCode}}&currency={{currency}}&pageNum=1&pageSize={{pageSize}}"),
        "_performance_resolved_inputs": {
            "uid": "{{uid}}",
            "ticket": "{{ticket}}",
            "countryCode": "{{countryCode}}",
            "currency": "{{currency}}",
            "pageNum": "1",
            "pageSize": "{{pageSize}}",
        },
    }

    jmx = app.build_jmeter_jmx(
        {"name": "test", "base_url": "https://example.test"},
        [case],
        runtime,
        True,
        {
            "_jmeter_runtime_defaults": runtime,
            "_jmeter_non_gui_plan": True,
            "_jmeter_targets_prevalidated": True,
            "_jmeter_account_columns": ["applicant_uid", "applicant_ticket"],
        },
    )

    assert "pageNum=1" in jmx
    assert "pageSize=${pageSize}" in jmx
    assert "agentUid=" not in jmx
    assert "proxyUid=" not in jmx
    assert "appsflyerId=" not in jmx


def test_performance_jmx_contains_transaction_sync_and_thread_pinned_accounts():
    runtime = {"appCode": "100156", "t": "1788620000000"}
    jmx = app.build_jmeter_jmx(
        {"name": "test", "base_url": "https://example.test"},
        [_case("/api/performance/read?uid={{uid}}&ticket={{ticket}}")],
        runtime,
        True,
        {
            "jmeter_threads": 8,
            "_jmeter_non_gui_plan": True,
            "_jmeter_performance_profile": "concurrency",
            "_jmeter_transaction_name": "salary-trade-flow",
            "_jmeter_transaction_mode": "business_transaction",
            "_jmeter_account_columns": ["applicant_uid", "applicant_ticket", "proxy_uid", "proxy_ticket"],
        },
    )

    assert 'testname="TX::salary-trade-flow"' in jmx
    assert '<boolProp name="TransactionController.parent">true</boolProp>' in jmx
    assert 'testname="并发同时释放"' in jmx
    assert '<intProp name="groupSize">8</intProp>' in jmx
    assert '<stringProp name="ThreadGroup.num_threads">8</stringProp>' in jmx
    assert '<stringProp name="ThreadGroup.ramp_time">1</stringProp>' in jmx
    assert '<intProp name="ThreadGroup.num_threads">' not in jmx
    assert "__performance_account_initialized" in jmx
    assert 'def accountColumns = ["applicant_ticket", "applicant_uid", "proxy_ticket", "proxy_uid"]' in jmx
    assert "vars.put('__performance_account_' + name, value)" in jmx
    assert "vars.put('t', String.valueOf(System.currentTimeMillis()))" in jmx
    assert "AUTOTEST_AUTH_CONTEXT uid=" in jmx
    assert "AUTOTEST_AUTH_FAILURE url=" in jmx
    assert "__performance_account_rotate_requested" in jmx
    assert "__performance_account_rotate_requested_iteration" in jmx
    assert "requestedIteration != currentIteration" in jmx
    assert "AUTOTEST_ACCOUNT_ROTATED thread=" in jmx
    assert "AUTOTEST_ACCOUNT_POOL_EXHAUSTED thread=" in jmx
    assert "ctx.getThread().stop()" in jmx
    assert "AUTOTEST_JMETER_RUNTIME_ROWS_B64" in jmx
    assert "ctx.getThreadNum()" in jmx
    assert "token.split('[.]').length" in jmx
    assert "JMeter进程级账号数据缺少字段" not in jmx
    assert "uid=${applicant_uid}" in jmx
    assert '<stringProp name="Header.name">t</stringProp><stringProp name="Header.value">${__time(,)}</stringProp>' in jmx
    assert '<stringProp name="Header.name">Accept</stringProp><stringProp name="Header.value">application/json</stringProp>' in jmx
    assert 'testname="查看结果树" enabled="false"' in jmx


def test_spike_profile_only_synchronizes_the_actual_spike_phase():
    common = {
        "jmeter_threads": 8,
        "_jmeter_non_gui_plan": True,
        "_jmeter_performance_profile": "spike",
    }

    pre_spike = app.build_jmeter_jmx(
        {"name": "test", "base_url": "https://example.test"},
        [_case("/api/health")],
        {},
        True,
        {**common, "_jmeter_workload_phase": "pre-spike"},
    )
    spike = app.build_jmeter_jmx(
        {"name": "test", "base_url": "https://example.test"},
        [_case("/api/health")],
        {},
        True,
        {**common, "_jmeter_workload_phase": "spike"},
    )
    recovery = app.build_jmeter_jmx(
        {"name": "test", "base_url": "https://example.test"},
        [_case("/api/health")],
        {},
        True,
        {**common, "_jmeter_workload_phase": "recovery"},
    )

    assert 'testname="并发同时释放"' not in pre_spike
    assert 'testname="并发同时释放"' in spike
    assert 'testname="并发同时释放"' not in recovery


def test_performance_jmx_adds_declared_response_extractor_to_its_producer():
    jmx = app.build_jmeter_jmx(
        {"name": "test", "base_url": "https://example.test"},
        [
            {
                **_case("/userserv/salary/trade/order/create"),
                "method": "POST",
                "payload": '{"amount": 100}',
            },
            _case("/salary/trade/order/detail?orderNo=${salary_order_no}"),
        ],
        {"uid": "1001", "orderNo": "${salary_order_no}"},
        True,
        {
            "_jmeter_runtime_defaults": {"uid": "1001"},
            "_jmeter_non_gui_plan": True,
            "_jmeter_targets_prevalidated": True,
            "_jmeter_extraction_rules": [{
                "variable": "salary_order_no",
                "source_method": "POST",
                "source_path": "/userserv/salary/trade/order/create",
                "json_paths": ["$.data.orderNo"],
            }],
        },
    )

    assert 'testname="提取 salary_order_no"' in jmx
    assert '<stringProp name="JSONPostProcessor.referenceNames">salary_order_no</stringProp>' in jmx
    assert '<stringProp name="JSONPostProcessor.jsonPathExprs">$.data.orderNo</stringProp>' in jmx
    assert 'testname="校验关联变量 salary_order_no"' in jmx
    assert "响应未提取到必需关联变量: salary_order_no" in jmx
    assert "orderNo=${salary_order_no}" in jmx


def test_performance_jmx_enforces_openapi_response_contract_as_jtl_assertion():
    case = {
        **_case("/api/orders/detail"),
        "_performance_response_contract": {
            "content_type": "application/json",
            "require_json": True,
            "required_fields": ["code", "data", "message"],
            "field_types": {"code": "integer", "data": "object", "message": "string"},
            "non_empty_fields": ["data"],
            "business_code_field": "code",
            "success_codes": [200],
            "message_field": "message",
        },
    }

    jmx = app.build_jmeter_jmx(
        {"name": "test", "base_url": "https://example.test"},
        [case],
        {},
        True,
        {"_jmeter_non_gui_plan": True, "_jmeter_targets_prevalidated": True},
    )

    assert 'testname="OpenAPI结构与业务成功断言"' in jmx
    assert "响应缺少OpenAPI必填字段" in jmx
    assert "响应字段类型不符合OpenAPI" in jmx
    assert "响应字段不应为空" in jmx


def test_jmeter_business_assertion_repairs_empty_openapi_contract_for_transaction():
    case = {
        "_performance_response_contract": {
            "require_json": True,
            "business_code_field": "",
            "success_codes": [],
            "message_field": "",
        },
        "_performance_require_business_code": True,
    }

    assertion = app._jmeter_business_assertion_xml(case, 200)

    assert "响应缺少必需业务码字段" in assertion
    encoded = assertion.split("decode('", 1)[1].split("')", 1)[0]
    contract = json.loads(base64.b64decode(encoded).decode("utf-8"))
    assert contract["business_code_field"] == "code"
    assert contract["success_codes"] == [0, 200, "0", "200"]
    assert contract["message_field"] == "message"
    assert contract["require_business_code"] is True


def test_performance_runtime_contract_requires_current_generator_version():
    assert app.PERFORMANCE_RUNTIME_CONTRACT_VERSION == "5.5"


def test_performance_runtime_params_persist_only_explicit_non_sensitive_values():
    persisted = app._persistable_performance_runtime_params({
        "runtime_params": {
            "receiveAccountType": "bank",
            "userRemark": "performance-test",
            "ticket": "must-not-persist",
            "api_token": "must-not-persist",
            "password": "must-not-persist",
        }
    })

    assert persisted == {
        "receiveAccountType": "bank",
        "userRemark": "performance-test",
    }


def test_performance_stage_runtime_inherits_plan_values_and_allows_safe_override():
    options = app._performance_stage_runtime_options(
        {
            "runtime_params": {
                "receiveAccountType": "bank",
                "userRemark": "from-plan",
                "ticket": "must-not-persist",
            }
        },
        {
            "stage": 1,
            "runtime_params": {
                "userRemark": "from-stage",
                "reason": "quality-check",
                "password": "must-not-persist",
            },
        },
    )

    assert options["stage"] == 1
    assert options["runtime_params"] == {
        "receiveAccountType": "bank",
        "userRemark": "from-stage",
        "reason": "quality-check",
    }


def test_performance_options_distinguish_fillable_inputs_from_hard_blockers(
    monkeypatch,
    tmp_path,
):
    cases = [
        {
            "id": "fillable",
            "title": "可补参数事务",
            "method": "POST",
            "path": "/orders",
            "_performance_method": "POST",
            "_performance_path": "/orders",
            "_performance_key": "POST /orders",
        },
        {
            "id": "credential",
            "title": "缺少凭证事务",
            "method": "GET",
            "path": "/orders/detail",
            "_performance_method": "GET",
            "_performance_path": "/orders/detail",
            "_performance_key": "GET /orders/detail",
        },
    ]

    monkeypatch.setattr(
        app,
        "requirement_package_by_id",
        lambda *_: {
            "package_id": "demo",
            "name": "Demo",
            "root": str(tmp_path),
        },
    )
    monkeypatch.setattr(app, "row", lambda *_: {"base_url": "https://example.test"})
    monkeypatch.setattr(app, "_requirement_package_cases", lambda *_: cases)
    monkeypatch.setattr(
        app,
        "_performance_target_cases",
        lambda selected, _options=None: (list(selected), []),
    )
    monkeypatch.setattr(
        app,
        "project_execution_profile",
        lambda *_: {"performance": {"profile": "baseline"}},
    )
    monkeypatch.setattr(app, "_runtime_context", lambda *_: {})
    monkeypatch.setattr(app, "_performance_manifest_runtime_context", lambda _root, runtime: runtime)
    monkeypatch.setattr(
        app,
        "_performance_profile_catalog",
        lambda: [{"profile": "baseline", "threads": 1}],
    )
    monkeypatch.setattr(
        app,
        "_performance_transaction_scenarios",
        lambda *_: [
            {
                "scenario_id": "fillable-flow",
                "name": "可补参数事务",
                "steps": [{"case_id": "fillable"}],
                "blockers": [],
                "_cases": [cases[0]],
            },
            {
                "scenario_id": "credential-flow",
                "name": "缺少凭证事务",
                "steps": [{"case_id": "credential"}],
                "blockers": [],
                "_cases": [cases[1]],
            },
        ],
    )

    def fake_preflight(_root, selected, _runtime, _columns):
        targets = []
        for case in selected:
            if case["id"] == "fillable":
                missing = [{
                    "name": "request_body",
                    "location": "body",
                    "reason": "缺少请求体字段",
                    "missing_fields": ["receiveAccountType", "userRemark"],
                }]
            else:
                missing = [{
                    "name": "ticket",
                    "location": "query",
                    "reason": "缺少凭证来源",
                }]
            targets.append({
                "key": case["_performance_key"],
                "status": "BLOCKED",
                "missing": missing,
            })
        return {"status": "BLOCKED", "targets": targets}

    monkeypatch.setattr(app, "_performance_target_preflight", fake_preflight)

    result = app.requirement_performance_options("project-1", "demo")
    by_id = {item["scenario_id"]: item for item in result["transactions"]}

    assert by_id["fillable-flow"]["status"] == "NEEDS_INPUT"
    assert [
        item["name"]
        for item in by_id["fillable-flow"]["required_runtime_inputs"]
    ] == ["receiveAccountType", "userRemark"]
    assert by_id["credential-flow"]["status"] == "BLOCKED"
    assert by_id["credential-flow"]["required_runtime_inputs"][0]["sensitive"] is True
    assert "账号CSV" in by_id["credential-flow"]["input_blockers"][0]


def test_performance_manifest_runtime_context_reads_non_sensitive_values(monkeypatch, tmp_path):
    monkeypatch.setattr(
        app,
        "_load_yaml_file",
        lambda _: {
            "runtime_parameters": [
                {"name": "receiveAccountType", "value": "bank", "purpose": "收款方式"},
                {"name": "reason", "value": "quality-hub-test", "purpose": "测试备注"},
                {"name": "ticket", "value": "must-not-persist"},
            ]
        },
    )

    context = app._performance_manifest_runtime_context(
        tmp_path,
        {"reason": "caller-wins"},
    )

    assert context["receiveAccountType"] == "bank"
    assert context["reason"] == "caller-wins"
    assert "ticket" not in context
    assert context["_input_sources"]["receiveAccountType"]["type"] == "package_literal"
    assert any("敏感字段" in item for item in context["_runtime_warnings"])


def test_performance_transaction_scenarios_preserve_execution_plan_order(tmp_path):
    cases = [
        {"id": "create", "title": "创建订单：正常请求", "method": "POST", "path": "/api/orders"},
        {"id": "detail", "title": "查询订单：正常请求", "method": "GET", "path": "/api/orders/detail"},
        {"id": "negative", "title": "查询订单：缺失必填参数", "method": "GET", "path": "/api/orders/detail"},
    ]
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    (output_dir / "execution-plan.json").write_text(
        json.dumps({
            "scenarios": [{
                "scenario_id": "order-flow",
                "name": "创建并查询订单",
                "status": "READY",
                "transaction_steps": [
                    {"order": 1, "case_id": "create", "method": "POST", "path": "/api/orders", "action": "创建订单"},
                    {"order": 2, "case_id": "detail", "method": "GET", "path": "/api/orders/detail", "action": "查询订单"},
                ],
                "cases": [
                    {"id": "create"},
                    {"id": "detail"},
                    {"id": "negative"},
                ],
                "tool_tasks": [{"tool": "jmeter", "cases": ["create", "detail", "negative"], "blockers": []}],
            }]
        }, ensure_ascii=False),
        encoding="utf-8",
    )

    transactions = app._performance_transaction_scenarios(tmp_path, cases)

    assert len(transactions) == 1
    assert transactions[0]["scenario_id"] == "order-flow"
    assert transactions[0]["requires_mutation_permission"] is True
    assert [item["path"] for item in transactions[0]["steps"]] == [
        "/api/orders",
        "/api/orders/detail",
    ]


def test_performance_transaction_scenarios_block_implicit_case_order(tmp_path):
    cases = [
        {"id": "create", "title": "创建订单：正常请求", "method": "POST", "path": "/api/orders"},
        {"id": "cancel", "title": "取消订单：正常请求", "method": "POST", "path": "/api/orders/cancel"},
    ]
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    (output_dir / "execution-plan.json").write_text(
        json.dumps({
            "scenarios": [{
                "scenario_id": "unsafe-order-flow",
                "name": "未声明顺序的订单流",
                "status": "READY",
                "cases": [{"id": "create"}, {"id": "cancel"}],
                "tool_tasks": [{"tool": "jmeter", "cases": ["create", "cancel"], "blockers": []}],
            }]
        }, ensure_ascii=False),
        encoding="utf-8",
    )

    transactions = app._performance_transaction_scenarios(tmp_path, cases)

    assert len(transactions) == 1
    assert transactions[0]["steps"] == []
    assert any("禁止从用例集合猜测业务顺序" in item for item in transactions[0]["blockers"])


def test_performance_measurement_mode_requires_explicit_multi_step_transaction():
    assert app._performance_plan_measurement_mode(
        {
            "transaction": {"status": "NOT_SELECTED", "transaction_mode": "request_only"},
            "execution_context": {"transaction_mode": "business_transaction"},
        },
        {"transaction_mode": "business_transaction"},
    ) == "request_only"

    assert app._performance_plan_measurement_mode(
        {
            "transaction": {
                "scenario_id": "create-and-query",
                "steps": [
                    {"order": 1, "status": "READY"},
                    {"order": 2, "status": "READY"},
                ],
                "blockers": [],
            },
            "execution_context": {"transaction_mode": "business_transaction"},
        },
        {"transaction_mode": "business_transaction"},
    ) == "business_transaction"


def test_performance_stage_target_cases_restores_transaction_mutations_and_step_metadata(monkeypatch, tmp_path):
    cases = [
        {"id": "create", "title": "创建订单：正常请求", "method": "POST", "path": "/api/orders"},
        {"id": "cancel", "title": "取消订单：正常请求", "method": "POST", "path": "/api/orders/cancel"},
        {"id": "readonly", "title": "查询订单：正常请求", "method": "GET", "path": "/api/orders/detail"},
    ]
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    (output_dir / "execution-plan.json").write_text(
        json.dumps({
            "scenarios": [{
                "scenario_id": "create-cancel",
                "name": "创建并取消订单",
                "status": "READY",
                "transaction_steps": [
                    {
                        "order": 1,
                        "case_id": "create",
                        "method": "POST",
                        "path": "/api/orders",
                        "requires_proxy_reference": True,
                    },
                    {
                        "order": 2,
                        "case_id": "cancel",
                        "method": "POST",
                        "path": "/api/orders/cancel",
                    },
                ],
                "tool_tasks": [{"tool": "jmeter", "cases": ["create", "cancel"], "blockers": []}],
            }]
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(app, "_requirement_package_cases", lambda *_: cases)
    plan = {
        "execution_context": {
            "scenario_id": "create-cancel",
            "target_apis": ["POST /api/orders", "POST /api/orders/cancel"],
        },
        "transaction": {"scenario_id": "create-cancel"},
    }

    selected = app._performance_stage_target_cases("project", "package", tmp_path, plan)

    assert [item["_performance_key"] for item in selected] == [
        "POST /api/orders",
        "POST /api/orders/cancel",
    ]
    assert selected[0]["_performance_requires_proxy_reference"] is True


def test_salary_trade_load_runtime_selects_first_probe_valid_applicant(monkeypatch):
    applicants = [
        {"applicant_uid": "1001", "applicant_ticket": "ticket-1", "currency": "USD"},
        {"applicant_uid": "1002", "applicant_ticket": "ticket-2", "currency": "USD"},
    ]
    monkeypatch.setattr(app, "_role_csv_path", lambda *args: Path("applicants.csv"))
    monkeypatch.setattr(app, "_csv_rows_for_path", lambda path: applicants)
    monkeypatch.setattr(app, "_salary_trade_csv_runtime_context", lambda package_root, runtime: {"appCode": "100156", **(runtime or {})})
    monkeypatch.setattr(
        app,
        "_readonly_auth_probe",
        lambda project, cases, runtime, **kwargs: {
            "status": "PASSED" if runtime["uid"] == "1002" else "FAILED",
            "summary": "ok" if runtime["uid"] == "1002" else "401",
            "items": [{"http_status": 200 if runtime["uid"] == "1002" else 401}],
        },
    )

    runtime, preflight = app._salary_trade_load_runtime_context(
        {"base_url": "https://example.test"},
        Path("requirements/salary-trade"),
        [_case()],
        {},
    )

    assert runtime["uid"] == "1002"
    assert runtime["ticket"] == "ticket-2"
    assert runtime["appCode"] == "100156"
    assert preflight["status"] == "PASSED"
    assert preflight["csv_row"] == 2


def test_salary_trade_round_robin_live_preflight_requires_one_valid_applicant(monkeypatch, tmp_path):
    captured = {}
    monkeypatch.setattr(app, "_role_csv_path", lambda *_: tmp_path / "accounts.csv")
    monkeypatch.setattr(
        app,
        "_csv_rows_for_path",
        lambda _: [
            {"applicant_uid": "1001", "applicant_ticket": "ticket-1", "currency": "USD"},
            {"applicant_uid": "1002", "applicant_ticket": "ticket-2", "currency": "USD"},
        ],
    )
    monkeypatch.setattr(app, "_looks_like_jwt", lambda _: False)
    monkeypatch.setattr(
        app,
        "_salary_trade_account_pool_preflight",
        lambda project, package_root, cases, required_applicants, require_proxy: (
            captured.update({"required_applicants": required_applicants})
            or {
                "status": "PASSED",
                "summary": {},
                "applicants": [{"uid": "1001", "status": "PASSED"}],
                "proxies": [],
            }
        ),
    )

    pool = app._salary_trade_performance_account_pool(
        {"base_url": "https://example.test"},
        tmp_path,
        [{"method": "GET", "path": "/userserv/salary/trade/agents"}],
        threads=8,
        reuse_policy="round_robin",
        live_probe=True,
    )

    assert captured["required_applicants"] == 1
    assert pool["status"] == "READY_WITH_WARNINGS"
    assert pool["accounts"] == 1
    assert pool["reuse_ratio"] == 8.0
    assert "受控轮询复用" in pool["message"]


def test_salary_trade_strict_unique_live_preflight_requires_one_account_per_thread(monkeypatch, tmp_path):
    captured = {}
    monkeypatch.setattr(app, "_role_csv_path", lambda *_: tmp_path / "accounts.csv")
    monkeypatch.setattr(
        app,
        "_csv_rows_for_path",
        lambda _: [
            {"applicant_uid": "1001", "applicant_ticket": "ticket-1", "currency": "USD"},
            {"applicant_uid": "1002", "applicant_ticket": "ticket-2", "currency": "USD"},
        ],
    )
    monkeypatch.setattr(app, "_looks_like_jwt", lambda _: False)
    monkeypatch.setattr(
        app,
        "_salary_trade_account_pool_preflight",
        lambda project, package_root, cases, required_applicants, require_proxy: (
            captured.update({"required_applicants": required_applicants})
            or {
                "status": "BLOCKED",
                "summary": {},
                "applicants": [{"uid": "1001", "status": "PASSED"}],
                "proxies": [],
            }
        ),
    )

    pool = app._salary_trade_performance_account_pool(
        {"base_url": "https://example.test"},
        tmp_path,
        [{"method": "GET", "path": "/userserv/salary/trade/agents"}],
        threads=8,
        reuse_policy="strict_unique",
        live_probe=True,
    )

    assert captured["required_applicants"] == 8
    assert pool["status"] == "BLOCKED"


def test_salary_trade_create_transaction_requires_proxy_uid_but_not_proxy_auth(monkeypatch, tmp_path):
    applicant_path = tmp_path / "applicants.csv"
    proxy_path = tmp_path / "proxies.csv"
    monkeypatch.setattr(
        app,
        "_role_csv_path",
        lambda _root, role, _fallback: applicant_path if role == "applicant" else proxy_path,
    )
    monkeypatch.setattr(
        app,
        "_csv_rows_for_path",
        lambda path: (
            [{"applicant_uid": "1001", "applicant_ticket": "ticket-1", "currency": "USD"}]
            if path == applicant_path
            else [{"proxy_uid": "2001", "support_currencies": "USD"}]
        ),
    )
    monkeypatch.setattr(app, "_looks_like_jwt", lambda _: False)

    pool = app._salary_trade_performance_account_pool(
        {"base_url": "https://example.test"},
        tmp_path,
        [{
            "method": "POST",
            "path": "/userserv/salary/trade/order/create",
            "_performance_requires_proxy_reference": True,
        }],
        threads=1,
        reuse_policy="strict_unique",
        live_probe=False,
    )

    assert pool["status"] == "READY"
    assert pool["rows"][0]["proxy_uid"] == "2001"
    assert pool["rows"][0]["proxy_ticket"] == ""
    assert pool["role_requirements"] == {
        "applicant_auth": True,
        "proxy_reference": True,
        "proxy_auth": False,
    }


def test_salary_trade_mutation_transaction_uses_package_get_for_live_auth_probe(monkeypatch, tmp_path):
    applicant_path = tmp_path / "applicants.csv"
    proxy_path = tmp_path / "proxies.csv"
    captured = {}
    monkeypatch.setattr(
        app,
        "_role_csv_path",
        lambda _root, role, _fallback: applicant_path if role == "applicant" else proxy_path,
    )
    monkeypatch.setattr(
        app,
        "_csv_rows_for_path",
        lambda path: (
            [{"applicant_uid": "1001", "applicant_ticket": "ticket-1", "currency": "USD"}]
            if path == applicant_path
            else [{"proxy_uid": "2001", "support_currencies": "USD"}]
        ),
    )
    monkeypatch.setattr(app, "_looks_like_jwt", lambda _: False)
    monkeypatch.setattr(
        app,
        "_requirement_package_cases",
        lambda *_: [{
            "title": "申请记录：正常请求",
            "method": "GET",
            "path": "/union/getAnchorApplyRecord",
            "expected_status": 200,
        }],
    )

    def fake_preflight(_project, _root, cases, **_kwargs):
        captured["cases"] = cases
        return {
            "status": "PASSED",
            "summary": {},
            "applicants": [{"uid": "1001", "status": "PASSED"}],
            "proxies": [],
        }

    monkeypatch.setattr(app, "_salary_trade_account_pool_preflight", fake_preflight)
    monkeypatch.setattr(
        app,
        "_salary_trade_quota_account_preflight",
        lambda *_: {
            "status": "PASSED",
            "message": "ok",
            "accounts": [{"uid": "1001", "status": "PASSED"}],
        },
    )

    pool = app._salary_trade_performance_account_pool(
        {"id": "project-1", "base_url": "https://example.test"},
        tmp_path,
        [{
            "method": "POST",
            "path": "/userserv/salary/trade/order/create",
            "_performance_requires_proxy_reference": True,
        }],
        threads=1,
        reuse_policy="strict_unique",
        live_probe=True,
    )

    assert any(item["method"] == "GET" for item in captured["cases"])
    assert pool["status"] == "READY"
    assert pool["rows"][0]["applicant_uid"] == "1001"
    assert pool["rows"][0]["proxy_uid"] == "2001"
    assert pool["role_requirements"] == {
        "applicant_auth": True,
        "proxy_reference": True,
        "proxy_auth": False,
    }


def test_salary_trade_quota_preflight_blocks_insufficient_salary(monkeypatch):
    monkeypatch.setattr(
        app.urllib.request,
        "urlopen",
        lambda request, timeout=5: type(
            "Response",
            (),
            {
                "status": 200,
                "read": lambda self, size: (
                    b'{"code":200,"data":{"availableSalaryAmount":20,'
                    b'"processingSalary":0,"minApplyAmount":10}}'
                ),
            },
        )(),
    )
    quota_case = {
        "title": "查询工资额度：正常请求",
        "method": "GET",
        "path": "/userserv/salary/trade/quota",
        "headers": "{}",
        "payload": "",
        "expected_status": 200,
    }

    result = app._salary_trade_quota_account_preflight(
        {"base_url": "https://example.test"},
        quota_case,
        [{
            "applicant_uid": "1001",
            "applicant_ticket": "ticket-1",
            "salaryAmount": "50",
            "currency": "USD",
        }],
    )

    assert result["status"] == "BLOCKED"
    assert result["accounts"][0]["available_salary"] == "20"
    assert "小于申请金额50" in result["accounts"][0]["reason"]


def test_salary_trade_quota_preflight_accepts_ready_account(monkeypatch):
    monkeypatch.setattr(
        app.urllib.request,
        "urlopen",
        lambda request, timeout=5: type(
            "Response",
            (),
            {
                "status": 200,
                "read": lambda self, size: (
                    b'{"code":200,"data":{"availableSalaryAmount":100,'
                    b'"processingSalary":0,"minApplyAmount":50}}'
                ),
            },
        )(),
    )
    quota_case = {
        "title": "查询工资额度：正常请求",
        "method": "GET",
        "path": "/userserv/salary/trade/quota",
        "headers": "{}",
        "payload": "",
        "expected_status": 200,
    }

    result = app._salary_trade_quota_account_preflight(
        {"base_url": "https://example.test"},
        quota_case,
        [{
            "applicant_uid": "1001",
            "applicant_ticket": "ticket-1",
            "salaryAmount": "50",
            "currency": "USD",
        }],
    )

    assert result["status"] == "PASSED"
    assert result["accounts"][0]["status"] == "PASSED"


def test_salary_trade_account_preflight_scopes_resources_to_applicant_target(monkeypatch, tmp_path):
    package_root = tmp_path / "requirements" / "salary-trade"
    package_root.mkdir(parents=True)
    applicant_path = tmp_path / "applicants.csv"
    proxy_path = tmp_path / "proxies.csv"
    monkeypatch.setattr(app, "REQUIREMENT_PACKAGE_ROOT", tmp_path / "requirements")
    monkeypatch.setattr(
        app,
        "_role_csv_path",
        lambda _root, role, _fallback: applicant_path if role == "applicant" else proxy_path,
    )
    monkeypatch.setattr(
        app,
        "_csv_rows_for_path",
        lambda path: [{"uid": "1001", "ticket": "ticket-1", "currency": "USD"}] if path == applicant_path else [],
    )
    monkeypatch.setattr(
        app,
        "_load_yaml_file",
        lambda _path: {"credentials": [{"role": "applicant", "min_count": 8}]},
    )
    monkeypatch.setattr(app, "_salary_trade_csv_runtime_context", lambda *_args: {})
    monkeypatch.setattr(
        app,
        "_readonly_auth_probe",
        lambda *_args, **_kwargs: {
            "status": "PASSED",
            "summary": "ok",
            "items": [{"http_status": 200, "business_code": 200}],
        },
    )

    result = app._salary_trade_account_pool_preflight(
        {"base_url": "https://example.test"},
        package_root,
        [_case()],
        required_applicants=1,
        require_proxy=False,
    )

    assert result["status"] == "PASSED"
    assert result["summary"]["required_applicants"] == 1
    assert result["summary"]["required_roles"] == ["applicant"]
    assert result["summary"]["proxies_total"] == 0
    assert result["summary"]["missing_proxy_currencies"] == []


def test_salary_trade_performance_pool_redacts_external_csv_location(monkeypatch, tmp_path):
    applicant_path = Path("D:/private/applicants.csv")
    proxy_path = Path("D:/private/proxies.csv")
    monkeypatch.setattr(
        app,
        "_role_csv_path",
        lambda _root, role, _fallback: applicant_path if role == "applicant" else proxy_path,
    )
    monkeypatch.setattr(
        app,
        "_csv_rows_for_path",
        lambda path: [{"uid": "1001", "ticket": "ticket-1", "currency": "USD"}] if path == applicant_path else [],
    )

    pool = app._salary_trade_performance_account_pool(
        {"base_url": "https://example.test"},
        tmp_path / "requirements" / "salary-trade",
        [_case()],
        threads=1,
    )

    assert pool["rows"][0]["applicant_source"] == "external_csv:applicant:applicants.csv"
    assert "D:/private" not in str(pool["allocations"])


def test_jmeter_performance_diagnosis_classifies_network_errors(tmp_path):
    jtl = tmp_path / "result.jtl"
    jtl.write_text(
        "timeStamp,elapsed,label,responseCode,responseMessage,success,failureMessage\n"
        "1000,200,read,200,OK,true,\n"
        "1200,10000,read,Non HTTP response code: org.apache.http.conn.ConnectTimeoutException,Connect timed out,false,\n"
        "1400,30000,read,Non HTTP response code: java.net.SocketTimeoutException,Read timed out,false,\n",
        encoding="utf-8",
    )

    summary = app._summarize_jmeter_jtl(jtl)
    gate = app._performance_gate(summary, {"max_error_rate": 100, "max_p95_ms": 60000, "max_p99_ms": 60000})
    diagnosis = app._performance_diagnosis(summary, gate)

    categories = {item["category"]: item["count"] for item in summary["error_categories"]}
    assert categories == {"connect_timeout": 1, "read_timeout": 1}
    assert "少量失败采样" in diagnosis["conclusion"]


def test_redact_runtime_file_removes_ticket_value(tmp_path):
    report = tmp_path / "result.jtl"
    report.write_text("URL\nhttps://example.test/read?uid=1001&ticket=secret-ticket\n", encoding="utf-8")

    changed = app._redact_runtime_file(report, {"uid": "1001", "ticket": "secret-ticket"})

    assert changed is True
    text = report.read_text(encoding="utf-8")
    assert "secret-ticket" not in text
    assert "ticket=***REDACTED***" in text


def test_redact_runtime_file_removes_entire_jwt_after_existing_redaction_marker(tmp_path):
    report = tmp_path / "result.jtl"
    report.write_text(
        "url=https://example.test/read?ticket=***REDACTED***sInR5cCI6IkpXVCJ9.eyJ1aWQiOjEwMDF9.signature&uid=1001\n",
        encoding="utf-8",
    )

    changed = app._redact_runtime_file(report, {})

    assert changed is True
    text = report.read_text(encoding="utf-8")
    assert text == "url=https://example.test/read?ticket=***REDACTED***&uid=1001\n"


def test_redact_runtime_text_removes_jwt_even_when_csv_shifted_it_to_wrong_field():
    token = "eyJhbGciOiJIUzI1NiJ9.eyJ1aWQiOjEwMDEsImV4cCI6OTk5OTk5OTk5OX0.signature123"

    redacted = app._redact_runtime_text(f"channel={token}&uid=1001", {})

    assert token not in redacted
    assert redacted == "channel=***REDACTED***&uid=1001"


def test_runtime_environment_injection_keeps_import_only_workflow(monkeypatch, tmp_path):
    source_jmx = tmp_path / "plans" / "test.jmx"
    source_jmx.parent.mkdir(parents=True)
    source_jmx.write_text(
        app.build_jmeter_jmx(
            {"name": "test", "base_url": "https://example.test"},
            [_case("/api/health")],
            {},
            True,
            {"_jmeter_non_gui_plan": True},
        ),
        encoding="utf-8",
    )
    workflow = tmp_path / "workflow.json"
    workflow.write_text(
        '{"schema_version":"2.0","source_jmx":"' + str(source_jmx).replace('\\', '/') + '","metadata":{"preflight_status":"PASS"}}',
        encoding="utf-8",
    )
    captured = {}

    def fake_bridge(runtime_workflow, _output_dir, timeout_seconds=1800, env=None):
        captured.update(app._read_json_asset(runtime_workflow))
        captured["runtime_jmx_text"] = Path(captured["source_jmx"]).read_text(encoding="utf-8")
        captured["runtime_rows"] = json.loads(
            base64.b64decode(env["AUTOTEST_JMETER_RUNTIME_ROWS_B64"]).decode("utf-8")
        )
        return {"status": "PASSED", "exit_code": 0, "duration_ms": 1, "stdout": "", "stderr": ""}

    monkeypatch.setattr(app, "_run_jmeter_mcp_bridge", fake_bridge)

    app._execute_jmeter_mcp_workflow(
        workflow,
        tmp_path / "report",
        {"uid": "1001", "ticket": "runtime-only"},
    )

    assert captured["source_jmx"].endswith("runtime-plan.jmx")
    assert "variables" not in captured
    assert "root_csv_data_sets" not in captured
    assert '<CSVDataSet' not in captured["runtime_jmx_text"]
    assert "AUTOTEST_JMETER_RUNTIME_ROWS_B64" in captured["runtime_jmx_text"]
    assert "runtime-only" not in captured["runtime_jmx_text"]
    assert captured["runtime_rows"] == [{"uid": "1001", "ticket": "runtime-only"}]


def test_account_pool_and_runtime_use_process_scoped_environment_rows(monkeypatch, tmp_path):
    source_jmx = tmp_path / "plans" / "test.jmx"
    source_jmx.parent.mkdir(parents=True)
    source_jmx.write_text(
        app.build_jmeter_jmx(
            {"name": "test", "base_url": "https://example.test"},
            [_case("/api/read?uid={{uid}}&ticket={{ticket}}")],
            {},
            True,
            {
                "_jmeter_non_gui_plan": True,
                "_jmeter_performance_profile": "baseline",
                "_jmeter_transaction_name": "read-flow",
                "_jmeter_account_columns": ["applicant_uid", "applicant_ticket"],
            },
        ),
        encoding="utf-8",
    )
    workflow = tmp_path / "workflow.json"
    workflow.write_text(
        '{"schema_version":"2.0","source_jmx":"' + str(source_jmx).replace('\\', '/') + '","metadata":{"preflight_status":"PASS"}}',
        encoding="utf-8",
    )
    captured = {}

    def fake_bridge(runtime_workflow, output_dir, timeout_seconds=1800, env=None):
        payload = app._read_json_asset(runtime_workflow)
        runtime_jmx = Path(payload["source_jmx"])
        text = runtime_jmx.read_text(encoding="utf-8")
        root = app.ET.fromstring(text)
        data_sets = list(root.iter("CSVDataSet"))
        captured["count"] = len(data_sets)
        captured["jmx"] = text
        captured["runtime_rows"] = json.loads(
            base64.b64decode(env["AUTOTEST_JMETER_RUNTIME_ROWS_B64"]).decode("utf-8")
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "result.jtl").write_text(
            "timeStamp,elapsed,label,responseCode,responseMessage,success,failureMessage\n"
            "1000,20,read,200,https://example.test/read?ticket=account-secret&uid=1001,true,\n",
            encoding="utf-8",
        )
        return {"status": "PASSED", "exit_code": 0, "duration_ms": 1, "stdout": "", "stderr": ""}

    monkeypatch.setattr(app, "_run_jmeter_mcp_bridge", fake_bridge)

    result = app._execute_jmeter_mcp_workflow(
        workflow,
        tmp_path / "report",
        {"appVersion": "100.1", "supportCurrencies": "SAR,USD"},
        runtime_rows=[{"applicant_uid": "1001", "applicant_ticket": "account-secret"}],
    )

    assert captured["count"] == 0
    assert "account-secret" not in captured["jmx"]
    assert captured["runtime_rows"] == [{
        "appVersion": "100.1",
        "supportCurrencies": "SAR,USD",
        "applicant_uid": "1001",
        "applicant_ticket": "account-secret",
    }]
    assert "account-secret" not in Path(result["jtl_path"]).read_text(encoding="utf-8")


def test_wealth_performance_entry_uses_mcp_and_updates_requirement_run(monkeypatch, tmp_path):
    package_root = tmp_path / "requirements" / "wealth-level"
    package_root.mkdir(parents=True)
    monkeypatch.setattr(app, "REQUIREMENT_PACKAGE_ROOT", tmp_path / "requirements")
    monkeypatch.setattr(app, "row", lambda *_: {"id": "project-1", "name": "Demo", "base_url": "https://example.test"})
    monkeypatch.setattr(
        app,
        "requirement_package_by_id",
        lambda *_: {"package_id": "wealth-level", "name": "财富等级", "root": str(package_root)},
    )
    monkeypatch.setattr(
        app,
        "_ensure_requirement_run_context",
        lambda *_args, **_kwargs: {"run_id": "run-mcp-1", "run_context_path": "runs/run-mcp-1/run-context.json"},
    )
    generated = {}

    def fake_write_asset(**kwargs):
        generated.update(kwargs)
        kwargs["workflow_path"].write_text('{"schema_version":"1.0"}', encoding="utf-8")
        kwargs["target_path"].write_text("<jmeterTestPlan/>", encoding="utf-8")
        return {"jmx_path": str(kwargs["target_path"]), "engine": app.JMETER_MCP_ENGINE}

    def fake_execute(_workflow_path, output_dir, _runtime_context, **_kwargs):
        output_dir.mkdir(parents=True, exist_ok=True)
        jtl = output_dir / "result.jtl"
        jtl.write_text(
            "timeStamp,elapsed,label,responseCode,responseMessage,success,failureMessage\n"
            "1000,40,wealth,200,OK,true,\n"
            "1100,50,wealth,200,OK,true,\n",
            encoding="utf-8",
        )
        html = output_dir / "jmeter-html" / "index.html"
        html.parent.mkdir(parents=True)
        html.write_text("ok", encoding="utf-8")
        analysis = output_dir / "analysis.json"
        analysis.write_text("{}", encoding="utf-8")
        return {
            "status": "PASSED",
            "exit_code": 0,
            "duration_ms": 100,
            "stdout": "",
            "stderr": "",
            "jtl_path": str(jtl),
            "html_path": str(html),
            "analysis_path": str(analysis),
        }

    updated = {}
    monkeypatch.setattr(app, "_write_jmeter_mcp_asset", fake_write_asset)
    monkeypatch.setattr(app, "_execute_jmeter_mcp_workflow", fake_execute)
    monkeypatch.setattr(app, "update_requirement_run_context", lambda *args: updated.update({"args": args}))

    result = app.run_jmeter_wealth("project-1", "secret-ticket", 1455001, 2, 3, 1, _case("/level/exeperience/v2/get"))

    assert result["status"] == "PASSED"
    assert result["engine"] == app.JMETER_MCP_ENGINE
    assert result["execution_mode"] == "mcp_non_gui"
    assert result["requests"] == 2
    assert result["success"] == 2
    assert generated.get("source_jmx") is None
    assert generated["threads"] == 2
    assert generated["loops"] == 3
    assert updated["args"][3:5] == ("jmeter", "PASSED")
