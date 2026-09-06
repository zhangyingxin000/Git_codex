from quality_hub_backend.services.regression_selection import infer_change_scope, select_regression_cases


STRUCTURED = {
    "cases": [
        {
            "id": "case-create",
            "title": "申请人创建订单",
            "requirement_ref": "REQ-ORDER",
            "priority": "P0",
            "method": "POST",
            "path": "/orders",
            "db_checks": [{"table": "trade_order"}],
            "traceability": {"evidence_rules": ["order-created"]},
        },
        {
            "id": "case-detail",
            "title": "查询订单详情",
            "requirement_ref": "REQ-ORDER",
            "priority": "P1",
            "method": "GET",
            "path": "/orders/{id}",
            "db_checks": [{"table": "trade_order"}],
            "traceability": {"evidence_rules": ["order-created"]},
        },
        {
            "id": "case-wealth",
            "title": "查询财富等级",
            "requirement_ref": "REQ-WEALTH",
            "priority": "P2",
            "method": "GET",
            "path": "/wealth/level",
            "lifecycle_status": "DEPRECATED",
        },
    ]
}


def test_regression_selector_blocks_without_change_scope() -> None:
    result = select_regression_cases(STRUCTURED, {})
    assert result["status"] == "BLOCKED"
    assert result["summary"]["selected"] == 0


def test_regression_selector_selects_direct_related_and_critical_cases() -> None:
    result = select_regression_cases(STRUCTURED, {"changed_endpoints": ["/orders/{id}"]})
    selected = {item["case_id"]: item for item in result["selected_cases"]}

    assert result["status"] == "READY"
    assert selected["case-detail"]["selection_type"] == "DIRECT"
    assert selected["case-create"]["selection_type"] == "RELATED"
    assert "case-wealth" not in selected


def test_regression_selector_matches_database_change() -> None:
    result = select_regression_cases(STRUCTURED, {"changed_tables": ["trade_order"], "include_related": False, "include_critical": False})
    assert {item["case_id"] for item in result["selected_cases"]} == {"case-create", "case-detail"}


def test_regression_selector_defaults_to_active_lifecycle() -> None:
    default_result = select_regression_cases(STRUCTURED, {"keywords": ["财富"]})
    included_result = select_regression_cases(STRUCTURED, {"keywords": ["财富"], "lifecycle_statuses": ["ACTIVE", "DEPRECATED"], "include_critical": False})

    assert default_result["summary"]["selected"] == 1  # P0 protection only; deprecated direct match is excluded.
    assert {item["case_id"] for item in included_result["selected_cases"]} == {"case-wealth"}
    assert included_result["selected_cases"][0]["lifecycle_status"] == "DEPRECATED"


def test_change_scope_inference_compares_openapi_requirement_and_metadata() -> None:
    baseline_openapi = {"paths": {"/orders": {"get": {"responses": {"200": {}}}}}}
    current_openapi = {
        "paths": {
            "/orders": {"get": {"responses": {"200": {}, "404": {}}}},
            "/orders/{id}": {"delete": {"responses": {"204": {}}}},
        }
    }

    result = infer_change_scope({
        "baseline_openapi": baseline_openapi,
        "current_openapi": current_openapi,
        "baseline_requirement": "REQ-ORDER 查询订单",
        "current_requirement": "REQ-ORDER 查询订单\nREQ-CANCEL 取消订单",
        "baseline_db_metadata": {"tables": ["trade_order"]},
        "current_db_metadata": {"tables": ["trade_order", "trade_refund"]},
        "baseline_redis_metadata": {"keys": ["order:{id}"]},
        "current_redis_metadata": {"keys": ["order:{id}", "refund:{id}"]},
    })

    assert result["has_changes"] is True
    assert set(result["change_scope"]["endpoints"]) == {"DELETE /orders/{id}", "GET /orders"}
    assert "req-cancel" in result["change_scope"]["requirements"]
    assert result["change_scope"]["tables"] == ["trade_refund"]
    assert result["change_scope"]["redis_keys"] == ["refund:{id}"]


def test_first_openapi_version_uses_full_interface_scope_with_warning() -> None:
    result = infer_change_scope({"current_openapi": {"paths": {"/health": {"get": {}}}}})

    assert result["change_scope"]["endpoints"] == ["GET /health"]
    assert any("首次" in warning for warning in result["warnings"])
