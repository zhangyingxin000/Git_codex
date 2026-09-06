import json
from pathlib import Path

from quality_hub_backend.services.api_case_design import generate_api_case_design
from quality_hub_backend.services.api_case_execution import (
    compile_api_cases_to_postman,
    write_api_execution_assets,
)


SPEC = {
    "openapi": "3.0.0",
    "paths": {
        "/orders/{orderId}": {
            "post": {
                "summary": "更新订单",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {"name": "orderId", "in": "path", "required": True, "example": "1001", "schema": {"type": "string"}},
                    {"name": "ticket", "in": "query", "required": True, "example": "{{ticket}}", "schema": {"type": "string"}},
                    {"name": "pageSize", "in": "query", "required": True, "example": 10, "schema": {"type": "integer", "minimum": 1}},
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["remark"],
                                "properties": {"remark": {"type": "string", "minLength": 1}},
                            }
                        }
                    },
                },
            }
        }
    },
}


def _flat_items(collection):
    return [item for folder in collection["item"] for item in folder.get("item", [])]


def test_compile_api_cases_builds_traceable_newman_collection() -> None:
    design = generate_api_case_design(SPEC, "orders")
    design["package_name"] = "订单"
    compiled = compile_api_cases_to_postman(design, "https://test.example.com")
    items = _flat_items(compiled["collection"])

    assert compiled["summary"]["compiled_newman_cases"] > 0
    assert compiled["summary"]["skipped_cases"] > 0
    assert compiled["collection"]["variable"][0]["value"] == "https://test.example.com"
    assert all(item["name"].startswith("[TC_ORDERS_") for item in items)
    assert all(item.get("x-autotest-case", {}).get("case_id") for item in items)
    assert all(item.get("event") for item in items)
    assert compiled["summary"]["required_runtime_variables"] == ["ticket"]
    assert compiled["collection"].get("event")


def test_compile_api_cases_applies_query_auth_body_and_method_mutations() -> None:
    design = generate_api_case_design(SPEC, "orders")
    compiled = compile_api_cases_to_postman(design)
    items = _flat_items(compiled["collection"])

    missing_page_size = next(item for item in items if "缺失必填字段 query.pageSize" in item["name"])
    assert "pageSize=" not in missing_page_size["request"]["url"]

    missing_auth = next(item for item in items if "缺失认证凭证" in item["name"])
    assert "ticket=" not in missing_auth["request"]["url"]

    missing_body = next(item for item in items if "缺失整个请求体" in item["name"])
    assert "body" not in missing_body["request"]

    wrong_method = next(item for item in items if "使用不支持的HTTP方法" in item["name"])
    assert wrong_method["request"]["method"] == "GET"


def test_write_api_execution_assets(tmp_path: Path) -> None:
    design = generate_api_case_design(SPEC, "orders")
    compiled = compile_api_cases_to_postman(design)
    paths = write_api_execution_assets(compiled, tmp_path)

    collection = json.loads(Path(paths["collection"]).read_text(encoding="utf-8"))
    manifest = json.loads(Path(paths["manifest"]).read_text(encoding="utf-8"))
    assert collection["info"]["schema"].endswith("collection.json")
    assert manifest["mapping"]
    assert manifest["collection_path"] == paths["collection"]
