from __future__ import annotations

import copy
import json
import re
import urllib.parse
from collections import defaultdict
from pathlib import Path
from typing import Any


AUTH_NAMES = {"authorization", "ticket", "token", "access_token", "cookie"}
BUILTIN_VARIABLES = {
    "random_int", "random_phone", "random_uuid", "now_iso", "timestamp",
    "random_string", "random_email", "random_enum", "random_date", "random_boolean",
}


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


def _remove_nested(target: dict[str, Any], dotted: str) -> None:
    parts = [part for part in dotted.split(".") if part and part != "$"]
    if not parts:
        target.clear()
        return
    current: Any = target
    for part in parts[:-1]:
        if not isinstance(current, dict):
            return
        current = current.get(part)
    if isinstance(current, dict):
        current.pop(parts[-1], None)


def _operation_baseline(operation: dict[str, Any]) -> dict[str, Any]:
    query: dict[str, Any] = {}
    headers: dict[str, Any] = {}
    path_values: dict[str, Any] = {}
    body: Any = {}
    body_fields = []
    for field in operation.get("fields") or []:
        location = str(field.get("location") or "query")
        name = str(field.get("name") or "")
        value = copy.deepcopy(field.get("sample"))
        if location == "query":
            query[name] = value
        elif location == "header":
            headers[name] = value
        elif location == "path":
            path_values[name] = value
        elif location == "cookie":
            headers.setdefault("Cookie", "")
            headers["Cookie"] += ("; " if headers["Cookie"] else "") + f"{name}={value}"
        elif location == "body":
            body_fields.append((name, value))
    for name, value in sorted(body_fields, key=lambda item: item[0].count(".")):
        if name == "$":
            body = value
        elif isinstance(body, dict):
            _set_nested(body, name, value)
    content_types = operation.get("content_types") or []
    if content_types and "Content-Type" not in headers:
        headers["Content-Type"] = str(content_types[0])
    return {"query": query, "headers": headers, "path_values": path_values, "body": body}


def _replace_path_values(path: str, values: dict[str, Any]) -> str:
    result = path
    for name in re.findall(r"\{([^{}]+)\}", path):
        value = values.get(name, "{{" + name + "}}")
        result = result.replace("{" + name + "}", urllib.parse.quote(str(value), safe="{}"))
    return result


def _remove_auth(request: dict[str, Any]) -> None:
    request["query"] = {key: value for key, value in request["query"].items() if key.lower() not in AUTH_NAMES}
    request["headers"] = {key: value for key, value in request["headers"].items() if key.lower() not in AUTH_NAMES}


def _replace_auth(request: dict[str, Any], value: Any) -> None:
    replaced = False
    for container_name in ("query", "headers"):
        container = request[container_name]
        for key in list(container):
            if key.lower() in AUTH_NAMES:
                container[key] = value
                replaced = True
    if not replaced:
        request["headers"]["Authorization"] = f"Bearer {value}"


def _replace_field(request: dict[str, Any], field: str, value: Any) -> None:
    location, _, name = field.partition(".")
    if location == "body" and isinstance(request["body"], dict):
        _set_nested(request["body"], name, value)
    elif location == "path":
        request["path_values"][name] = value
    elif location in {"query", "header"}:
        request["headers" if location == "header" else "query"][name] = value


