from __future__ import annotations

import re
import json
from collections import defaultdict, deque
from typing import Any


def _values(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, (list, tuple, set)):
        return {str(item).strip().lower() for item in value if str(item).strip()}
    text = str(value).strip()
    if not text:
        return set()
    return {item.strip().lower() for item in re.split(r"[,;\n，；]+", text) if item.strip()}


def _case_text(case: dict[str, Any]) -> str:
    parts = [
        case.get("id"), case.get("title"), case.get("requirement_ref"), case.get("business_goal"),
        case.get("scenario_id"), case.get("scenario_type"), case.get("method"), case.get("path"),
        case.get("actors"), case.get("account_slots"), case.get("preconditions"), case.get("steps"),
        case.get("expected_results"), case.get("state_path"), case.get("required_variables"),
    ]
    return "\n".join(str(part or "") for part in parts).lower()


def _evidence_tokens(case: dict[str, Any]) -> tuple[set[str], set[str]]:
    tables = {
        str(check.get("table") or "").strip().lower()
        for check in case.get("db_checks") or []
        if isinstance(check, dict) and str(check.get("table") or "").strip()
    }
    keys = {
        str(check.get("key") or "").strip().lower()
        for check in case.get("redis_checks") or []
        if isinstance(check, dict) and str(check.get("key") or "").strip()
    }
    return tables, keys


def _scope(payload: dict[str, Any]) -> dict[str, set[str]]:
    aliases = {
        "case_ids": ("case_ids",),
        "requirements": ("requirements", "changed_requirements", "requirement_refs"),
        "endpoints": ("endpoints", "changed_endpoints", "paths"),
        "tables": ("tables", "changed_tables", "db_tables"),
        "redis_keys": ("redis_keys", "changed_redis_keys"),
        "roles": ("roles", "changed_roles"),
        "states": ("states", "changed_states"),
        "keywords": ("keywords", "business_keywords"),
    }
    source = payload.get("change_scope") if isinstance(payload.get("change_scope"), dict) else payload
    result: dict[str, set[str]] = {}
    for target, names in aliases.items():
        result[target] = set()
        for name in names:
            result[target].update(_values(source.get(name)))
    return result


