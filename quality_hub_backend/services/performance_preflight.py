from __future__ import annotations

import json
import re
import urllib.parse
from collections.abc import Iterable
from copy import deepcopy
from typing import Any


_PLACEHOLDER_PATTERNS = (
    re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*\}\}"),
    re.compile(r"\$\{\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*\}"),
)
_BUILTIN_VARIABLES = {
    "t",
    "timestamp",
    "now",
    "threadNum",
    "thread_num",
}
_VARIABLE_ALIASES = {
    "anchorUid": ("uid", "applicant_uid"),
    "anchorTicket": ("ticket", "applicant_ticket"),
    "agentUid": ("proxy_uid", "uid"),
    "proxyUid": ("proxy_uid", "uid"),
    "orderNo": ("salary_order_no", "order_no"),
    "orderId": ("salary_order_id", "order_id"),
    "receiveCurrency": ("currency",),
    "receiveAccount": ("bankAccount", "bank_account"),
    "receiveAccountType": ("receive_account_type", "accountType", "account_type"),
    "userRemark": ("user_remark",),
}
_SAFE_OPENAPI_INPUTS = {
    "page",
    "pageno",
    "pagenum",
    "pagesize",
    "limit",
    "offset",
}
_SAFE_OPENAPI_HEADERS = {"accept", "content-type"}
_SENSITIVE_INPUT_RE = re.compile(r"ticket|token|password|secret|authorization|cookie", re.I)


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _walk_strings(item)


def referenced_variables(value: Any) -> set[str]:
    variables: set[str] = set()
    for text in _walk_strings(value):
        for pattern in _PLACEHOLDER_PATTERNS:
            variables.update(pattern.findall(text))
    return variables


