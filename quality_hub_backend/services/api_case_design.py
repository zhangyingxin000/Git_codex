from __future__ import annotations

import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as xml_escape


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}
MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
AUTH_NAMES = {"authorization", "ticket", "token", "access_token", "cookie"}
TECHNICAL_PARAMETER_NAMES = {
    "devicetype", "systemlanguage", "appversion", "os", "nettype", "channel",
    "appsflyerid", "language", "appcode", "deviceid", "version", "osversion",
    "isvpnconnected", "appid", "model", "packagename", "isptype", "organic",
}


def _resolve(schema: Any, spec: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(schema, dict):
        return {}
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/"):
        value: Any = spec
        for part in ref[2:].split("/"):
            value = value.get(part.replace("~1", "/").replace("~0", "~"), {}) if isinstance(value, dict) else {}
        return _resolve(value, spec)
    merged: dict[str, Any] = {}
    for part in schema.get("allOf") or []:
        merged.update(_resolve(part, spec))
    merged.update({key: value for key, value in schema.items() if key != "allOf"})
    return merged


def _sample(schema: dict[str, Any]) -> Any:
    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]
    enum = schema.get("enum") or []
    if enum:
        return enum[0]
    kind = schema.get("type")
    if kind == "integer":
        return int(schema.get("minimum", 1))
    if kind == "number":
        return float(schema.get("minimum", 1))
    if kind == "boolean":
        return True
    if kind == "array":
        return [_sample(schema.get("items") or {})]
    if kind == "object":
        required = set(schema.get("required") or [])
        return {
            name: _sample(child)
            for name, child in (schema.get("properties") or {}).items()
            if name in required
        }
    return {
        "email": "test@example.com",
        "uuid": "00000000-0000-4000-8000-000000000001",
        "date": "2026-09-04",
        "date-time": "2026-09-04T12:00:00Z",
    }.get(str(schema.get("format") or ""), "valid-value")


def _field(location: str, name: str, schema: dict[str, Any], required: bool) -> dict[str, Any]:
    return {
        "location": location,
        "name": name,
        "field": f"{location}.{name}",
        "required": required,
        "schema": schema,
        "sample": _sample(schema),
    }


def _body_fields(schema: dict[str, Any], spec: dict[str, Any], prefix: str = "", inherited_required: bool = False) -> list[dict[str, Any]]:
    schema = _resolve(schema, spec)
    if schema.get("type") != "object" and not schema.get("properties"):
        return [_field("body", prefix or "$", schema, inherited_required)]
    required = set(schema.get("required") or [])
    result = []
    for name, raw_child in (schema.get("properties") or {}).items():
        child = _resolve(raw_child, spec)
        full_name = f"{prefix}.{name}" if prefix else name
        # A required request body does not make every property required. Only
        # the object's own required list (or a required parent object) does.
        is_required = inherited_required or name in required
        result.append(_field("body", full_name, child, is_required))
        if child.get("type") == "object" or child.get("properties"):
            result.extend(_body_fields(child, spec, full_name, is_required))
    return result


def _operation_fields(path_item: dict[str, Any], operation: dict[str, Any], spec: dict[str, Any]) -> list[dict[str, Any]]:
    fields = []
    for parameter in (path_item.get("parameters") or []) + (operation.get("parameters") or []):
        parameter = _resolve(parameter, spec)
        name = str(parameter.get("name") or "").strip()
        if not name:
            continue
        location = str(parameter.get("in") or "query")
        schema = _resolve(parameter.get("schema") or {}, spec)
        if "example" in parameter and "example" not in schema:
            schema["example"] = parameter["example"]
        fields.append(_field(location, name, schema, bool(parameter.get("required"))))
    request_body = _resolve(operation.get("requestBody") or {}, spec)
    for content_type, media in (request_body.get("content") or {}).items():
        media = media if isinstance(media, dict) else {}
        schema = _resolve(media.get("schema") or {}, spec)
        body_fields = _body_fields(schema, spec)
        for item in body_fields:
            item["content_type"] = content_type
        fields.extend(body_fields)
        break
    unique = {}
    for item in fields:
        unique[item["field"]] = item
    return list(unique.values())