def _operation_map(document: Any) -> dict[str, str]:
    if not isinstance(document, dict):
        return {}
    operations: dict[str, str] = {}
    for path, path_item in (document.get("paths") or {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if str(method).lower() not in {"get", "post", "put", "patch", "delete", "head", "options"}:
                continue
            operations[f"{str(method).upper()} {path}"] = json.dumps(operation or {}, ensure_ascii=False, sort_keys=True)
    return operations


def _metadata_names(value: Any, collection_keys: tuple[str, ...], name_keys: tuple[str, ...]) -> set[str]:
    if not value:
        return set()
    if isinstance(value, dict):
        for key in collection_keys:
            if key in value:
                return _metadata_names(value.get(key), collection_keys, name_keys)
        if any(key in value for key in name_keys):
            return {str(next((value.get(key) for key in name_keys if value.get(key)), "")).strip().lower()}
        return {str(key).strip().lower() for key in value if str(key).strip()}
    if isinstance(value, (list, tuple, set)):
        names: set[str] = set()
        for item in value:
            if isinstance(item, dict):
                name = next((item.get(key) for key in name_keys if item.get(key)), "")
                if name:
                    names.add(str(name).strip().lower())
            elif str(item).strip():
                names.add(str(item).strip().lower())
        return names
    return _values(value)


def _changed_requirement_tokens(current: str, baseline: str) -> tuple[set[str], set[str]]:
    current_lines = {line.strip() for line in str(current or "").splitlines() if line.strip()}
    baseline_lines = {line.strip() for line in str(baseline or "").splitlines() if line.strip()}
    changed_text = "\n".join(sorted(current_lines.symmetric_difference(baseline_lines)))
    requirement_ids = {item.lower() for item in re.findall(r"\b(?:REQ|US|STORY|需求)[-_ ]?[A-Z0-9]+\b", changed_text, re.I)}
    keywords = {
        item.lower() for item in re.findall(r"[\u4e00-\u9fff]{2,12}|[A-Za-z][A-Za-z0-9_-]{2,30}", changed_text)
        if item.lower() not in {"http", "https", "string", "object", "array", "true", "false"}
    }
    return requirement_ids, set(sorted(keywords)[:40])


def infer_change_scope(sources: dict[str, Any] | None = None) -> dict[str, Any]:
    sources = sources or {}
    scope = {key: set() for key in ("case_ids", "requirements", "endpoints", "tables", "redis_keys", "roles", "states", "keywords")}
    evidence = []
    warnings = []

    current_openapi = sources.get("current_openapi")
    baseline_openapi = sources.get("baseline_openapi")
    current_operations = _operation_map(current_openapi)
    baseline_operations = _operation_map(baseline_openapi)
    if current_operations:
        if baseline_openapi:
            changed = {
                key for key in set(current_operations) | set(baseline_operations)
                if current_operations.get(key) != baseline_operations.get(key)
            }
            scope["endpoints"].update(changed)
            evidence.append({"source": "openapi", "mode": "diff", "changed": len(changed)})
        else:
            scope["endpoints"].update(current_operations)
            warnings.append("OpenAPI没有上一版，首次按全部接口建立回归范围。")
            evidence.append({"source": "openapi", "mode": "initial_full", "changed": len(current_operations)})

    current_requirement = str(sources.get("current_requirement") or "")
    baseline_requirement = str(sources.get("baseline_requirement") or "")
    if current_requirement and baseline_requirement:
        requirement_ids, keywords = _changed_requirement_tokens(current_requirement, baseline_requirement)
        scope["requirements"].update(requirement_ids)
        scope["keywords"].update(keywords)
        evidence.append({"source": "requirement", "mode": "diff", "changed": len(requirement_ids) + len(keywords)})
    elif current_requirement:
        warnings.append("需求文档没有可比较的上一版，未凭空推断需求变更。")

    for source_name, target, collection_keys, name_keys in (
        ("db_metadata", "tables", ("tables", "entities"), ("table", "table_name", "name")),
        ("redis_metadata", "redis_keys", ("keys", "patterns", "items"), ("key", "key_pattern", "name")),
    ):
        current = _metadata_names(sources.get(f"current_{source_name}"), collection_keys, name_keys)
        baseline = _metadata_names(sources.get(f"baseline_{source_name}"), collection_keys, name_keys)
        if current and sources.get(f"baseline_{source_name}") is not None:
            changed = current.symmetric_difference(baseline)
            scope[target].update(changed)
            evidence.append({"source": source_name, "mode": "diff", "changed": len(changed)})
        elif current:
            warnings.append(f"{source_name}没有上一版，未将全部元数据误判为业务变更。")

    return {
        "change_scope": {key: sorted(value) for key, value in scope.items()},
        "evidence": evidence,
        "warnings": warnings,
        "has_changes": any(scope.values()),
    }


def select_regression_cases(structured: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    source_cases = [case for case in structured.get("cases") or [] if isinstance(case, dict)]
    lifecycle_statuses = _values(payload.get("lifecycle_statuses") or ["ACTIVE"])
    cases = [
        case for case in source_cases
        if str(case.get("lifecycle_status") or "ACTIVE").strip().lower() in lifecycle_statuses
    ]
    scope = _scope(payload)
    has_scope = any(scope.values())
    if not has_scope:
        return {
            "schema_version": "1.0",
            "report_type": "REQUIREMENT_REGRESSION_SELECTION",
            "status": "BLOCKED",
            "change_scope": {key: sorted(value) for key, value in scope.items()},
            "summary": {"source_cases": len(source_cases), "eligible_cases": len(cases), "selected": 0, "direct": 0, "related": 0},
            "selected_cases": [],
            "message": "未提供变更范围，平台不会无依据地自动选择回归用例。",
        }

    reasons: dict[str, list[str]] = defaultdict(list)
    case_by_id = {str(case.get("id") or ""): case for case in cases if str(case.get("id") or "")}
    for case_id, case in case_by_id.items():
        text = _case_text(case)
        method_path = f"{str(case.get('method') or '').lower()} {str(case.get('path') or '').lower()}".strip()
        tables, redis_keys = _evidence_tokens(case)
        if case_id.lower() in scope["case_ids"]:
            reasons[case_id].append("直接指定用例")
        for value in scope["requirements"]:
            if value in text:
                reasons[case_id].append(f"命中需求变更：{value}")
        for value in scope["endpoints"]:
            if value == str(case.get("path") or "").lower() or value in method_path:
                reasons[case_id].append(f"命中接口变更：{value}")
        for value in scope["tables"]:
            if value in tables:
                reasons[case_id].append(f"命中数据库表变更：{value}")
        for value in scope["redis_keys"]:
            if any(value == key or value in key or key in value for key in redis_keys):
                reasons[case_id].append(f"命中Redis变更：{value}")
        for value in scope["roles"]:
            if value in text:
                reasons[case_id].append(f"命中角色变更：{value}")
        for value in scope["states"]:
            if value in text:
                reasons[case_id].append(f"命中状态变更：{value}")
        for value in scope["keywords"]:
            if value in text:
                reasons[case_id].append(f"命中业务关键词：{value}")

    direct_ids = set(reasons)
    related_ids: set[str] = set()
    if payload.get("include_related", True) and direct_ids:
        indexes: dict[tuple[str, str], set[str]] = defaultdict(set)
        for case_id, case in case_by_id.items():
            for ref in _values(case.get("requirement_ref")):
                indexes[("requirement", ref)].add(case_id)
            path = str(case.get("path") or "").strip().lower()
            if path:
                indexes[("path", path)].add(case_id)
            scenario_id = str(case.get("scenario_id") or "").strip().lower()
            if scenario_id:
                indexes[("scenario", scenario_id)].add(case_id)
            for rule_id in _values((case.get("traceability") or {}).get("evidence_rules") or case.get("evidence_rule_ids")):
                indexes[("evidence", rule_id)].add(case_id)
        queue = deque(direct_ids)
        visited = set(direct_ids)
        while queue:
            source_id = queue.popleft()
            source = case_by_id[source_id]
            keys = []
            keys.extend(("requirement", value) for value in _values(source.get("requirement_ref")))
            path = str(source.get("path") or "").strip().lower()
            if path:
                keys.append(("path", path))
            scenario_id = str(source.get("scenario_id") or "").strip().lower()
            if scenario_id:
                keys.append(("scenario", scenario_id))
            keys.extend(("evidence", value) for value in _values((source.get("traceability") or {}).get("evidence_rules") or source.get("evidence_rule_ids")))
            for key in keys:
                for candidate_id in indexes.get(key, set()):
                    if candidate_id in visited:
                        continue
                    visited.add(candidate_id)
                    related_ids.add(candidate_id)
                    reasons[candidate_id].append(f"关联影响：共享{key[0]} {key[1]}")
                    queue.append(candidate_id)

    if payload.get("include_critical", True):
        for case_id, case in case_by_id.items():
            if str(case.get("priority") or "").upper() == "P0" and case_id not in reasons:
                reasons[case_id].append("关键路径保护：P0")
                related_ids.add(case_id)

    selected = []
    for case in cases:
        case_id = str(case.get("id") or "")
        if case_id not in reasons:
            continue
        selected.append({
            "case_id": case_id,
            "title": case.get("title"),
            "priority": case.get("priority"),
            "lifecycle_status": str(case.get("lifecycle_status") or "ACTIVE").upper(),
            "scenario_id": case.get("scenario_id"),
            "method": case.get("method"),
            "path": case.get("path"),
            "selection_type": "DIRECT" if case_id in direct_ids else "RELATED",
            "reasons": list(dict.fromkeys(reasons[case_id])),
            "automation_readiness": case.get("automation_readiness") or case.get("automation_status"),
            "recommended_tool": case.get("coverage_tool") or (case.get("automation") or {}).get("recommended_tools"),
        })
    max_cases = int(payload.get("max_cases") or 0)
    truncated = max_cases > 0 and len(selected) > max_cases
    if truncated:
        selected = selected[:max_cases]
    return {
        "schema_version": "1.0",
        "report_type": "REQUIREMENT_REGRESSION_SELECTION",
        "status": "READY_WITH_WARNINGS" if truncated else "READY",
        "change_scope": {key: sorted(value) for key, value in scope.items()},
        "selection_policy": {"include_related": payload.get("include_related", True), "include_critical": payload.get("include_critical", True), "lifecycle_statuses": sorted(status.upper() for status in lifecycle_statuses), "max_cases": max_cases},
        "summary": {
            "source_cases": len(source_cases),
            "eligible_cases": len(cases),
            "selected": len(selected),
            "direct": sum(item["selection_type"] == "DIRECT" for item in selected),
            "related": sum(item["selection_type"] == "RELATED" for item in selected),
            "truncated": truncated,
        },
        "selected_cases": selected,
    }
