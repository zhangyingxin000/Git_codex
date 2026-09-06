from quality_hub_backend.services.performance_preflight import (
    apply_resolved_inputs,
    build_target_readiness,
    normalize_account_pool,
    public_account_pool,
    summarize_missing_runtime_inputs,
)


def test_missing_runtime_inputs_flatten_body_fields_and_mark_credentials():
    result = summarize_missing_runtime_inputs({
        "targets": [
            {
                "key": "POST /orders",
                "missing": [{
                    "name": "request_body",
                    "location": "body",
                    "reason": "缺少请求体字段",
                    "missing_fields": ["receiveAccountType", "userRemark"],
                }],
            },
            {
                "key": "GET /orders",
                "missing": [{
                    "name": "ticket",
                    "location": "query",
                    "reason": "缺少凭证来源",
                }],
            },
        ]
    })

    assert [item["name"] for item in result] == [
        "receiveAccountType",
        "userRemark",
        "ticket",
    ]
    assert result[0]["fillable"] is True
    assert result[0]["targets"] == ["POST /orders"]
    assert result[2]["sensitive"] is True
    assert result[2]["fillable"] is False


def test_target_readiness_blocks_only_targets_with_missing_required_data():
    cases = [
        {
            "title": "查询订单",
            "method": "GET",
            "path": "/api/orders?uid={{applicant_uid}}&ticket={{applicant_ticket}}",
        },
        {
            "title": "创建订单",
            "method": "POST",
            "path": "/api/orders",
            "payload": "",
        },
    ]
    openapi = {
        "paths": {
            "/api/orders": {
                "get": {
                    "parameters": [
                        {"name": "uid", "in": "query", "required": True},
                        {"name": "ticket", "in": "query", "required": True},
                    ]
                },
                "post": {"requestBody": {"required": True, "content": {"application/json": {}}}},
            }
        }
    }

    result = build_target_readiness(
        cases,
        csv_columns=["applicant_uid", "applicant_ticket"],
        openapi_documents=[openapi],
    )

    assert result["status"] == "READY_WITH_WARNINGS"
    assert result["summary"] == {"targets": 2, "ready": 1, "blocked": 1}
    assert result["targets"][0]["status"] == "READY"
    assert result["targets"][1]["missing"] == [
        {"name": "request_body", "location": "body", "reason": "OpenAPI声明请求体必填"}
    ]


def test_target_readiness_uses_only_safe_openapi_pagination_defaults_and_applies_them():
    cases = [{"title": "查询代理", "method": "GET", "path": "/api/agents"}]
    openapi = {
        "paths": {
            "/api/agents": {
                "get": {
                    "parameters": [
                        {"name": "pageNum", "in": "query", "required": True, "example": "1"},
                        {"name": "pageSize", "in": "query", "required": True, "example": "20"},
                        {"name": "unionId", "in": "query", "required": True, "example": "invented-user"},
                    ]
                }
            }
        }
    }

    blocked = build_target_readiness(cases, openapi_documents=[openapi])
    assert blocked["targets"][0]["status"] == "BLOCKED"
    assert [item["name"] for item in blocked["targets"][0]["missing"]] == ["unionId"]

    ready = build_target_readiness(
        cases,
        runtime_values={"unionId": "union-1001"},
        openapi_documents=[openapi],
    )
    target = ready["targets"][0]
    assert target["status"] == "READY"
    assert target["resolved_inputs"] == {
        "pageNum": "1",
        "pageSize": "20",
        "unionId": "{{unionId}}",
    }
    assert target["input_sources"]["pageNum"]["type"] == "openapi_safe_default"
    assert target["input_sources"]["unionId"]["type"] == "runtime"
    resolved = apply_resolved_inputs(cases, ready)
    assert resolved[0]["path"] == "/api/agents?pageNum=1&pageSize=20&unionId={{unionId}}"