def _apply_mutation(operation: dict[str, Any], mutation: dict[str, Any]) -> dict[str, Any]:
    request = _operation_baseline(operation)
    request.update({"method": operation["method"], "raw_body": None})
    action = str(mutation.get("action") or "use_valid_baseline")
    field = str(mutation.get("field") or "")
    location, _, name = field.partition(".")
    if action == "remove":
        if location == "body" and isinstance(request["body"], dict):
            _remove_nested(request["body"], name)
        elif location == "path":
            request["path_values"][name] = ""
        elif location in {"query", "header"}:
            request["headers" if location == "header" else "query"].pop(name, None)
    elif action == "replace":
        value = mutation.get("value")
        if location == "body" and isinstance(request["body"], dict):
            _set_nested(request["body"], name, value)
        elif location == "path":
            request["path_values"][name] = value
        elif location in {"query", "header"}:
            request["headers" if location == "header" else "query"][name] = value
    elif action == "remove_auth":
        _remove_auth(request)
    elif action == "replace_auth":
        _replace_auth(request, mutation.get("value", "invalid-token"))
    elif action == "remove_request_body":
        request["body"] = None
    elif action == "replace_content_type":
        request["headers"]["Content-Type"] = str(mutation.get("value") or "text/plain")
    elif action == "malformed_json":
        request["raw_body"] = str(mutation.get("value") or "{invalid-json")
    elif action == "use_unsupported_http_method":
        request["method"] = "POST" if operation["method"] in {"GET", "HEAD", "OPTIONS"} else "GET"
    elif action == "empty_request":
        request.update({"query": {}, "headers": {}, "body": None})
    elif action in {"type_confusion", "sql_injection", "xss_injection", "unicode_null", "path_traversal", "oversized_id"}:
        _replace_field(request, field, mutation.get("value"))
    elif action == "oversized_payload":
        _replace_field(request, field, "A" * int(mutation.get("size_bytes") or 1024 * 1024))
    exploratory = mutation.get("exploratory_injection") or {}
    if exploratory and isinstance(request.get("body"), dict):
        request["body"][str(exploratory.get("field") or "__debug")] = exploratory.get("value", True)
    return request


def _builtin_pre_request_script() -> list[str]:
    return [
        "const pad = (n) => String(n).padStart(2, '0');",
        "pm.collectionVariables.set('random_phone', '1' + String(300 + Math.floor(Math.random() * 100)).padStart(3, '0') + String(Math.floor(Math.random() * 10000000)).padStart(7, '0'));",
        "pm.collectionVariables.set('random_email', 'test_' + Math.random().toString(36).slice(2, 10) + '@example.com');",
        "pm.collectionVariables.set('random_uuid', 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => { const r = Math.random() * 16 | 0; return (c === 'x' ? r : (r & 3 | 8)).toString(16); }));",
        "pm.collectionVariables.set('now_iso', new Date().toISOString());",
        "pm.collectionVariables.set('timestamp', String(Math.floor(Date.now() / 1000)));",
        "pm.collectionVariables.set('random_boolean', Math.random() >= 0.5 ? 'true' : 'false');",
    ]


def _expected_test_script(case: dict[str, Any]) -> list[str]:
    case_id = json.dumps(str(case.get("case_id") or ""), ensure_ascii=False)
    valid = str(case.get("equivalence_partition") or "") == "valid"
    action = str((case.get("request_mutation") or {}).get("action") or "")
    lines = [
        f"const autotestCaseId = {case_id};",
        'pm.test(autotestCaseId + " 不出现服务端未处理异常", function () { pm.expect(pm.response.code).to.be.below(500); });',
        "let responseJson = null;",
        "try { responseJson = pm.response.json(); } catch (e) { responseJson = null; }",
    ]
    if valid:
        lines.append('pm.test(autotestCaseId + " HTTP请求成功", function () { pm.expect(pm.response.code).to.be.within(200, 299); });')
        lines.append('if (responseJson && Object.prototype.hasOwnProperty.call(responseJson, "code")) { pm.test(autotestCaseId + " 业务码成功", function () { pm.expect([0, 200, "0", "200"]).to.include(responseJson.code); }); }')
    else:
        lines.append('pm.test(autotestCaseId + " 无效输入被明确处理", function () { const rejectedByHttp = pm.response.code >= 400 && pm.response.code < 500; const rejectedByBusiness = responseJson && Object.prototype.hasOwnProperty.call(responseJson, "code") && ![0, 200, "0", "200"].includes(responseJson.code); pm.expect(Boolean(rejectedByHttp || rejectedByBusiness)).to.eql(true); });')
    if action == "validate_response_contract":
        lines.append('pm.test(autotestCaseId + " 响应为合法JSON对象", function () { pm.expect(responseJson).to.be.an("object"); });')
    if action in {"remove_auth", "replace_auth"}:
        lines.append('pm.test(autotestCaseId + " 未返回受保护成功数据", function () { const denied = [401, 403].includes(pm.response.code) || (responseJson && ![0, 200, "0", "200"].includes(responseJson.code)); pm.expect(Boolean(denied)).to.eql(true); });')
    return lines


