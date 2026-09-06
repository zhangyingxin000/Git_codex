from pathlib import Path
import re

from quality_hub_backend.services.api_case_design import (
    generate_api_case_design,
    write_case_design,
)


SPEC = {
    "openapi": "3.0.0",
    "paths": {
        "/orders": {
            "post": {
                "summary": "创建订单",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {
                        "name": "pageSize",
                        "in": "query",
                        "required": True,
                        "schema": {"type": "integer", "minimum": 1, "maximum": 100},
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["currency", "remark"],
                                "properties": {
                                    "currency": {"type": "string", "enum": ["USD", "EGP"]},
                                    "remark": {"type": "string", "minLength": 1, "maxLength": 20},
                                    "callbackEmail": {"type": "string", "format": "email"},
                                    "tags": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 3},
                                },
                            }
                        }
                    },
                },
            }
        }
    },
}


def test_schema_generator_covers_equivalence_boundaries_security_and_concurrency() -> None:
    payload = generate_api_case_design(SPEC, "orders")
    titles = [case["title"] for case in payload["cases"]]

    assert payload["summary"]["interfaces"] == 1
    assert any("pageSize min-1" in title for title in titles)
    assert any("pageSize max+1" in title for title in titles)
    assert any("currency 枚举有效值 USD" in title for title in titles)
    assert any("currency 枚举外无效值" in title for title in titles)
    assert any("remark SQL注入字符" in title for title in titles)
    assert any("缺失认证凭证" in title for title in titles)
    assert any("重复提交与幂等性" in title for title in titles)
    assert any("同一资源并发请求" in title for title in titles)
    assert any("缺失整个请求体" in title for title in titles)
    assert any("Content-Type与请求体不匹配" in title for title in titles)
    assert any("使用不支持的HTTP方法" in title for title in titles)
    assert any("响应状态与Schema契约" in title for title in titles)
    assert any("callbackEmail email格式错误" in title for title in titles)
    assert any("tags minItems-1" in title for title in titles)
    assert not any("缺失必填字段 body.callbackEmail" in title for title in titles)
    assert not any("缺失必填字段 body.tags" in title for title in titles)
    assert payload["schema_version"] == "2.0"
    assert payload["quality_gate"]["status"] == "PASS"
    assert payload["summary"]["coverage_weights"] == {"normal": 40.0, "exception": 40.0, "boundary": 20.0}
    assert payload["execution_order"]
    assert all(re.fullmatch(r"TC_[A-Z0-9_]+_\d{3}_(normal|exception|boundary)", case["case_id"]) for case in payload["cases"])


def test_v2_contract_infers_string_boundaries_and_covers_mandatory_exceptions() -> None:
    payload = generate_api_case_design(SPEC, "orders")
    cases = payload["cases"]
    actions = {case["request_mutation"]["action"] for case in cases}

    assert {
        "empty_request", "type_confusion", "oversized_payload", "sql_injection",
        "xss_injection", "unicode_null", "path_traversal", "oversized_id",
        "repeat_same_request", "concurrent_same_request", "timeout_simulation",
    } <= actions
    inferred = [case for case in cases if case["inferred"]]
    assert any("callbackEmail minLength-1" in case["title"] for case in inferred)
    assert any("callbackEmail maxLength+1" in case["title"] for case in inferred)
    assert all(case["need_review"] for case in inferred)
    assert all({"status", "protocol", "schema", "business_logic", "performance"} <= set(case["assertions"]) for case in cases)
    assert all(case["cleanup"]["action"] != "none" for case in cases if case["method"] in {"POST", "PUT", "PATCH", "DELETE"})
    assert sum("exploratory" in case["tags"] for case in cases) == int(len(cases) * 0.2)


def test_schema_generator_writes_reviewable_outputs(tmp_path: Path) -> None:
    payload = generate_api_case_design(SPEC, "orders")
    paths = write_case_design(payload, tmp_path)

    assert Path(paths["json"]).is_file()
    markdown = Path(paths["markdown"]).read_text(encoding="utf-8")
    assert markdown.startswith("# Schema驱动接口测试用例 v2.0")
    assert "质量门禁：PASS" in markdown
    assert Path(paths["xlsx"]).read_bytes().startswith(b"PK")