def test_requirement_endpoint_contract_fills_openapi_gaps_from_declared_sources():
    cases = [{"title": "查询入口", "method": "GET", "path": "/union/entry"}]
    contracts = [{
        "method": "GET",
        "path": "/union/entry",
        "required_inputs": [
            {"name": "uid", "location": "query"},
            {"name": "ticket", "location": "query"},
            {"name": "appCode", "location": "query"},
        ],
    }]

    blocked = build_target_readiness(
        cases,
        csv_columns=["uid", "ticket"],
        endpoint_input_contracts=contracts,
    )
    assert blocked["targets"][0]["status"] == "BLOCKED"
    assert blocked["targets"][0]["missing"] == [{
        "name": "appCode",
        "location": "query",
        "reason": "需求包接口输入契约声明必填但当前数据源未提供",
    }]

    ready = build_target_readiness(
        cases,
        csv_columns=["uid", "ticket"],
        runtime_values={"appCode": "100156"},
        endpoint_input_contracts=contracts,
    )
    target = ready["targets"][0]
    assert target["status"] == "READY"
    assert target["openapi_matched"] is False
    assert target["resolved_path"] == (
        "/union/entry?uid={{uid}}&ticket={{ticket}}&appCode={{appCode}}"
    )
    assert all(
        item["declared_by"] == "requirement_resource_manifest"
        for item in target["required_inputs"]
    )


def test_declared_extraction_is_available_only_after_its_structured_producer():
    create = {"title": "创建订单", "method": "POST", "path": "/api/orders", "payload": {"amount": 100}}
    detail = {"title": "订单详情", "method": "GET", "path": "/api/orders/detail"}
    openapi = {
        "paths": {
            "/api/orders/detail": {
                "get": {
                    "parameters": [
                        {"name": "orderNo", "in": "query", "required": True, "example": "{{orderNo}}"}
                    ]
                }
            }
        }
    }
    rules = [{
        "variable": "salary_order_no",
        "source_method": "POST",
        "source_path": "/api/orders",
        "json_paths": ["$.data.orderNo"],
    }]

    without_producer = build_target_readiness(
        [detail],
        extraction_rules=rules,
        openapi_documents=[openapi],
    )
    assert without_producer["targets"][0]["status"] == "BLOCKED"

    with_producer = build_target_readiness(
        [create, detail],
        extraction_rules=rules,
        openapi_documents=[openapi],
    )
    target = with_producer["targets"][1]
    assert target["status"] == "READY"
    assert target["resolved_inputs"]["orderNo"] == "${salary_order_no}"
    assert target["input_sources"]["orderNo"]["type"] == "prior_extraction"
    assert with_producer["produced_variables"][0]["source_path"] == "/api/orders"


def test_existing_query_placeholder_is_not_treated_as_ready_without_a_source():
    cases = [{"title": "详情", "method": "GET", "path": "/api/detail?orderNo={{orderNo}}"}]
    openapi = {
        "paths": {
            "/api/detail": {
                "get": {
                    "parameters": [
                        {"name": "orderNo", "in": "query", "required": True}
                    ]
                }
            }
        }
    }

    result = build_target_readiness(cases, openapi_documents=[openapi])

    assert result["targets"][0]["status"] == "BLOCKED"
    reasons = [item["reason"] for item in result["targets"][0]["missing"]]
    assert any("来源" in reason for reason in reasons)


