from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from copy import deepcopy
from pathlib import Path
from typing import Any


_CATEGORIES = ("host", "runtime", "apm", "database", "redis", "middleware")
_DATABASE_COUNTERS = {
    "Questions": "questions",
    "Slow_queries": "slow_queries",
    "Innodb_row_lock_waits": "lock_waits",
    "Innodb_row_lock_time": "lock_wait_time_ms",
    "Connections": "connections",
    "Aborted_connects": "aborted_connects",
}


def describe_observability_configuration(
    manifest: dict[str, Any] | None = None,
    *,
    automatic_categories: tuple[str, ...] = (),
) -> dict[str, Any]:
    manifest = manifest or {}
    configured = {
        str(category).strip().lower()
        for category in automatic_categories
        if str(category).strip().lower() in _CATEGORIES
    }
    sources: list[dict[str, Any]] = [
        {"category": category, "type": "automatic", "status": "CONFIGURED"}
        for category in sorted(configured)
    ]
    for item in manifest.get("performance_observability") or []:
        if not isinstance(item, dict):
            continue
        category = str(item.get("category") or "").strip().lower()
        source_type = str(item.get("type") or "json_file").strip().lower()
        if category not in _CATEGORIES:
            continue
        has_location = bool(
            str(item.get("path") or "").strip()
            if source_type == "json_file"
            else str(item.get("url") or item.get("url_env") or "").strip()
        )
        sources.append({
            "category": category,
            "type": source_type,
            "status": "CONFIGURED" if has_location else "INCOMPLETE",
        })
        if has_location:
            configured.add(category)
    core = {"host", "apm", "database"}
    missing = sorted(core - configured)
    return {
        "status": "COMPLETE" if not missing else "PARTIAL" if configured else "MISSING",
        "configured_categories": sorted(configured),
        "missing_core_categories": missing,
        "sources": sources,
        "statement": (
            "根因证据源已配置齐全，执行后仍会校验实际采集结果。"
            if not missing
            else "运行前只确认证据源配置；未配置分类不会阻断压测，但会限制AI根因定位。"
        ),
    }


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
    except Exception:
        return None


def _resolve(package_root: Path, value: Any) -> Path:
    path = Path(str(value or ""))
    return path if path.is_absolute() else package_root / path


def _nested_value(payload: Any, path: Any) -> Any:
    current = payload
    for part in str(path or "").strip(".").split("."):
        if not part:
            continue
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _read_http_json(item: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    url = str(item.get("url") or os.getenv(str(item.get("url_env") or ""), "")).strip()
    source = {
        "type": "http_json",
        "category": str(item.get("category") or "").lower(),
    }
    if not url:
        return None, {
            **source,
            "status": "MISSING_CONFIGURATION",
            "reason": "未配置url或url_env对应的环境变量。",
        }
    try:
        parsed_url = urllib.parse.urlsplit(url)
        source["endpoint"] = urllib.parse.urlunsplit(
            (parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "")
        )
    except ValueError:
        source["endpoint"] = "invalid-url"
    headers = {"Accept": "application/json"}
    headers_env = str(item.get("headers_env") or "").strip()
    if headers_env:
        try:
            configured_headers = json.loads(os.getenv(headers_env, "{}"))
            if isinstance(configured_headers, dict):
                headers.update({str(key): str(value) for key, value in configured_headers.items()})
        except json.JSONDecodeError:
            return None, {
                **source,
                "status": "INVALID_CONFIGURATION",
                "reason": f"环境变量{headers_env}不是合法JSON对象。",
            }
    timeout = max(1, min(int(item.get("timeout_seconds") or 5), 30))
    try:
        request = urllib.request.Request(url, method="GET", headers=headers)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read(2_000_000).decode("utf-8", "replace"))
        selected = _nested_value(payload, item.get("payload_path")) if item.get("payload_path") else payload
        return selected, {**source, "status": "READY"}
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        return None, {
            **source,
            "status": "FAILED",
            "reason": str(exc)[:300],
        }