def _wrong_value(kind: str) -> Any:
    return {
        "integer": "not-an-integer",
        "number": "not-a-number",
        "boolean": "not-a-boolean",
        "array": {"unexpected": "object"},
        "object": ["unexpected-array"],
    }.get(kind, 123456)


def _security_candidate(field: dict[str, Any]) -> bool:
    name = str(field.get("name") or "").split(".")[-1].lower()
    if name in AUTH_NAMES or name in TECHNICAL_PARAMETER_NAMES:
        return False
    if field.get("location") == "body":
        return True
    business_tokens = (
        "id", "name", "no", "remark", "reason", "keyword", "search", "code",
        "email", "phone", "address", "country", "currency", "content", "title",
    )
    return any(token in name for token in business_tokens)


def _number_boundaries(schema: dict[str, Any]) -> list[tuple[str, Any, str]]:
    values = []
    is_integer = schema.get("type") == "integer"
    step = 1 if is_integer else 0.01
    for key, label in (("minimum", "min"), ("maximum", "max")):
        if key not in schema:
            continue
        base = float(schema[key])
        candidates = [(f"{label}-1", base - step, "invalid"), (label, base, "valid"), (f"{label}+1", base + step, "valid")]
        if key == "maximum":
            candidates = [(f"{label}-1", base - step, "valid"), (label, base, "valid"), (f"{label}+1", base + step, "invalid")]
        for name, value, partition in candidates:
            values.append((name, int(value) if is_integer else round(value, 6), partition))
    return values


def _length_boundaries(schema: dict[str, Any]) -> list[tuple[str, Any, str]]:
    values = []
    for key, label in (("minLength", "minLength"), ("maxLength", "maxLength")):
        if key not in schema:
            continue
        base = max(0, int(schema[key]))
        candidates = [(f"{label}-1", max(0, base - 1), "invalid"), (label, base, "valid"), (f"{label}+1", base + 1, "valid")]
        if key == "maxLength":
            candidates = [(f"{label}-1", max(0, base - 1), "valid"), (label, base, "valid"), (f"{label}+1", base + 1, "invalid")]
        for name, length, partition in candidates:
            values.append((name, "a" * length, partition))
    return values


def _collection_boundaries(schema: dict[str, Any]) -> list[tuple[str, Any, str]]:
    if schema.get("type") != "array":
        return []
    item = _sample(schema.get("items") or {})
    values = []
    for key, label in (("minItems", "minItems"), ("maxItems", "maxItems")):
        if key not in schema:
            continue
        base = max(0, int(schema[key]))
        candidates = [(f"{label}-1", max(0, base - 1), "invalid"), (label, base, "valid"), (f"{label}+1", base + 1, "valid")]
        if key == "maxItems":
            candidates = [(f"{label}-1", max(0, base - 1), "valid"), (label, base, "valid"), (f"{label}+1", base + 1, "invalid")]
        values.extend((name, [item for _ in range(size)], partition) for name, size, partition in candidates)
    return values


def _invalid_format_value(format_name: str) -> str:
    return {
        "email": "not-an-email",
        "uuid": "not-a-uuid",
        "date": "2026-99-99",
        "date-time": "not-a-date-time",
        "uri": "not a uri",
        "hostname": "invalid_host name",
        "ipv4": "999.999.999.999",
        "ipv6": "not-an-ipv6",
    }.get(format_name, "__invalid_format__")


def _case(
    case_id: str,
    operation: dict[str, Any],
    dimension: str,
    technique: str,
    partition: str,
    title: str,
    expected: str,
    mutation: dict[str, Any] | None = None,
    tool: str = "Newman",
    automation_status: str = "READY",
    priority: str = "P1",
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "operation_id": operation["operation_id"],
        "interface": operation["summary"],
        "method": operation["method"],
        "path": operation["path"],
        "dimension": dimension,
        "design_technique": technique,
        "equivalence_partition": partition,
        "title": title,
        "priority": priority,
        "preconditions": ["测试环境可用", "准备接口所需身份与公共参数", "确认测试数据可恢复或只读"],
        "steps": ["按请求变异规则准备数据", f"发送 {operation['method']} {operation['path']}", "检查HTTP状态、业务码、响应Schema和业务数据"],
        "request_mutation": mutation or {"action": "use_valid_baseline"},
        "expected_result": expected,
        "recommended_tool": tool,
        "automation_status": automation_status,
        "security_policy": "ISOLATED_TEST_ENVIRONMENT_ONLY" if dimension == "安全" else "STANDARD_TEST_ENVIRONMENT",
    }