def test_required_content_type_is_resolved_but_required_form_body_stays_blocked():
    cases = [{
        "title": "创建订单",
        "method": "POST",
        "path": "/api/orders",
        "headers": "{}",
        "payload": "",
    }]
    openapi = {
        "paths": {
            "/api/orders": {
                "post": {
                    "parameters": [{
                        "name": "Content-Type",
                        "in": "header",
                        "required": True,
                        "example": "application/x-www-form-urlencoded",
                    }],
                    "requestBody": {
                        "content": {
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "type": "object",
                                    "required": ["uid", "ticket", "amount"],
                                }
                            }
                        }
                    },
                }
            }
        }
    }

    result = build_target_readiness(cases, openapi_documents=[openapi])

    target = result["targets"][0]
    assert target["status"] == "BLOCKED"
    assert target["resolved_headers"] == {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    assert target["input_sources"]["Content-Type"]["type"] == "openapi_safe_header"
    assert target["missing"] == [{
        "name": "request_body",
        "location": "body",
        "reason": "OpenAPI请求体缺少必填字段：uid、ticket、amount",
        "required_fields": ["uid", "ticket", "amount"],
        "missing_fields": ["uid", "ticket", "amount"],
        "content_type": "application/x-www-form-urlencoded",
    }]


def test_safe_required_header_is_applied_to_ready_case_without_overwriting_existing_headers():
    cases = [{
        "title": "创建订单",
        "method": "POST",
        "path": "/api/orders",
        "headers": '{"X-Request-Source":"quality-hub"}',
        "payload": "uid={{uid}}&ticket={{ticket}}&amount=50",
    }]
    openapi = {
        "paths": {
            "/api/orders": {
                "post": {
                    "parameters": [{
                        "name": "Content-Type",
                        "in": "header",
                        "required": True,
                        "example": "application/x-www-form-urlencoded",
                    }],
                    "requestBody": {
                        "content": {
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "type": "object",
                                    "required": ["uid", "ticket", "amount"],
                                }
                            }
                        }
                    },
                }
            }
        }
    }

    readiness = build_target_readiness(
        cases,
        runtime_values={"uid": "1001", "ticket": "secret"},
        openapi_documents=[openapi],
    )
    resolved = apply_resolved_inputs(cases, readiness)

    assert readiness["targets"][0]["status"] == "READY"
    assert resolved[0]["headers"] == (
        '{"X-Request-Source": "quality-hub", '
        '"Content-Type": "application/x-www-form-urlencoded"}'
    )


