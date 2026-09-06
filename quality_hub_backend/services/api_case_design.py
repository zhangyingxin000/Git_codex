from __future__ import annotations

import json
import math
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
SCENARIO_WEIGHTS = {"normal": 40.0, "exception": 40.0, "boundary": 20.0}
PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)")
BUILTIN_VARIABLES = {
    "random_int", "random_phone", "random_uuid", "now_iso", "timestamp",
    "random_string", "random_email", "random_enum", "random_date", "random_boolean",
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


def _sample(schema: dict[str, Any], field_name: str = "") -> Any:
    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]
    enum = schema.get("enum") or []
    if enum:
        return enum[0]
    normalized_name = re.sub(r"[^a-z0-9]", "", field_name.lower())
    if "phone" in normalized_name or "mobile" in normalized_name:
        return "{{random_phone}}"
    if "email" in normalized_name:
        return "{{random_email}}"
    if "uuid" in normalized_name:
        return "{{random_uuid}}"
    if any(token in normalized_name for token in ("time", "createdat", "updatedat")):
        return "{{now_iso}}"
    if any(token in normalized_name for token in ("amount", "price", "fee", "total")):
        return 199.99
    kind = schema.get("type")
    if kind == "integer":
        return int(schema.get("minimum", 1))
    if kind == "number":
        return float(schema.get("minimum", 1))
    if kind == "boolean":
        return True
    if kind == "array":
        return [_sample(schema.get("items") or {}, field_name)]
    if kind == "object":
        required = set(schema.get("required") or [])
        return {
            name: _sample(child, name)
            for name, child in (schema.get("properties") or {}).items()
            if name in required
        }
    return {
        "email": "test@example.com",
        "uuid": "00000000-0000-4000-8000-000000000001",
        "date": "2026-09-04",
        "date-time": "2026-09-04T12:00:00Z",
    }.get(str(schema.get("format") or ""), "接口测试 Test data，正常值。")