def generate_api_case_design(spec: dict[str, Any], package_id: str = "") -> dict[str, Any]:
    operations = []
    cases = []
    sequence = 0

    def add(operation: dict[str, Any], *args: Any, **kwargs: Any) -> None:
        nonlocal sequence
        sequence += 1
        cases.append(_case(f"API-{sequence:05d}", operation, *args, **kwargs))

    for path, raw_item in (spec.get("paths") or {}).items():
        if not isinstance(raw_item, dict):
            continue
        for method, raw_operation in raw_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(raw_operation, dict):
                continue
            operation = {
                "operation_id": raw_operation.get("operationId") or f"{method.lower()}_{re.sub(r'[^a-zA-Z0-9]+', '_', path).strip('_')}",
                "summary": raw_operation.get("summary") or f"{method.upper()} {path}",
                "method": method.upper(),
                "path": path,
                "security": bool(raw_operation.get("security") or spec.get("security")),
            }
            request_body = _resolve(raw_operation.get("requestBody") or {}, spec)
            content_types = list((request_body.get("content") or {}).keys())
            operation["request_body_required"] = bool(request_body.get("required"))
            operation["content_types"] = content_types
            fields = _operation_fields(raw_item, raw_operation, spec)
            operation["fields"] = fields
            operations.append(operation)
            add(operation, "功能", "等价类划分", "valid", f"{operation['summary']}：有效等价类正常请求", "返回成功状态，响应Schema及核心业务结果正确。", priority="P0")
            add(operation, "响应契约", "契约校验", "valid", f"{operation['summary']}：响应状态与Schema契约", "HTTP状态、业务码、必填响应字段、字段类型和枚举均符合OpenAPI契约，不泄露未声明敏感字段。", {"action": "validate_response_contract"}, priority="P0")
            add(operation, "异常处理", "错误推测", "invalid", f"{operation['summary']}：使用不支持的HTTP方法", "返回405或明确的业务拒绝，不执行原接口业务写入。", {"action": "use_unsupported_http_method"})

            if operation["request_body_required"]:
                add(operation, "参数校验", "等价类划分", "invalid", f"{operation['summary']}：缺失整个请求体", "返回400或422，不产生500和任何部分业务写入。", {"action": "remove_request_body"}, priority="P0")
            if content_types:
                add(operation, "参数校验", "错误推测", "invalid", f"{operation['summary']}：Content-Type与请求体不匹配", "返回415、400或明确的参数错误，不按错误媒体类型解析和写入数据。", {"action": "replace_content_type", "declared": content_types, "value": "text/plain"})

            for field in fields:
                schema = field["schema"]
                field_name = field["field"]
                kind = str(schema.get("type") or "string")
                if field["required"]:
                    add(operation, "参数校验", "等价类划分", "invalid", f"{operation['summary']}：缺失必填字段 {field_name}", "接口明确拒绝请求，不产生错误业务数据。", {"action": "remove", "field": field_name}, priority="P0")
                if schema.get("nullable") is True:
                    add(operation, "等价类", "等价类划分", "valid", f"{operation['summary']}：{field_name} null有效等价类", "接口接受Schema声明可为空的字段，返回结果符合业务规则。", {"action": "replace", "field": field_name, "value": None})
                elif field["required"]:
                    add(operation, "参数校验", "等价类划分", "invalid", f"{operation['summary']}：{field_name} 非法null", "接口拒绝必填且不可为空字段的null值，不产生500或脏数据。", {"action": "replace", "field": field_name, "value": None})
                if kind in {"string", "array", "object"}:
                    add(operation, "边界值", "边界值分析", "invalid" if field["required"] else "boundary", f"{operation['summary']}：{field_name} 空值边界", "接口按Schema和业务规则接受或明确拒绝，不能产生500。", {"action": "replace", "field": field_name, "value": "" if kind == "string" else [] if kind == "array" else {}})
                add(operation, "参数校验", "等价类划分", "invalid", f"{operation['summary']}：{field_name} 类型错误", "接口返回参数错误，不产生500和业务脏数据。", {"action": "replace", "field": field_name, "value": _wrong_value(kind), "expected_type": kind})

                enum = schema.get("enum") or []
                for enum_value in enum:
                    add(operation, "等价类", "等价类划分", "valid", f"{operation['summary']}：{field_name} 枚举有效值 {enum_value}", "接口接受Schema声明的枚举值并返回正确业务结果。", {"action": "replace", "field": field_name, "value": enum_value})
                if enum:
                    add(operation, "等价类", "等价类划分", "invalid", f"{operation['summary']}：{field_name} 枚举外无效值", "接口拒绝未声明枚举值，不能静默写入无效状态。", {"action": "replace", "field": field_name, "value": "__invalid_enum__"})

                for boundary_name, value, partition in _number_boundaries(schema) + _length_boundaries(schema) + _collection_boundaries(schema):
                    add(operation, "边界值", "边界值分析", partition, f"{operation['summary']}：{field_name} {boundary_name}", "边界归属符合Schema；越界值被拒绝且不产生500。", {"action": "replace", "field": field_name, "value": value, "boundary": boundary_name})

                if schema.get("pattern"):
                    add(operation, "参数校验", "等价类划分", "invalid", f"{operation['summary']}：{field_name} 不符合正则格式", "接口拒绝不符合pattern的输入。", {"action": "replace", "field": field_name, "value": "__pattern_mismatch__", "pattern": schema["pattern"]})
                if schema.get("format"):
                    format_name = str(schema["format"])
                    add(operation, "参数校验", "等价类划分", "invalid", f"{operation['summary']}：{field_name} {format_name}格式错误", "接口拒绝不符合Schema format的输入，不产生500或错误持久化。", {"action": "replace", "field": field_name, "value": _invalid_format_value(format_name), "format": format_name})

                if kind == "string" and _security_candidate(field):
                    add(operation, "安全", "攻击输入", "invalid", f"{operation['summary']}：{field_name} SQL注入字符", "接口不执行注入语义，不泄露数据库错误，不绕过鉴权或条件。", {"action": "replace", "field": field_name, "value": "' OR '1'='1' --"}, tool="pytest", automation_status="REVIEW_REQUIRED", priority="P0")
                    add(operation, "安全", "攻击输入", "invalid", f"{operation['summary']}：{field_name} XSS脚本字符", "响应和持久化数据不得执行脚本，输出应安全编码。", {"action": "replace", "field": field_name, "value": "<script>alert(1)</script>"}, tool="pytest", automation_status="REVIEW_REQUIRED")

            auth_fields = [item for item in fields if item["name"].lower() in AUTH_NAMES or item["location"] == "header" and item["name"].lower() == "authorization"]
            if operation["security"] or auth_fields:
                add(operation, "认证授权", "等价类划分", "invalid", f"{operation['summary']}：缺失认证凭证", "返回401或403，不返回受保护业务数据。", {"action": "remove_auth"}, priority="P0")
                add(operation, "认证授权", "等价类划分", "invalid", f"{operation['summary']}：无效或伪造认证凭证", "返回401或403，不泄露凭证校验细节。", {"action": "replace_auth", "value": "invalid-token"}, priority="P0")

            if operation["method"] in MUTATION_METHODS:
                add(operation, "可靠性", "错误推测", "duplicate", f"{operation['summary']}：重复提交与幂等性", "重复请求不产生重复扣款、重复订单或重复状态流转。", {"action": "repeat_same_request", "times": 2}, tool="pytest", automation_status="REVIEW_REQUIRED", priority="P0")
                add(operation, "并发", "并发场景法", "concurrent", f"{operation['summary']}：同一业务数据并发提交", "并发请求满足唯一性、锁和状态机约束，最终数据一致。", {"action": "concurrent_same_request", "users": 5}, tool="JMeter", automation_status="REVIEW_REQUIRED", priority="P0")

            if any("json" in key.lower() for key in (request_body.get("content") or {})):
                add(operation, "异常处理", "错误推测", "invalid", f"{operation['summary']}：JSON格式损坏", "返回400或422，不产生500和部分写入。", {"action": "malformed_json", "value": "{invalid-json"})

    dimension_counts = dict(Counter(case["dimension"] for case in cases))
    tool_counts = dict(Counter(case["recommended_tool"] for case in cases))
    return {
        "schema_version": "1.0",
        "report_type": "SCHEMA_DRIVEN_API_TEST_CASE_DESIGN",
        "package_id": package_id,
        "summary": {
            "interfaces": len(operations),
            "cases": len(cases),
            "dimensions": dimension_counts,
            "tools": tool_counts,
            "review_required": sum(case["automation_status"] == "REVIEW_REQUIRED" for case in cases),
        },
        "coverage_dimensions": [
            "功能", "响应契约", "参数校验", "等价类", "边界值", "认证授权", "异常处理", "可靠性", "并发", "安全"
        ],
        "operations": operations,
        "cases": cases,
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# Schema驱动接口测试用例",
        "",
        f"- 接口数：{summary['interfaces']}",
        f"- 用例数：{summary['cases']}",
        f"- 需要人工确认后执行：{summary['review_required']}",
        f"- 测试维度：{', '.join(payload['coverage_dimensions'])}",
        "",
        "| 用例ID | 接口 | 方法 | 路径 | 测试维度 | 设计方法 | 等价类 | 用例标题 | 请求变异 | 预期结果 | 工具 | 自动化状态 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in payload["cases"]:
        mutation = json.dumps(case["request_mutation"], ensure_ascii=False)
        cells = [
            case["case_id"], case["interface"], case["method"], f"`{case['path']}`",
            case["dimension"], case["design_technique"], case["equivalence_partition"],
            case["title"], mutation, case["expected_result"], case["recommended_tool"],
            case["automation_status"],
        ]
        lines.append("| " + " | ".join(str(value).replace("|", "\\|").replace("\n", " ") for value in cells) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _excel_col(number: int) -> str:
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def write_xlsx(payload: dict[str, Any], path: Path) -> None:
    headers = ["用例ID", "接口", "方法", "路径", "测试维度", "设计方法", "等价类", "优先级", "用例标题", "前置条件", "步骤", "请求变异", "预期结果", "推荐工具", "自动化状态", "安全策略"]
    rows = [headers]
    for case in payload["cases"]:
        rows.append([
            case["case_id"], case["interface"], case["method"], case["path"], case["dimension"],
            case["design_technique"], case["equivalence_partition"], case["priority"], case["title"],
            "\n".join(case["preconditions"]), "\n".join(case["steps"]),
            json.dumps(case["request_mutation"], ensure_ascii=False), case["expected_result"],
            case["recommended_tool"], case["automation_status"], case["security_policy"],
        ])
    sheet_rows = []
    for row_index, values in enumerate(rows, 1):
        cells = []
        for column_index, value in enumerate(values, 1):
            reference = f"{_excel_col(column_index)}{row_index}"
            cells.append(f'<c r="{reference}" t="inlineStr"><is><t>{xml_escape(str(value))}</t></is></c>')
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    worksheet = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{''.join(sheet_rows)}</sheetData></worksheet>'''
    workbook = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="接口测试用例" sheetId="1" r:id="rId1"/></sheets></workbook>'''
    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'''
    workbook_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'''
    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'''
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)


def write_case_design(payload: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "api-test-cases.json"
    markdown_path = output_dir / "api-test-cases.md"
    xlsx_path = output_dir / "api-test-cases.xlsx"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(payload, markdown_path)
    write_xlsx(payload, xlsx_path)
    return {"json": str(json_path), "markdown": str(markdown_path), "xlsx": str(xlsx_path)}