def _merge_category(target: dict[str, Any], category: str, payload: Any) -> None:
    if category not in _CATEGORIES or payload in (None, "", [], {}):
        return
    if isinstance(payload, dict):
        target.setdefault(category, {}).update(payload)
    else:
        target[category] = {"samples": payload}


def build_database_status_evidence(
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
    *,
    source: str = "configured_business_database",
) -> dict[str, Any]:
    before = before or {}
    after = after or {}
    if not before and not after:
        return {}
    recognized_values = [
        _number(snapshot.get(name))
        for snapshot in (before, after)
        for name in (
            "Threads_connected",
            "Threads_running",
            *_DATABASE_COUNTERS,
        )
    ]
    if not any(value is not None for value in recognized_values):
        return {}
    evidence: dict[str, Any] = {
        "scope": source,
        "collection": "mysql_global_status_before_after",
        "threads_connected_before": _number(before.get("Threads_connected")),
        "threads_connected_after": _number(after.get("Threads_connected")),
        "threads_running_before": _number(before.get("Threads_running")),
        "threads_running_after": _number(after.get("Threads_running")),
    }
    for mysql_name, output_name in _DATABASE_COUNTERS.items():
        before_value = _number(before.get(mysql_name))
        after_value = _number(after.get(mysql_name))
        evidence[f"{output_name}_before"] = before_value
        evidence[f"{output_name}_after"] = after_value
        evidence[f"{output_name}_delta"] = (
            max(0.0, after_value - before_value)
            if before_value is not None and after_value is not None
            else None
        )
    evidence["slow_query_count"] = evidence.get("slow_queries_delta")
    evidence["lock_wait_count"] = evidence.get("lock_waits_delta")
    evidence["lock_wait_ms_total"] = evidence.get("lock_wait_time_ms_delta")
    return evidence


