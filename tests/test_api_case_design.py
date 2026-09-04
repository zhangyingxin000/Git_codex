from pathlib import Path

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
    assert any("同一业务数据并发提交" in title for title in titles)
    assert any("缺失整个请求体" in title for title in titles)
    assert any("Content-Type与请求体不匹配" in title for title in titles)
    assert any("使用不支持的HTTP方法" in title for title in titles)
    assert any("响应状态与Schema契约" in title for title in titles)
    assert any("callbackEmail email格式错误" in title for title in titles)
    assert any("tags minItems-1" in title for title in titles)
    assert not any("缺失必填字段 body.callbackEmail" in title for title in titles)
    assert not any("缺失必填字段 body.tags" in title for title in titles)


def test_schema_generator_writes_reviewable_outputs(tmp_path: Path) -> None:
    payload = generate_api_case_design(SPEC, "orders")
    paths = write_case_design(payload, tmp_path)

    assert Path(paths["json"]).is_file()
    assert Path(paths["markdown"]).read_text(encoding="utf-8").startswith("# Schema驱动接口测试用例")
    assert Path(paths["xlsx"]).read_bytes().startswith(b"PK")