def summarize_missing_runtime_inputs(readiness: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Flatten target preflight gaps into user-supplied runtime fields."""
    grouped: dict[str, dict[str, Any]] = {}
    for target in (readiness or {}).get("targets") or []:
        target_key = str(target.get("key") or "").strip()
        for missing in target.get("missing") or []:
            names = list(missing.get("missing_fields") or [])
            if not names and missing.get("name") != "request_body":
                names = [missing.get("name")]
            for raw_name in names:
                name = str(raw_name or "").strip()
                if not name:
                    continue
                item = grouped.setdefault(name, {
                    "name": name,
                    "location": str(missing.get("location") or "runtime"),
                    "sensitive": bool(_SENSITIVE_INPUT_RE.search(name)),
                    "fillable": not bool(_SENSITIVE_INPUT_RE.search(name)) and name != "request_body",
                    "targets": [],
                    "reasons": [],
                })
                if target_key and target_key not in item["targets"]:
                    item["targets"].append(target_key)
                reason = str(missing.get("reason") or "当前数据源未提供").strip()
                if reason and reason not in item["reasons"]:
                    item["reasons"].append(reason)
    return list(grouped.values())


def _operation(document: dict[str, Any], method: str, path: str) -> dict[str, Any]:
    paths = document.get("paths") if isinstance(document, dict) else {}
    if not isinstance(paths, dict):
        return {}
    normalized = "/" + str(path or "").split("?", 1)[0].strip("/")
    candidates = [normalized]
    if normalized.startswith("/userserv/"):
        candidates.append(normalized[len("/userserv") :])
    for candidate in candidates:
        item = paths.get(candidate)
        if isinstance(item, dict) and isinstance(item.get(method.lower()), dict):
            return item[method.lower()]
    return {}


def _request_body_input(request_body: Any) -> dict[str, Any] | None:
    if not isinstance(request_body, dict):
        return None
    content = request_body.get("content")
    if not isinstance(content, dict) or not content:
        return (
            {"name": "request_body", "location": "body", "required_fields": []}
            if request_body.get("required")
            else None
        )

    content_type = ""
    media: dict[str, Any] = {}
    for candidate, definition in content.items():
        if isinstance(definition, dict):
            content_type = str(candidate or "").strip()
            media = definition
            break
    schema = media.get("schema") if isinstance(media.get("schema"), dict) else {}
    required_fields = [
        str(name).strip()
        for name in schema.get("required") or []
        if str(name).strip()
    ]
    if not request_body.get("required") and not required_fields:
        return None
    return {
        "name": "request_body",
        "location": "body",
        "content_type": content_type,
        "required_fields": required_fields,
    }


def _required_operation_inputs(operation: dict[str, Any]) -> list[dict[str, Any]]:
    required: list[dict[str, Any]] = []
    body_input = _request_body_input(operation.get("requestBody"))
    for parameter in operation.get("parameters") or []:
        if not isinstance(parameter, dict) or not parameter.get("required"):
            continue
        name = str(parameter.get("name") or "").strip()
        if name:
            schema = parameter.get("schema") if isinstance(parameter.get("schema"), dict) else {}
            required.append({
                "name": name,
                "location": str(parameter.get("in") or "query"),
                "example": parameter.get("example"),
                "default": schema.get("default"),
                "content_type": (
                    body_input.get("content_type")
                    if body_input and name.lower() == "content-type"
                    else ""
                ),
            })
    if body_input:
        required.append(body_input)
    return required


def _declared_endpoint_inputs(
    contracts: Iterable[dict[str, Any]],
    method: str,
    path: str,
) -> list[dict[str, Any]]:
    normalized = _normalized_path(path)
    for contract in contracts:
        if not isinstance(contract, dict):
            continue
        contract_method = str(contract.get("method") or "").strip().upper()
        contract_path = str(contract.get("path") or "").strip()
        if contract_method != method or _normalized_path(contract_path) != normalized:
            continue
        return [
            {
                "name": str(item.get("name") or "").strip(),
                "location": str(item.get("location") or "query").strip().lower(),
                "declared_by": "requirement_resource_manifest",
            }
            for item in contract.get("required_inputs") or []
            if isinstance(item, dict) and str(item.get("name") or "").strip()
        ]
    return []


def _merge_required_inputs(*groups: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    positions: dict[tuple[str, str], int] = {}
    for group in groups:
        for item in group:
            name = str(item.get("name") or "").strip()
            location = str(item.get("location") or "query").strip().lower()
            if not name:
                continue
            key = (name.lower(), location)
            normalized = {**item, "name": name, "location": location}
            if key in positions:
                merged[positions[key]] = {**merged[positions[key]], **normalized}
            else:
                positions[key] = len(merged)
                merged.append(normalized)
    return merged


def _response_contract(operation: dict[str, Any], expected_status: Any = 200) -> dict[str, Any]:
    responses = operation.get("responses") if isinstance(operation, dict) else {}
    if not isinstance(responses, dict):
        return {}
    status = str(expected_status or 200)
    response = responses.get(status)
    if not isinstance(response, dict):
        response = next(
            (
                value for key, value in responses.items()
                if str(key).upper().endswith("XX")
                and str(key)[0:1] == status[0:1]
                and isinstance(value, dict)
            ),
            {},
        )
    content = response.get("content") if isinstance(response, dict) else {}
    if not isinstance(content, dict) or not content:
        return {}
    content_type = ""
    media: dict[str, Any] = {}
    for candidate, definition in content.items():
        if isinstance(definition, dict) and "json" in str(candidate).lower():
            content_type = str(candidate)
            media = definition
            break
    if not media:
        for candidate, definition in content.items():
            if isinstance(definition, dict):
                content_type = str(candidate)
                media = definition
                break
    schema = media.get("schema") if isinstance(media.get("schema"), dict) else {}
    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    required_fields = [
        str(name).strip()
        for name in schema.get("required") or []
        if str(name).strip()
    ]
    field_types = {
        str(name): str(definition.get("type"))
        for name, definition in properties.items()
        if isinstance(definition, dict) and definition.get("type")
    }
    non_empty_fields = []
    for name, definition in properties.items():
        if not isinstance(definition, dict):
            continue
        if (
            int(definition.get("minLength") or 0) > 0
            or int(definition.get("minItems") or 0) > 0
            or int(definition.get("minProperties") or 0) > 0
        ):
            non_empty_fields.append(str(name))
    code_definition = properties.get("code") if isinstance(properties.get("code"), dict) else {}
    success_codes = list(code_definition.get("enum") or [])
    if not success_codes and code_definition.get("const") is not None:
        success_codes = [code_definition.get("const")]
    if not success_codes:
        candidate = code_definition.get("default")
        if candidate is None:
            candidate = code_definition.get("example")
        if candidate is not None:
            success_codes = [candidate]
    if not success_codes and "code" in properties and status.startswith("2"):
        success_codes = [0, 200, "0", "200"]
    return {
        "content_type": content_type,
        "require_json": "json" in content_type.lower() or bool(required_fields),
        "required_fields": required_fields,
        "field_types": field_types,
        "non_empty_fields": non_empty_fields,
        "business_code_field": "code" if "code" in properties else "",
        "success_codes": success_codes,
        "message_field": "message" if "message" in properties else "",
    }


def _normalized_path(path: str) -> str:
    parsed = urllib.parse.urlsplit(
        path if path.startswith(("http://", "https://")) else "https://local/" + path.lstrip("/")
    )
    return "/" + (parsed.path or "/").strip("/")


def _source_for(name: str, sources: dict[str, dict[str, Any]]) -> tuple[str, dict[str, Any]] | None:
    candidates = (name, *_VARIABLE_ALIASES.get(name, ()))
    for candidate in candidates:
        if candidate in _BUILTIN_VARIABLES:
            return candidate, {"type": "builtin", "variable": candidate, "validated": True}
        if candidate in sources:
            return candidate, sources[candidate]
    return None


def _public_source(source: dict[str, Any]) -> dict[str, Any]:
    return {
        str(key): value
        for key, value in source.items()
        if key not in {"value", "raw_value"} and value not in (None, "")
    }


def _placeholder_for(source_name: str, source: dict[str, Any]) -> str:
    if source.get("type") == "prior_extraction":
        return "${" + source_name + "}"
    return "{{" + source_name + "}}"


def _safe_openapi_value(required: dict[str, Any]) -> str | None:
    name = str(required.get("name") or "")
    if name.lower() not in _SAFE_OPENAPI_INPUTS:
        return None
    value = required.get("default")
    if value in (None, ""):
        value = required.get("example")
    text = str(value or "").strip()
    if not text or referenced_variables(text):
        return None
    try:
        numeric = int(text)
    except ValueError:
        return None
    if name.lower() in {"page", "pageno", "pagenum"} and numeric < 1:
        return None
    if name.lower() == "pagesize" and not 1 <= numeric <= 1000:
        return None
    if name.lower() in {"limit", "offset"} and numeric < 0:
        return None
    return str(numeric)


def _safe_openapi_header_value(required: dict[str, Any]) -> str | None:
    name = str(required.get("name") or "").strip().lower()
    if name not in _SAFE_OPENAPI_HEADERS:
        return None
    value = required.get("default")
    if value in (None, ""):
        value = required.get("example")
    if value in (None, "") and name == "content-type":
        value = required.get("content_type")
    text = str(value or "").strip()
    if not text or referenced_variables(text) or "\n" in text or "\r" in text:
        return None
    if name in {"accept", "content-type"} and not re.fullmatch(
        r"[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+(?:\s*;\s*[A-Za-z0-9!#$&^_.+-]+=[^;\r\n]+)*",
        text,
    ):
        return None
    return text


def _case_headers(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return deepcopy(value)
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _header_value(headers: dict[str, Any], name: str) -> Any:
    expected = name.strip().lower()
    for key, value in headers.items():
        if str(key).strip().lower() == expected:
            return value
    return None


def _payload_field_names(payload: Any, content_type: str) -> set[str] | None:
    mapping = _payload_mapping(payload, content_type)
    return set(mapping) if mapping is not None else None


def _payload_mapping(payload: Any, content_type: str) -> dict[str, Any] | None:
    if isinstance(payload, dict):
        return deepcopy(payload)
    if payload in (None, ""):
        return {}
    if not isinstance(payload, str):
        return None
    text = payload.strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        parsed = None
    if isinstance(parsed, dict):
        return parsed
    if "application/x-www-form-urlencoded" in str(content_type or "").lower():
        return {
            str(name): value
            for name, value in urllib.parse.parse_qsl(text, keep_blank_values=True)
        }
    return None


def _serialize_payload_like(original: Any, payload: dict[str, Any], content_type: str) -> Any:
    if isinstance(original, dict):
        return payload
    if "application/x-www-form-urlencoded" in str(content_type or "").lower():
        return urllib.parse.urlencode(list(payload.items()), doseq=True, safe="${}[]")
    return json.dumps(payload, ensure_ascii=False)


def _matches_producer(rule: dict[str, Any], method: str, path: str) -> bool:
    source_method = str(rule.get("source_method") or "").strip().upper()
    source_path = str(rule.get("source_path") or "").strip()
    if not source_method or not source_path:
        return False
    return source_method == method and _normalized_path(source_path) == _normalized_path(path)


def _append_query_inputs(path: str, resolved_inputs: dict[str, Any], required_inputs: list[dict[str, Any]]) -> str:
    parsed = urllib.parse.urlsplit(
        path if path.startswith(("http://", "https://")) else "https://local/" + path.lstrip("/")
    )
    pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    current = {name for name, _ in pairs}
    locations = {str(item.get("name")): str(item.get("location") or "query") for item in required_inputs}
    for name, value in resolved_inputs.items():
        if locations.get(name) == "query" and name not in current:
            pairs.append((name, str(value)))
    query = urllib.parse.urlencode(pairs, doseq=True, safe="${}[]")
    rebuilt = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))
    if path.startswith(("http://", "https://")):
        return rebuilt
    return (parsed.path or "/") + (("?" + query) if query else "")


def build_target_readiness(
    cases: Iterable[dict[str, Any]],
    *,
    runtime_values: dict[str, Any] | None = None,
    runtime_sources: dict[str, dict[str, Any]] | None = None,
    csv_columns: Iterable[str] = (),
    extracted_variables: Iterable[str] = (),
    extraction_rules: Iterable[dict[str, Any]] = (),
    openapi_documents: Iterable[dict[str, Any]] = (),
    endpoint_input_contracts: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    runtime_values = runtime_values or {}
    runtime_sources = runtime_sources or {}
    sources: dict[str, dict[str, Any]] = {
        str(name): {"type": "csv", "variable": str(name), "validated": True}
        for name in csv_columns
        if str(name).strip()
    }
    for key, value in runtime_values.items():
        name = str(key)
        if name.startswith("_") or value in (None, "", [], {}):
            continue
        declared = runtime_sources.get(name) if isinstance(runtime_sources.get(name), dict) else {}
        sources[name] = {
            "type": declared.get("type") or sources.get(name, {}).get("type") or "runtime",
            "variable": name,
            "validated": bool(declared.get("validated", sources.get(name, {}).get("validated", False))),
            **{str(k): v for k, v in declared.items() if k not in {"value", "raw_value"}},
        }
    for name in extracted_variables:
        variable = str(name).strip()
        if variable:
            sources[variable] = {
                "type": "prior_extraction",
                "variable": variable,
                "validated": True,
                "already_produced": True,
            }
    for name in _BUILTIN_VARIABLES:
        sources.setdefault(name, {"type": "builtin", "variable": name, "validated": True})

    extraction_rules = [dict(item) for item in extraction_rules if isinstance(item, dict)]
    initial_variables = sorted(sources)
    produced: list[dict[str, Any]] = []

    targets: list[dict[str, Any]] = []
    for case in cases:
        method = str(case.get("_performance_method") or case.get("method") or "").upper()
        path = str(case.get("_performance_path") or case.get("path") or "")
        key = str(case.get("_performance_key") or f"{method} {_normalized_path(path)}").strip()
        serialized_fields = {
            field: case.get(field)
            for field in ("path", "headers", "payload", "parameters", "context", "request")
        }
        referenced = referenced_variables(serialized_fields)
        operation: dict[str, Any] = {}
        for document in openapi_documents:
            operation = _operation(document, method, path)
            if operation:
                break
        required_inputs = _merge_required_inputs(
            _required_operation_inputs(operation),
            _declared_endpoint_inputs(endpoint_input_contracts, method, path),
        )
        response_contract = _response_contract(operation, case.get("expected_status") or 200)

        parsed = urllib.parse.urlsplit(
            path if path.startswith(("http://", "https://")) else "https://local/" + path.lstrip("/")
        )
        query_values = {
            name: value
            for name, value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        }
        case_headers = _case_headers(case.get("headers"))
        missing: list[dict[str, Any]] = []
        resolved_inputs: dict[str, Any] = {}
        resolved_headers: dict[str, Any] = {}
        resolved_body: dict[str, Any] = {}
        resolved_body_content_type = ""
        input_sources: dict[str, dict[str, Any]] = {}
        for variable in sorted(referenced):
            resolved = _source_for(variable, sources)
            if not resolved:
                missing.append({"name": variable, "location": "placeholder", "reason": "变量没有运行时、CSV或前置提取来源"})
            else:
                source_name, source = resolved
                input_sources.setdefault(variable, _public_source(source))
                resolved_inputs.setdefault(variable, _placeholder_for(source_name, source))
        for required in required_inputs:
            name = required["name"]
            location = required["location"]
            if location == "body":
                payload = case.get("payload")
                required_fields = list(required.get("required_fields") or [])
                content_type = str(required.get("content_type") or "")
                payload_mapping = _payload_mapping(payload, content_type)
                if payload_mapping == {} and not required_fields:
                    missing.append({"name": name, "location": location, "reason": "OpenAPI声明请求体必填"})
                elif payload_mapping is not None and required_fields:
                    missing_fields = []
                    for field in required_fields:
                        current_value = payload_mapping.get(field)
                        if current_value not in (None, ""):
                            current_refs = referenced_variables(current_value)
                            unresolved_refs = [ref for ref in current_refs if not _source_for(ref, sources)]
                            if unresolved_refs:
                                missing_fields.append(field)
                                continue
                            resolved_body[field] = current_value
                            input_sources.setdefault(field, {
                                "type": "case_definition",
                                "validated": not bool(current_refs),
                                "variables": sorted(current_refs),
                            })
                            continue
                        resolved = _source_for(field, sources)
                        if not resolved:
                            missing_fields.append(field)
                            continue
                        source_name, source = resolved
                        value = _placeholder_for(source_name, source)
                        payload_mapping[field] = value
                        resolved_body[field] = value
                        resolved_inputs.setdefault(field, value)
                        input_sources.setdefault(field, _public_source(source))
                    if missing_fields:
                        missing.append({
                            "name": name,
                            "location": location,
                            "reason": "OpenAPI请求体缺少必填字段：" + "、".join(missing_fields),
                            "required_fields": required_fields,
                            "missing_fields": missing_fields,
                            "content_type": content_type,
                        })
                    else:
                        resolved_body = payload_mapping
                        resolved_body_content_type = content_type
                continue
            explicit_value = (
                _header_value(case_headers, name)
                if location == "header"
                else query_values.get(name)
            )
            explicit_value = str(explicit_value or "").strip()
            if explicit_value:
                explicit_refs = referenced_variables(explicit_value)
                unresolved_refs = [ref for ref in explicit_refs if not _source_for(ref, sources)]
                if not unresolved_refs:
                    resolved_inputs[name] = explicit_value
                    if location == "header":
                        resolved_headers[name] = explicit_value
                    input_sources[name] = {
                        "type": "case_definition",
                        "validated": not bool(explicit_refs),
                        "variables": sorted(explicit_refs),
                    }
                    continue
                missing.append({
                    "name": name,
                    "location": location,
                    "reason": "请求中已有占位符，但其运行时来源尚未准备：" + "、".join(sorted(unresolved_refs)),
                })
                continue
            resolved = _source_for(name, sources)
            if resolved:
                source_name, source = resolved
                resolved_inputs[name] = _placeholder_for(source_name, source)
                if location == "header":
                    resolved_headers[name] = resolved_inputs[name]
                input_sources[name] = _public_source(source)
                continue
            if location == "header":
                safe_header = _safe_openapi_header_value(required)
                if safe_header is not None:
                    resolved_inputs[name] = safe_header
                    resolved_headers[name] = safe_header
                    input_sources[name] = {
                        "type": "openapi_safe_header",
                        "validated": True,
                        "policy": "protocol_header_only",
                    }
                    continue
            safe_default = _safe_openapi_value(required)
            if safe_default is not None:
                resolved_inputs[name] = safe_default
                input_sources[name] = {
                    "type": "openapi_safe_default",
                    "validated": True,
                    "policy": "pagination_only",
                }
                continue
            declared_by = (
                "需求包接口输入契约"
                if required.get("declared_by") == "requirement_resource_manifest"
                else "OpenAPI"
            )
            missing.append({
                "name": name,
                "location": location,
                "reason": f"{declared_by}声明必填但当前数据源未提供",
            })

        deduplicated: list[dict[str, str]] = []
        seen = set()
        for item in missing:
            identity = (item["name"], item["location"])
            if identity not in seen:
                seen.add(identity)
                deduplicated.append(item)
        status = "BLOCKED" if deduplicated else "READY"
        resolved_path = _append_query_inputs(path, resolved_inputs, required_inputs) if status == "READY" else path
        targets.append({
            "key": key,
            "method": method,
            "path": parsed.path or path,
            "name": case.get("title") or case.get("name") or key,
            "status": status,
            "required_inputs": required_inputs,
            "referenced_variables": sorted(referenced),
            "missing": deduplicated,
            "resolved_inputs": resolved_inputs,
            "resolved_headers": resolved_headers,
            "resolved_body": resolved_body,
            "resolved_body_content_type": resolved_body_content_type,
            "input_sources": input_sources,
            "resolved_path": resolved_path,
            "openapi_matched": bool(operation),
            "response_contract": response_contract,
        })

        for rule in extraction_rules:
            variable = str(rule.get("variable") or "").strip()
            if not variable or not _matches_producer(rule, method, path):
                continue
            source = {
                "type": "prior_extraction",
                "variable": variable,
                "validated": True,
                "source_method": method,
                "source_path": _normalized_path(path),
                "json_paths": list(rule.get("json_paths") or []),
            }
            sources[variable] = source
            produced.append(_public_source(source))

    ready = [item for item in targets if item["status"] == "READY"]
    blocked = [item for item in targets if item["status"] == "BLOCKED"]
    return {
        "status": "BLOCKED" if targets and not ready else "READY_WITH_WARNINGS" if blocked else "READY",
        "summary": {
            "targets": len(targets),
            "ready": len(ready),
            "blocked": len(blocked),
        },
        "available_variables": initial_variables,
        "produced_variables": produced,
        "targets": targets,
    }


def apply_resolved_inputs(
    cases: Iterable[dict[str, Any]],
    readiness: dict[str, Any],
) -> list[dict[str, Any]]:
    by_key = {str(item.get("key") or ""): item for item in readiness.get("targets") or []}
    resolved_cases: list[dict[str, Any]] = []
    for source_case in cases:
        case = deepcopy(source_case)
        method = str(case.get("_performance_method") or case.get("method") or "").upper()
        path = str(case.get("_performance_path") or case.get("path") or "")
        key = str(case.get("_performance_key") or f"{method} {_normalized_path(path)}").strip()
        target = by_key.get(key) or {}
        if target.get("status") == "READY":
            if target.get("resolved_path"):
                case["path"] = str(target["resolved_path"])
            case["_performance_path"] = _normalized_path(case["path"])
            case["_performance_resolved_inputs"] = deepcopy(target.get("resolved_inputs") or {})
            case["_performance_input_sources"] = deepcopy(target.get("input_sources") or {})
            case["_performance_response_contract"] = deepcopy(target.get("response_contract") or {})
            resolved_headers = target.get("resolved_headers") or {}
            if resolved_headers:
                original_headers = case.get("headers")
                headers = _case_headers(original_headers)
                existing = {str(name).strip().lower() for name in headers}
                for name, value in resolved_headers.items():
                    if str(name).strip().lower() not in existing:
                        headers[str(name)] = value
                case["headers"] = (
                    json.dumps(headers, ensure_ascii=False)
                    if isinstance(original_headers, str)
                    else headers
                )
            resolved_body = target.get("resolved_body") or {}
            if resolved_body:
                case["payload"] = _serialize_payload_like(
                    case.get("payload"),
                    resolved_body,
                    str(target.get("resolved_body_content_type") or ""),
                )
        resolved_cases.append(case)
    return resolved_cases


def normalize_account_pool(
    applicant_rows: Iterable[dict[str, Any]],
    proxy_rows: Iterable[dict[str, Any]] = (),
    *,
    threads: int,
    reuse_policy: str = "round_robin",
    require_proxy_ticket: bool = True,
) -> dict[str, Any]:
    requested_threads = max(1, int(threads or 1))
    policy = str(reuse_policy or "round_robin").strip().lower()
    if policy not in {"round_robin", "strict_unique"}:
        raise ValueError("账号复用策略只允许 round_robin 或 strict_unique")

    valid_proxies: list[dict[str, Any]] = []
    for row in proxy_rows:
        enabled = str(row.get("enabled", "true")).strip().lower()
        uid = str(row.get("proxy_uid") or row.get("uid") or row.get("agent_uid") or "").strip()
        ticket = str(row.get("proxy_ticket") or row.get("ticket") or row.get("access_token") or "").strip()
        if (
            enabled not in {"0", "false", "no", "off"}
            and uid
            and (ticket or not require_proxy_ticket)
        ):
            valid_proxies.append(dict(row))

    rows: list[dict[str, str]] = []
    skipped: list[dict[str, Any]] = []
    proxy_cursor: dict[str, int] = {}
    for index, source in enumerate(applicant_rows, start=1):
        enabled = str(source.get("enabled", "true")).strip().lower()
        uid = str(source.get("applicant_uid") or source.get("uid") or "").strip()
        ticket = str(source.get("applicant_ticket") or source.get("ticket") or source.get("access_token") or "").strip()
        if enabled in {"0", "false", "no", "off"} or not uid or not ticket:
            skipped.append({"row": index, "uid": uid, "reason": "disabled_or_missing_uid_ticket"})
            continue
        currency = str(source.get("currency") or "").strip().upper()
        matching = []
        for proxy in valid_proxies:
            supported = str(proxy.get("support_currencies") or proxy.get("supportCurrencies") or proxy.get("currency") or "")
            currencies = {item.strip().upper() for item in re.split(r"[,|;/]", supported) if item.strip()}
            if not currency or currency in currencies:
                matching.append(proxy)
        proxy = None
        if matching:
            cursor = proxy_cursor.get(currency, 0)
            proxy = matching[cursor % len(matching)]
            proxy_cursor[currency] = cursor + 1

        normalized = {
            str(key): str(value)
            for key, value in source.items()
            if value not in (None, "")
        }
        normalized.update({
            "uid": uid,
            "ticket": ticket,
            "applicant_uid": uid,
            "applicant_ticket": ticket,
            "applicant_source": str(
                source.get("account_source")
                or source.get("source")
                or "applicant_account_pool"
            ),
            "anchorUid": uid,
            "anchorTicket": ticket,
            "countryCode": str(source.get("countryCode") or source.get("country_code") or ""),
            "country_code": str(source.get("countryCode") or source.get("country_code") or ""),
            "currency": currency,
        })
        if not normalized.get("receiveAccountType") and any(
            str(source.get(name) or "").strip()
            for name in ("bankAccount", "bank_account", "bankName", "bank_name")
        ):
            normalized["receiveAccountType"] = "bank"
        if not normalized.get("userRemark") and str(source.get("remark") or "").strip():
            normalized["userRemark"] = str(source["remark"]).strip()
        if proxy:
            proxy_uid = str(proxy.get("proxy_uid") or proxy.get("uid") or proxy.get("agent_uid") or "").strip()
            proxy_ticket = str(proxy.get("proxy_ticket") or proxy.get("ticket") or proxy.get("access_token") or "").strip()
            normalized.update({
                "proxy_uid": proxy_uid,
                "proxy_ticket": proxy_ticket,
                "proxy_source": str(
                    proxy.get("account_source")
                    or proxy.get("source")
                    or "proxy_account_pool"
                ),
                "proxyUid": proxy_uid,
                "agentUid": proxy_uid,
                "agentTicket": proxy_ticket,
            })
        rows.append(normalized)

    if not rows:
        status = "BLOCKED"
        message = "账号池没有同时具备uid和ticket的可执行申请人。"
    elif policy == "strict_unique" and len(rows) < requested_threads:
        status = "BLOCKED"
        message = f"严格独占模式需要{requested_threads}个账号，当前只有{len(rows)}个。"
    else:
        status = "READY_WITH_WARNINGS" if len(rows) < requested_threads else "READY"
        message = (
            f"{requested_threads}个线程将对{len(rows)}个账号进行受控轮询复用。"
            if len(rows) < requested_threads
            else f"账号数量满足{requested_threads}个线程的独立首轮分配。"
        )

    columns = sorted({key for row in rows for key in row})
    public_allocations = [
        {
            "slot": index,
            "applicant_uid": row.get("applicant_uid", ""),
            "applicant_source": row.get("applicant_source", ""),
            "country_code": row.get("country_code", ""),
            "currency": row.get("currency", ""),
            "proxy_uid": row.get("proxy_uid", ""),
            "proxy_source": row.get("proxy_source", ""),
        }
        for index, row in enumerate(rows, start=1)
    ]
    return {
        "status": status,
        "policy": policy,
        "threads": requested_threads,
        "accounts": len(rows),
        "reuse_ratio": round(requested_threads / len(rows), 2) if rows else None,
        "message": message,
        "rows": rows,
        "columns": columns,
        "allocations": public_allocations,
        "skipped": deepcopy(skipped),
    }


def public_account_pool(pool: dict[str, Any]) -> dict[str, Any]:
    return {
        key: deepcopy(value)
        for key, value in pool.items()
        if key != "rows"
    }