def _field(location: str, name: str, schema: dict[str, Any], required: bool) -> dict[str, Any]:
    return {
        "location": location,
        "name": name,
        "field": f"{location}.{name}",
        "required": required,
        "schema": schema,
        "sample": _sample(schema, name),
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


def _effective_schema(schema: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    result = dict(schema)
    inferred = False
    if str(result.get("type") or "string") == "string" and not result.get("enum"):
        if "minLength" not in result:
            result["minLength"] = 1
            inferred = True
        if "maxLength" not in result:
            result["maxLength"] = 255
            inferred = True
    return result, inferred


def _date_boundaries(schema: dict[str, Any]) -> list[tuple[str, Any, str]]:
    format_name = str(schema.get("format") or "")
    if format_name == "date":
        return [("Unix纪元边界", "1970-01-01", "valid"), ("2038时间边界", "2038-01-19", "valid")]
    if format_name == "date-time":
        return [("Unix纪元边界", "1970-01-01T00:00:00Z", "valid"), ("2038时间边界", "2038-01-19T03:14:07Z", "valid")]
    return []


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


def _module_code(package_id: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", package_id or "API").strip("_").upper()
    return value[:32] or "API"


def _scenario_type(dimension: str, partition: str) -> str:
    if dimension == "边界值":
        return "boundary"
    if partition == "valid" and dimension not in {"安全", "异常处理", "认证授权", "并发", "可靠性"}:
        return "normal"
    return "exception"


def _variable_name(field: dict[str, Any]) -> str:
    raw = f"{field.get('location', 'query')}_{field.get('name', 'value')}"
    return re.sub(r"[^A-Za-z0-9_]+", "_", raw).strip("_") or "value"


def _set_nested(target: dict[str, Any], dotted: str, value: Any) -> None:
    parts = [part for part in dotted.split(".") if part and part != "$"]
    if not parts:
        return
    current = target
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            child = {}
            current[part] = child
        current = child
    current[parts[-1]] = value


def _standard_context_payload(operation: dict[str, Any], mutation: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    variables: dict[str, Any] = {}
    payload: dict[str, Any] = {"path": {}, "query": {}, "headers": {}, "body": {}, "mutation": mutation}
    for field in operation.get("fields") or []:
        variable = _variable_name(field)
        variables[variable] = field.get("sample")
        location = str(field.get("location") or "query")
        name = str(field.get("name") or "")
        value = "{{" + variable + "}}"
        if location == "body":
            _set_nested(payload["body"], name, value)
        elif location == "header":
            payload["headers"][name] = value
        elif location in {"query", "path"}:
            payload[location][name] = value
    dependencies = []
    if operation.get("security"):
        dependencies.append({
            "id": "DEP_AUTH",
            "description": "获取接口授权凭证",
            "source": "AUTH_PROVIDER",
            "extract": "$.data.token",
            "store_as": "{{auth_token}}",
            "on_fail": "skip_all",
            "inferred": True,
            "need_review": True,
        })
        variables.setdefault("auth_token", "{{runtime_auth_token}}")
    return {"dependencies": dependencies, "variables": variables}, payload


def _priority_label(priority: str) -> str:
    return {"P0": "critical", "P1": "high", "P2": "medium", "P3": "low"}.get(priority, "high")


def _case_tags(dimension: str, scenario: str, priority: str, tool: str) -> list[str]:
    tags = ["regression", scenario]
    if scenario == "normal" and priority == "P0":
        tags.append("smoke")
    if priority == "P0":
        tags.append("critical")
    if dimension == "安全":
        tags.append("security")
    if dimension in {"并发", "可靠性"} or tool == "JMeter":
        tags.append("performance")
    return list(dict.fromkeys(tags))


def _cleanup(operation: dict[str, Any]) -> dict[str, Any]:
    if operation["method"] not in MUTATION_METHODS:
        return {"action": "none", "on_fail": "ignore", "retry": 0, "timeout": 5000}
    return {
        "action": "NEEDS_CONFIGURATION",
        "on_fail": "mark",
        "retry": 3,
        "timeout": 5000,
        "fallback": {"mark_as": "AUTO_TEST_{{timestamp}}", "notify": True},
        "inferred": True,
        "need_review": True,
        "suggestion": "请绑定删除接口、回滚接口或测试数据定期清理任务",
    }


def _expected_status(operation: dict[str, Any], scenario: str, mutation: dict[str, Any]) -> int:
    if scenario == "normal":
        return int(operation.get("success_status") or 200)
    action = str(mutation.get("action") or "")
    if action in {"remove_auth", "replace_auth"}:
        return 401
    if action == "replace_content_type":
        return 415
    if action == "use_unsupported_http_method":
        return 405
    if action == "oversized_payload":
        return 413
    if action == "timeout_simulation":
        return 504
    return 400


def _success_response(operation: dict[str, Any], spec: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    responses = operation.get("responses") or {}
    for status, response in responses.items():
        if str(status).isdigit() and 200 <= int(status) < 300:
            response = _resolve(response, spec)
            for media in (response.get("content") or {}).values():
                if isinstance(media, dict):
                    return int(status), _resolve(media.get("schema") or {}, spec)
            return int(status), {"type": "object"}
    return 200, {"type": "object"}


def _first_field(operation: dict[str, Any], *, kind: str = "", security: bool = False) -> dict[str, Any] | None:
    fields = operation.get("fields") or []
    for field in fields:
        schema = field.get("schema") or {}
        if kind and str(schema.get("type") or "string") != kind:
            continue
        if security and not _security_candidate(field):
            continue
        return field
    return fields[0] if fields and not kind and not security else None


def _distribute_coverage_weights(cases: list[dict[str, Any]]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for scenario, target in SCENARIO_WEIGHTS.items():
        group = [case for case in cases if case.get("meta", {}).get("scenario_type") == scenario]
        if not group:
            totals[scenario] = 0.0
            continue
        share = round(target / len(group), 8)
        assigned = 0.0
        for case in group[:-1]:
            case["meta"]["coverage_weight"] = share
            assigned += share
        group[-1]["meta"]["coverage_weight"] = round(target - assigned, 8)
        totals[scenario] = round(sum(float(case["meta"]["coverage_weight"]) for case in group), 8)
    return totals


def _placeholder_names(value: Any) -> set[str]:
    return set(PLACEHOLDER_PATTERN.findall(json.dumps(value, ensure_ascii=False)))


def _quality_gate(cases: list[dict[str, Any]], weights: dict[str, float]) -> dict[str, Any]:
    exception_actions = {
        str((case.get("request_mutation") or {}).get("action") or "")
        for case in cases
        if case.get("meta", {}).get("scenario_type") == "exception"
    }
    unresolved = []
    for case in cases:
        defined = set((case.get("context") or {}).get("variables") or {}) | BUILTIN_VARIABLES
        used = _placeholder_names({
            "payload": case.get("payload"),
            "assertions": case.get("assertions"),
            "cleanup": case.get("cleanup"),
        })
        missing = sorted(used - defined)
        if missing:
            unresolved.append({"case_id": case.get("case_id"), "variables": missing})
    write_cases = [case for case in cases if case.get("method") in MUTATION_METHODS]
    cleanup_complete = all(str((case.get("cleanup") or {}).get("action") or "") not in {"", "none"} for case in write_cases)
    assertion_depth = all(
        bool((case.get("assertions") or {}).get("protocol"))
        and bool((case.get("assertions") or {}).get("schema"))
        and bool((case.get("assertions") or {}).get("business_logic"))
        for case in cases
    )
    checks = {
        "coverage_40_40_20": all(abs(weights.get(name, 0.0) - target) < 0.000001 for name, target in SCENARIO_WEIGHTS.items()),
        "exception_types_at_least_5": len(exception_actions) >= 5,
        "assertion_layers_at_least_3": assertion_depth,
        "write_cleanup_complete": cleanup_complete,
        "dependency_variables_complete": not unresolved,
        "performance_assertion_rate_at_least_50": (
            sum(bool((case.get("assertions") or {}).get("performance")) for case in cases) / max(1, len(cases)) >= 0.5
        ),
    }
    return {
        "status": "PASS" if all(checks.values()) else "REVIEW_REQUIRED",
        "checks": checks,
        "unresolved_variables": unresolved,
        "thresholds": {"pass_rate": 95, "critical_pass_rate": 100, "security_pass_rate": 100},
    }


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
    inferred: bool = False,
    need_review: bool = False,
) -> dict[str, Any]:
    mutation = mutation or {"action": "use_valid_baseline"}
    scenario = _scenario_type(dimension, partition)
    context, payload = _standard_context_payload(operation, mutation)
    amount_fields = [
        field for field in operation.get("fields") or []
        if any(token in str(field.get("name") or "").lower() for token in ("amount", "price", "fee", "total"))
    ]
    business_logic = [expected]
    if amount_fields:
        business_logic.append("所有金额保留两位小数；存在子项时 total == sum(items.amount)")
    response_schema = operation.get("response_schema") or {"type": "object"}
    aggregate_review = need_review or inferred or automation_status != "READY" or bool(context["dependencies"])
    standard = {
        "case_id": case_id,
        "description": title,
        "priority": _priority_label(priority),
        "tags": _case_tags(dimension, scenario, priority, tool),
        "meta": {
            "protocol": operation.get("protocol", "rest"),
            "method": operation["method"],
            "endpoint": operation["path"],
            "scenario_type": scenario,
            "coverage_weight": 0,
            "inferred": inferred,
            "need_review": aggregate_review,
        },
        "context": context,
        "payload": payload,
        "assertions": {
            "status": _expected_status(operation, scenario, mutation),
            "protocol": {
                "status": _expected_status(operation, scenario, mutation),
                "headers": ["Content-Type"] + (["X-Request-Id"] if operation.get("request_id_header") else []),
                "version": operation.get("protocol_version") or "HTTP/1.1_or_HTTP/2",
            },
            "schema": response_schema,
            "business_logic": business_logic,
            "db_check": operation.get("sql_check"),
            "cache_check": operation.get("cache_check"),
            "message_check": operation.get("message_check"),
            "performance": {"max_response_ms": int(operation.get("max_response_ms") or 500)},
        },
        "cleanup": _cleanup(operation),
        "inferred": inferred,
        "need_review": aggregate_review,
        "suggestion": "请核对推断约束和运行数据" if aggregate_review else "",
    }
    standard.update({
        "operation_id": operation["operation_id"],
        "interface": operation["summary"],
        "method": operation["method"],
        "path": operation["path"],
        "dimension": dimension,
        "design_technique": technique,
        "equivalence_partition": partition,
        "title": title,
        "legacy_priority": priority,
        "preconditions": ["测试环境可用", "准备接口所需身份与公共参数", "确认测试数据可恢复或只读"],
        "steps": ["按请求变异规则准备数据", f"发送 {operation['method']} {operation['path']}", "检查HTTP状态、业务码、响应Schema和业务数据"],
        "request_mutation": mutation,
        "expected_result": expected,
        "recommended_tool": tool,
        "automation_status": automation_status,
        "security_policy": "ISOLATED_TEST_ENVIRONMENT_ONLY" if dimension == "安全" else "STANDARD_TEST_ENVIRONMENT",
    })
    if operation.get("deprecated"):
        standard["tags"] = list(dict.fromkeys(standard["tags"] + ["deprecated"]))
    return standard


def generate_api_case_design(spec: dict[str, Any], package_id: str = "") -> dict[str, Any]:
    operations = []
    cases = []
    sequence = 0

    def add(operation: dict[str, Any], *args: Any, **kwargs: Any) -> None:
        nonlocal sequence
        sequence += 1
        dimension = str(args[0]) if args else str(kwargs.get("dimension") or "功能")
        partition = str(args[2]) if len(args) > 2 else str(kwargs.get("partition") or "valid")
        scenario = _scenario_type(dimension, partition)
        volume = (sequence - 1) // 999 + 1
        local_sequence = (sequence - 1) % 999 + 1
        module = _module_code(package_id)
        if volume > 1:
            module = f"{module}_{volume}"
        case_id = f"TC_{module}_{local_sequence:03d}_{scenario}"
        cases.append(_case(case_id, operation, *args, **kwargs))

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
                "protocol": "rest",
                "deprecated": bool(raw_operation.get("deprecated")),
                "responses": raw_operation.get("responses") or {},
                "sql_check": raw_operation.get("x-sql-check"),
                "cache_check": raw_operation.get("x-cache-check"),
                "message_check": raw_operation.get("x-message-check"),
                "max_response_ms": raw_operation.get("x-max-response-ms") or 500,
                "callbacks": raw_operation.get("callbacks") or raw_operation.get("x-callbacks") or {},
            }
            success_status, response_schema = _success_response(raw_operation, spec)
            operation["success_status"] = success_status
            operation["response_schema"] = response_schema
            response_headers = {
                str(name).lower()
                for response in (raw_operation.get("responses") or {}).values()
                if isinstance(response, dict)
                for name in (response.get("headers") or {})
            }
            operation["request_id_header"] = "x-request-id" in response_headers
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
                schema, inferred_constraints = _effective_schema(field["schema"])
                field["schema"] = schema
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

                for boundary_name, value, partition in _number_boundaries(schema) + _length_boundaries(schema) + _collection_boundaries(schema) + _date_boundaries(schema):
                    add(operation, "边界值", "边界值分析", partition, f"{operation['summary']}：{field_name} {boundary_name}", "边界归属符合Schema；越界值被拒绝且不产生500。", {"action": "replace", "field": field_name, "value": value, "boundary": boundary_name}, inferred=inferred_constraints, need_review=inferred_constraints)

                if kind == "boolean":
                    for boolean_value in (True, False):
                        add(operation, "等价类", "等价类划分", "valid", f"{operation['summary']}：{field_name} 布尔值 {str(boolean_value).lower()}", "接口接受Schema声明的布尔值并按业务语义处理。", {"action": "replace", "field": field_name, "value": boolean_value})

                if schema.get("pattern"):
                    add(operation, "参数校验", "等价类划分", "invalid", f"{operation['summary']}：{field_name} 不符合正则格式", "接口拒绝不符合pattern的输入。", {"action": "replace", "field": field_name, "value": "__pattern_mismatch__", "pattern": schema["pattern"]})
                if schema.get("format"):
                    format_name = str(schema["format"])
                    add(operation, "参数校验", "等价类划分", "invalid", f"{operation['summary']}：{field_name} {format_name}格式错误", "接口拒绝不符合Schema format的输入，不产生500或错误持久化。", {"action": "replace", "field": field_name, "value": _invalid_format_value(format_name), "format": format_name})

                if kind == "string" and _security_candidate(field):
                    add(operation, "安全", "攻击输入", "invalid", f"{operation['summary']}：{field_name} SQL注入字符", "接口不执行注入语义，不泄露数据库错误，不绕过鉴权或条件。", {"action": "replace", "field": field_name, "value": "' OR '1'='1' --"}, tool="pytest", automation_status="REVIEW_REQUIRED", priority="P0")
                    add(operation, "安全", "攻击输入", "invalid", f"{operation['summary']}：{field_name} XSS脚本字符", "响应和持久化数据不得执行脚本，输出应安全编码。", {"action": "replace", "field": field_name, "value": "<script>alert(1)</script>"}, tool="pytest", automation_status="REVIEW_REQUIRED")

            probe = _first_field(operation, security=True) or _first_field(operation)
            probe_field = str((probe or {}).get("field") or "body.__probe")
            type_probe = _first_field(operation)
            type_field = str((type_probe or {}).get("field") or "body.__type_probe")
            type_kind = str(((type_probe or {}).get("schema") or {}).get("type") or "string")
            id_probe = next(
                (field for field in fields if "id" in str(field.get("name") or "").lower()),
                probe,
            )
            id_field = str((id_probe or {}).get("field") or "query.id")

            add(operation, "异常处理", "错误推测", "invalid", f"{operation['summary']}：空请求或空参数", "返回400或明确的参数缺失错误，不产生500和部分业务写入。", {"action": "empty_request"}, priority="P0")
            add(operation, "参数校验", "错误推测", "invalid", f"{operation['summary']}：通用类型混淆", "字符串、数字或布尔类型混淆时应返回明确参数错误。", {"action": "type_confusion", "field": type_field, "value": _wrong_value(type_kind), "expected_type": type_kind}, priority="P0")
            add(operation, "边界值", "错误推测", "invalid", f"{operation['summary']}：单字段1MB超大Payload", "返回413、明确拒绝或受控截断，不进入正常业务写入。", {"action": "oversized_payload", "field": probe_field, "size_bytes": 1024 * 1024}, tool="pytest", automation_status="REVIEW_REQUIRED", need_review=True)
            add(operation, "安全", "攻击输入", "invalid", f"{operation['summary']}：通用SQL注入检测", "输入被安全转义或拒绝，不返回额外数据和数据库错误。", {"action": "sql_injection", "field": probe_field, "value": "' OR '1'='1"}, tool="pytest", automation_status="REVIEW_REQUIRED", priority="P0")
            add(operation, "安全", "攻击输入", "invalid", f"{operation['summary']}：通用XSS检测", "脚本内容被转义或拒绝，不在响应或后续页面执行。", {"action": "xss_injection", "field": probe_field, "value": "<script>alert(1)</script>"}, tool="pytest", automation_status="REVIEW_REQUIRED")
            add(operation, "安全", "攻击输入", "invalid", f"{operation['summary']}：Unicode空字符攻击", "返回400或明确拒绝，不截断后绕过校验。", {"action": "unicode_null", "field": probe_field, "value": "prefix\u0000suffix"}, tool="pytest", automation_status="REVIEW_REQUIRED")
            add(operation, "安全", "攻击输入", "invalid", f"{operation['summary']}：路径遍历尝试", "返回403、400或明确拒绝，不读取测试范围外文件。", {"action": "path_traversal", "field": probe_field, "value": "../../../../etc/passwd"}, tool="pytest", automation_status="REVIEW_REQUIRED", priority="P0")
            add(operation, "边界值", "边界值分析", "invalid", f"{operation['summary']}：超大ID越界", "返回400或参数越界错误，不产生整数溢出和500。", {"action": "oversized_id", "field": id_field, "value": 999999999999999999999}, tool="pytest", automation_status="REVIEW_REQUIRED")
            add(operation, "可靠性", "错误推测", "invalid", f"{operation['summary']}：超时模拟", "存在受控延迟能力时返回504或明确超时；无注入能力时标记不适用并人工确认。", {"action": "timeout_simulation", "delay_ms": 30000}, tool="pytest", automation_status="REVIEW_REQUIRED", need_review=True)

            if operation.get("callbacks"):
                add(operation, "异常处理", "Mock场景", "invalid", f"{operation['summary']}：第三方回调使用Mock期望", "只调用隔离Mock端点并校验回调协议、签名和重试，不真实调用第三方。", {"action": "mock_callback", "callbacks": list(operation["callbacks"])}, tool="pytest", automation_status="REVIEW_REQUIRED", need_review=True)

            auth_fields = [item for item in fields if item["name"].lower() in AUTH_NAMES or item["location"] == "header" and item["name"].lower() == "authorization"]
            if operation["security"] or auth_fields:
                add(operation, "认证授权", "等价类划分", "invalid", f"{operation['summary']}：缺失认证凭证", "返回401或403，不返回受保护业务数据。", {"action": "remove_auth"}, priority="P0")
                add(operation, "认证授权", "等价类划分", "invalid", f"{operation['summary']}：无效或伪造认证凭证", "返回401或403，不泄露凭证校验细节。", {"action": "replace_auth", "value": "invalid-token"}, priority="P0")

            add(operation, "可靠性", "错误推测", "duplicate", f"{operation['summary']}：重复提交与幂等性", "相同幂等键重复请求不产生重复扣款、重复订单或重复状态流转；只读接口应返回一致结果。", {"action": "repeat_same_request", "times": 2}, tool="pytest", automation_status="REVIEW_REQUIRED", priority="P0")
            add(operation, "并发", "并发场景法", "concurrent", f"{operation['summary']}：同一资源并发请求", "写接口应满足锁、版本和状态机约束；只读接口结果应稳定且无异常。", {"action": "concurrent_same_request", "users": 5}, tool="JMeter", automation_status="REVIEW_REQUIRED", priority="P0")

            if any("json" in key.lower() for key in (request_body.get("content") or {})):
                add(operation, "异常处理", "错误推测", "invalid", f"{operation['summary']}：JSON格式损坏", "返回400或422，不产生500和部分写入。", {"action": "malformed_json", "value": "{invalid-json"})

    exploratory_count = math.floor(len(cases) * 0.2)
    exploratory_candidates = [
        case for case in cases
        if case.get("meta", {}).get("scenario_type") != "boundary"
        and case.get("security_policy") == "STANDARD_TEST_ENVIRONMENT"
    ]
    for case in exploratory_candidates[:exploratory_count]:
        case["request_mutation"]["exploratory_injection"] = {"field": "__debug", "value": True}
        case["payload"]["mutation"] = case["request_mutation"]
        case["tags"] = list(dict.fromkeys(case["tags"] + ["exploratory"]))

    coverage_weights = _distribute_coverage_weights(cases)
    scenario_counts = dict(Counter(case["meta"]["scenario_type"] for case in cases))
    dimension_counts = dict(Counter(case["dimension"] for case in cases))
    tool_counts = dict(Counter(case["recommended_tool"] for case in cases))
    quality_gate = _quality_gate(cases, coverage_weights)
    execution_order = [
        case["case_id"]
        for case in sorted(
            cases,
            key=lambda item: (
                0 if item.get("priority") == "critical" else 1,
                0 if "security" in (item.get("tags") or []) else 1,
                0 if item.get("method") in {"POST", "GET", "PUT", "PATCH", "DELETE"} else 1,
                int(re.search(r"_(\d{3})_", item["case_id"]).group(1)),
            ),
        )
    ]
    protocols = sorted({str(operation.get("protocol") or "rest") for operation in operations})
    endpoints = [operation["path"] for operation in operations]
    return {
        "schema_version": "2.0",
        "report_type": "SCHEMA_DRIVEN_API_TEST_CASE_DESIGN",
        "package_id": package_id,
        "test_suite": {
            "name": f"{package_id or 'API'} 接口测试集",
            "version": "2.0.0",
            "target": {
                "protocol": protocols[0] if len(protocols) == 1 else protocols,
                "base_url": str((spec.get("servers") or [{}])[0].get("url") or ""),
                "endpoint": endpoints[0] if len(endpoints) == 1 else endpoints,
            },
        },
        "execution_order": execution_order,
        "summary": {
            "interfaces": len(operations),
            "cases": len(cases),
            "total": len(cases),
            "normal": scenario_counts.get("normal", 0),
            "exception": scenario_counts.get("exception", 0),
            "boundary": scenario_counts.get("boundary", 0),
            "coverage_weights": coverage_weights,
            "estimated_duration": round(len(cases) * 0.4, 1),
            "dimensions": dimension_counts,
            "tools": tool_counts,
            "review_required": sum(case["automation_status"] == "REVIEW_REQUIRED" for case in cases),
            "quality_gate": quality_gate["thresholds"],
        },
        "quality_gate": quality_gate,
        "coverage_dimensions": [
            "功能", "响应契约", "参数校验", "等价类", "边界值", "认证授权", "异常处理", "可靠性", "并发", "安全"
        ],
        "operations": operations,
        "cases": cases,
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# Schema驱动接口测试用例 v2.0",
        "",
        f"- 接口数：{summary['interfaces']}",
        f"- 用例数：{summary['cases']}",
        f"- 场景数：正常 {summary['normal']} / 异常 {summary['exception']} / 边界 {summary['boundary']}",
        f"- 覆盖权重：正常 {summary['coverage_weights']['normal']}% / 异常 {summary['coverage_weights']['exception']}% / 边界 {summary['coverage_weights']['boundary']}%",
        f"- 质量门禁：{payload['quality_gate']['status']}",
        f"- 需要人工确认后执行：{summary['review_required']}",
        f"- 测试维度：{', '.join(payload['coverage_dimensions'])}",
        "",
        "| 用例ID | 场景 | 权重 | 协议 | 接口 | 请求上下文/参数 | 断言层 | 清理 | 推断/复核 | 标签 | 工具 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in payload["cases"]:
        context_payload = json.dumps({"context": case["context"], "payload": case["payload"]}, ensure_ascii=False)
        assertions = json.dumps(case["assertions"], ensure_ascii=False)
        cleanup = json.dumps(case["cleanup"], ensure_ascii=False)
        cells = [
            case["case_id"], case["meta"]["scenario_type"], case["meta"]["coverage_weight"],
            case["meta"]["protocol"], f"{case['method']} `{case['path']}`", context_payload,
            assertions, cleanup, f"{case['inferred']}/{case['need_review']}",
            ", ".join(case["tags"]), case["recommended_tool"],
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
    headers = ["用例ID", "描述", "场景类型", "覆盖权重", "协议", "方法", "路径", "优先级", "标签", "依赖与变量", "请求载荷", "协议断言", "Schema断言", "业务断言", "数据断言", "性能断言", "清理", "是否推断", "需要复核", "建议", "推荐工具", "自动化状态"]
    rows = [headers]
    for case in payload["cases"]:
        rows.append([
            case["case_id"], case["description"], case["meta"]["scenario_type"], case["meta"]["coverage_weight"],
            case["meta"]["protocol"], case["method"], case["path"], case["priority"], ", ".join(case["tags"]),
            json.dumps(case["context"], ensure_ascii=False), json.dumps(case["payload"], ensure_ascii=False),
            json.dumps(case["assertions"]["protocol"], ensure_ascii=False), json.dumps(case["assertions"]["schema"], ensure_ascii=False),
            json.dumps(case["assertions"]["business_logic"], ensure_ascii=False),
            json.dumps({"db": case["assertions"].get("db_check"), "cache": case["assertions"].get("cache_check"), "message": case["assertions"].get("message_check")}, ensure_ascii=False),
            json.dumps(case["assertions"]["performance"], ensure_ascii=False), json.dumps(case["cleanup"], ensure_ascii=False),
            case["inferred"], case["need_review"], case["suggestion"], case["recommended_tool"], case["automation_status"],
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