def collect_observability_evidence(
    package_root: str | Path,
    *,
    options: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
    window_start_ms: int | None = None,
    window_end_ms: int | None = None,
) -> dict[str, Any]:
    root = Path(package_root)
    options = options or {}
    manifest = manifest or {}
    categories: dict[str, Any] = {}
    sources: list[dict[str, Any]] = []

    direct = options.get("observability_evidence")
    if isinstance(direct, dict):
        for category in _CATEGORIES:
            _merge_category(categories, category, direct.get(category))
        sources.append({"type": "runtime_payload", "status": "READY"})

    configured_files = options.get("observability_files")
    if isinstance(configured_files, dict):
        for category, value in configured_files.items():
            path = _resolve(root, value)
            payload = _read_json(path)
            _merge_category(categories, str(category), payload)
            sources.append({
                "type": "json_file",
                "category": str(category),
                "path": str(path),
                "status": "READY" if payload is not None else "MISSING",
            })

    for item in manifest.get("performance_observability") or []:
        if not isinstance(item, dict):
            continue
        source_type = str(item.get("type") or "json_file").lower()
        category = str(item.get("category") or "").lower()
        if category not in _CATEGORIES:
            sources.append({
                "type": source_type,
                "category": category,
                "status": "UNSUPPORTED",
                "reason": "不支持的可观测性分类。",
            })
            continue
        if source_type == "http_json":
            payload, source = _read_http_json(item)
            _merge_category(categories, category, payload)
            sources.append(source)
            continue
        if source_type != "json_file":
            sources.append({
                "type": source_type,
                "category": category,
                "status": "UNSUPPORTED",
                "reason": "当前支持json_file和http_json。",
            })
            continue
        path = _resolve(root, item.get("path"))
        payload = _read_json(path)
        _merge_category(categories, category, payload)
        sources.append({
            "type": source_type,
            "category": category,
            "path": str(path),
            "status": "READY" if payload is not None else "MISSING",
        })

    available = sorted(categories)
    missing = [category for category in ("host", "apm", "database") if category not in categories]
    signals: list[dict[str, Any]] = []

    host = categories.get("host") or {}
    cpu = _number(host.get("cpu_percent_max") or host.get("cpu_max_percent"))
    memory = _number(host.get("memory_percent_max") or host.get("memory_max_percent"))
    if cpu is not None and cpu >= 85:
        signals.append({"category": "host", "severity": "P1", "signal": "cpu_saturation", "value": cpu, "unit": "%"})
    if memory is not None and memory >= 85:
        signals.append({"category": "host", "severity": "P1", "signal": "memory_pressure", "value": memory, "unit": "%"})

    runtime = categories.get("runtime") or {}
    gc_pause = _number(runtime.get("gc_pause_ms_max") or runtime.get("max_gc_pause_ms"))
    if gc_pause is not None and gc_pause >= 500:
        signals.append({"category": "runtime", "severity": "P1", "signal": "long_gc_pause", "value": gc_pause, "unit": "ms"})

    database = categories.get("database") or {}
    slow_queries = _number(database.get("slow_queries") or database.get("slow_query_count"))
    lock_wait = _number(
        database.get("lock_wait_ms_max")
        or database.get("max_lock_wait_ms")
        or database.get("lock_wait_ms_total")
    )
    lock_wait_count = _number(database.get("lock_wait_count"))
    aborted_connects = _number(database.get("aborted_connects_delta"))
    if slow_queries is not None and slow_queries > 0:
        signals.append({"category": "database", "severity": "P1", "signal": "slow_queries", "value": slow_queries, "unit": "count"})
    if lock_wait is not None and lock_wait >= 200:
        signals.append({"category": "database", "severity": "P1", "signal": "lock_wait", "value": lock_wait, "unit": "ms"})
    if lock_wait_count is not None and lock_wait_count > 0 and not lock_wait:
        signals.append({"category": "database", "severity": "P1", "signal": "lock_waits", "value": lock_wait_count, "unit": "count"})
    if aborted_connects is not None and aborted_connects > 0:
        signals.append({"category": "database", "severity": "P1", "signal": "aborted_connects", "value": aborted_connects, "unit": "count"})

    apm = categories.get("apm") or {}
    apm_error_rate = _number(apm.get("error_rate") or apm.get("error_rate_percent"))
    if apm_error_rate is not None and apm_error_rate > 1:
        signals.append({"category": "apm", "severity": "P1", "signal": "application_errors", "value": apm_error_rate, "unit": "%"})

    return {
        "schema_version": "1.0",
        "status": "COMPLETE" if not missing else "PARTIAL" if available else "MISSING",
        "window": {"start_ms": window_start_ms, "end_ms": window_end_ms},
        "available_categories": available,
        "missing_core_categories": missing,
        "sources": sources,
        "categories": categories,
        "signals": signals,
        "statement": (
            "已取得与本次JTL窗口关联的外部性能证据。"
            if available
            else "当前没有外部监控证据，AI只能给出待验证的瓶颈假设。"
        ),
    }


def attach_observability_to_diagnosis(
    diagnosis: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    result = deepcopy(diagnosis or {})
    result["observability"] = evidence
    boundary = result.setdefault("evidence_boundary", {})
    available = set(evidence.get("available_categories") or [])
    category_labels = {
        "host": "应用CPU/内存/GC",
        "runtime": "应用CPU/内存/GC",
        "database": "数据库等待",
        "redis": "Redis命中率",
        "middleware": "中间件积压",
        "apm": "应用日志/APM",
    }
    required = list(boundary.get("requires_external_evidence") or [])
    boundary["requires_external_evidence"] = [
        item for item in required
        if not any(category_labels.get(category) == item for category in available)
    ]
    boundary["available_external_evidence"] = sorted(available)
    signals = evidence.get("signals") or []
    if signals:
        result["bottleneck_hypotheses"] = [
            {
                "scope": signal.get("category"),
                "confidence": "medium",
                "reason": f"同一运行窗口检测到 {signal.get('signal')}={signal.get('value')}{signal.get('unit') or ''}，需要结合调用链继续确认因果关系。",
                "required_evidence": ["对应时间点的调用链、日志或SQL明细"],
            }
            for signal in signals[:8]
        ]
        result.setdefault("findings", []).extend({
            "severity": signal.get("severity") or "P1",
            "title": f"外部监控信号：{signal.get('signal')}",
            "detail": f"{signal.get('category')} 在本次窗口记录为 {signal.get('value')}{signal.get('unit') or ''}。",
        } for signal in signals[:8])
    return result