def test_required_form_body_is_built_only_from_registered_sources():
    cases = [{
        "title": "创建订单",
        "method": "POST",
        "path": "/api/orders",
        "headers": "{}",
        "payload": "",
    }]
    openapi = {
        "paths": {
            "/api/orders": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "type": "object",
                                    "required": [
                                        "uid",
                                        "ticket",
                                        "receiveCurrency",
                                        "receiveAccount",
                                    ],
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    readiness = build_target_readiness(
        cases,
        csv_columns=["uid", "ticket", "currency", "bankAccount"],
        openapi_documents=[openapi],
    )
    target = readiness["targets"][0]
    resolved = apply_resolved_inputs(cases, readiness)

    assert target["status"] == "READY"
    assert target["resolved_body"] == {
        "uid": "{{uid}}",
        "ticket": "{{ticket}}",
        "receiveCurrency": "{{currency}}",
        "receiveAccount": "{{bankAccount}}",
    }
    assert resolved[0]["payload"] == (
        "uid={{uid}}&ticket={{ticket}}&receiveCurrency={{currency}}"
        "&receiveAccount={{bankAccount}}"
    )


def test_required_form_body_reports_only_fields_without_registered_sources():
    cases = [{
        "title": "创建订单",
        "method": "POST",
        "path": "/api/orders",
        "payload": "",
    }]
    openapi = {
        "paths": {
            "/api/orders": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "type": "object",
                                    "required": ["uid", "ticket", "businessRemark"],
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    readiness = build_target_readiness(
        cases,
        csv_columns=["uid", "ticket"],
        openapi_documents=[openapi],
    )

    target = readiness["targets"][0]
    assert target["status"] == "BLOCKED"
    assert target["resolved_body"] == {
        "uid": "{{uid}}",
        "ticket": "{{ticket}}",
    }
    assert target["missing"][0]["missing_fields"] == ["businessRemark"]


def test_openapi_response_contract_is_attached_to_ready_case():
    cases = [{
        "title": "订单详情",
        "method": "GET",
        "path": "/api/orders/detail",
        "expected_status": 200,
    }]
    openapi = {
        "paths": {
            "/api/orders/detail": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["code", "data", "message"],
                                        "properties": {
                                            "code": {"type": "integer", "example": 200},
                                            "data": {"type": "object", "minProperties": 1},
                                            "message": {"type": "string"},
                                        },
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    readiness = build_target_readiness(cases, openapi_documents=[openapi])
    resolved = apply_resolved_inputs(cases, readiness)

    contract = readiness["targets"][0]["response_contract"]
    assert contract["required_fields"] == ["code", "data", "message"]
    assert contract["field_types"] == {
        "code": "integer",
        "data": "object",
        "message": "string",
    }
    assert contract["non_empty_fields"] == ["data"]
    assert contract["success_codes"] == [200]
    assert resolved[0]["_performance_response_contract"] == contract


def test_account_pool_matches_proxy_by_support_currencies_and_rotates_candidates():
    applicants = [
        {"applicant_uid": "1001", "applicant_ticket": "a-1", "country_code": "EG", "currency": "EGP", "account_source": "requirements/demo/applicants.csv"},
        {"applicant_uid": "1002", "applicant_ticket": "a-2", "country_code": "EG", "currency": "EGP"},
        {"applicant_uid": "1003", "applicant_ticket": "a-3", "country_code": "US", "currency": "USD"},
    ]
    proxies = [
        {"proxy_uid": "2001", "proxy_ticket": "p-1", "country_code": "SA", "support_currencies": "EGP,USD", "account_source": "requirements/demo/proxies.csv"},
        {"proxy_uid": "2002", "proxy_ticket": "p-2", "country_code": "OA", "support_currencies": "EGP"},
    ]

    pool = normalize_account_pool(applicants, proxies, threads=3, reuse_policy="round_robin")

    assert pool["status"] == "READY"
    assert [row["proxy_uid"] for row in pool["rows"]] == ["2001", "2002", "2001"]
    assert pool["rows"][0]["country_code"] == "EG"
    assert pool["rows"][0]["currency"] == "EGP"
    assert pool["rows"][0]["applicant_source"] == "requirements/demo/applicants.csv"
    assert pool["rows"][0]["proxy_source"] == "requirements/demo/proxies.csv"
    public = public_account_pool(pool)
    assert "rows" not in public
    assert "a-1" not in str(public)
    assert "p-1" not in str(public)
    assert public["allocations"][0]["applicant_source"] == "requirements/demo/applicants.csv"
    assert public["allocations"][0]["proxy_source"] == "requirements/demo/proxies.csv"


def test_account_pool_strict_unique_blocks_when_accounts_are_insufficient():
    pool = normalize_account_pool(
        [{"uid": "1001", "ticket": "ticket-1", "currency": "USD"}],
        [],
        threads=2,
        reuse_policy="strict_unique",
    )

    assert pool["status"] == "BLOCKED"
    assert "需要2个账号" in pool["message"]


def test_account_pool_allows_proxy_reference_without_proxy_ticket():
    pool = normalize_account_pool(
        [{"uid": "1001", "ticket": "applicant-ticket", "currency": "USD"}],
        [{"proxy_uid": "2001", "support_currencies": "USD"}],
        threads=1,
        reuse_policy="strict_unique",
        require_proxy_ticket=False,
    )

    assert pool["status"] == "READY"
    assert pool["rows"][0]["proxy_uid"] == "2001"
    assert pool["rows"][0]["proxy_ticket"] == ""


def test_account_pool_derives_bank_type_and_resolves_applicant_remark_alias():
    pool = normalize_account_pool(
        [{
            "uid": "1001",
            "ticket": "applicant-ticket",
            "bankAccount": "TEST-ACCOUNT-001",
            "bankName": "Test Bank",
            "remark": "applicant order remark",
        }],
        [],
        threads=1,
    )
    readiness = build_target_readiness(
        [{"title": "创建订单", "method": "POST", "path": "/api/orders", "payload": ""}],
        csv_columns=pool["columns"],
        openapi_documents=[{
            "paths": {
                "/api/orders": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/x-www-form-urlencoded": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["receiveAccountType", "userRemark"],
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }],
    )

    assert pool["rows"][0]["receiveAccountType"] == "bank"
    assert pool["rows"][0]["userRemark"] == "applicant order remark"
    assert readiness["targets"][0]["status"] == "READY"
    assert readiness["targets"][0]["resolved_body"] == {
        "receiveAccountType": "{{receiveAccountType}}",
        "userRemark": "{{userRemark}}",
    }