def compile_api_cases_to_postman(case_design: dict[str, Any], base_url: str = "", include_review_required: bool = False) -> dict[str, Any]:
    operations = {str(item.get("operation_id")): item for item in case_design.get("operations") or []}
    folders: dict[str, list[dict[str, Any]]] = defaultdict(list)
    mapping = []
    skipped = []
    for case in case_design.get("cases") or []:
        case_id = str(case.get("case_id") or "")
        status = str(case.get("automation_status") or "")
        tool = str(case.get("recommended_tool") or "")
        if status != "READY" and not include_review_required:
            skipped.append({"case_id": case_id, "reason": status or "NOT_READY", "recommended_tool": tool})
            continue
        if tool.lower() != "newman":
            skipped.append({"case_id": case_id, "reason": "ROUTED_TO_OTHER_TOOL", "recommended_tool": tool})
            continue
        operation = operations.get(str(case.get("operation_id") or ""))
        if not operation:
            skipped.append({"case_id": case_id, "reason": "MISSING_OPERATION", "recommended_tool": tool})
            continue
        mutation = case.get("request_mutation") or {}
        compiled = _apply_mutation(operation, mutation)
        path = _replace_path_values(str(operation.get("path") or case.get("path") or ""), compiled["path_values"])
        query = urllib.parse.urlencode(list(compiled["query"].items()), doseq=True, safe="{}%")
        raw_url = "{{baseUrl}}" + (path if path.startswith("/") else "/" + path)
        if query:
            raw_url += "?" + query
        request: dict[str, Any] = {
            "method": compiled["method"],
            "header": [{"key": key, "value": str(value), "type": "text"} for key, value in compiled["headers"].items()],
            "url": raw_url,
            "description": str(case.get("expected_result") or ""),
        }
        if compiled["raw_body"] is not None:
            request["body"] = {"mode": "raw", "raw": compiled["raw_body"]}
        elif compiled["body"] not in (None, {}, ""):
            request["body"] = {"mode": "raw", "raw": json.dumps(compiled["body"], ensure_ascii=False)}
        item = {
            "name": f"[{case_id}] {case.get('title') or case_id}",
            "request": request,
            "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": _expected_test_script(case)}}],
            "x-autotest-case": {"case_id": case_id, "dimension": case.get("dimension"), "partition": case.get("equivalence_partition"), "mutation": mutation},
        }
        folders[str(case.get("dimension") or "其他")].append(item)
        mapping.append({"case_id": case_id, "collection_item": item["name"], "dimension": case.get("dimension"), "method": compiled["method"], "path": operation.get("path")})
    required_runtime_variables = sorted({
        variable
        for items in folders.values()
        for item in items
        for variable in re.findall(r"\{\{([A-Za-z0-9_]+)\}\}", json.dumps(item.get("request") or {}, ensure_ascii=False))
        if variable != "baseUrl" and variable not in BUILTIN_VARIABLES
    })
    collection = {
        "info": {
            "name": f"{case_design.get('package_name') or case_design.get('package_id') or 'Requirement'} 接口测试集合",
            "description": "由接口测试用例设计编译生成；不包含复杂业务场景和性能测试计划。",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [{"key": "baseUrl", "value": base_url}],
        "event": [{"listen": "prerequest", "script": {"type": "text/javascript", "exec": _builtin_pre_request_script()}}],
        "item": [{"name": name, "item": items} for name, items in folders.items()],
    }
    return {
        "schema_version": "1.0",
        "report_type": "API_TEST_CASE_EXECUTION_ASSET",
        "package_id": case_design.get("package_id"),
        "summary": {"source_cases": len(case_design.get("cases") or []), "compiled_newman_cases": len(mapping), "skipped_cases": len(skipped), "required_runtime_variables": required_runtime_variables},
        "collection": collection,
        "mapping": mapping,
        "skipped": skipped,
    }


def write_api_execution_assets(payload: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    collection_path = output_dir / "api-test-collection.json"
    manifest_path = output_dir / "api-test-execution-manifest.json"
    collection_path.write_text(json.dumps(payload["collection"], ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {key: value for key, value in payload.items() if key != "collection"}
    manifest["collection_path"] = str(collection_path)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"collection": str(collection_path), "manifest": str(manifest_path)}
