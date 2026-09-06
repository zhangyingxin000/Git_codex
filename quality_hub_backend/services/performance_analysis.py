from __future__ import annotations

import csv
import math
import re
import statistics
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable


PROFILE_ALIASES = {
    "stability": "soak",
    "concurrent": "concurrency",
}

PROFILE_THRESHOLDS = {
    "smoke": {
        "label": "冒烟验证",
        "max_error_rate": 0.0,
        "max_p95_ms": 3000.0,
        "max_p99_ms": 5000.0,
        "min_throughput_rps": 0.0,
    },
    "baseline": {
        "label": "基准测试",
        "max_error_rate": 1.0,
        "max_p95_ms": 1500.0,
        "max_p99_ms": 2500.0,
        "min_throughput_rps": 1.0,
    },
    "load": {
        "label": "负载测试",
        "max_error_rate": 1.0,
        "max_p95_ms": 2000.0,
        "max_p99_ms": 3500.0,
        "min_throughput_rps": 5.0,
    },
    "concurrency": {
        "label": "并发测试",
        "max_error_rate": 1.0,
        "max_p95_ms": 2000.0,
        "max_p99_ms": 3500.0,
        "min_throughput_rps": 0.0,
    },
    "spike": {
        "label": "突增测试",
        "max_error_rate": 2.0,
        "max_p95_ms": 3000.0,
        "max_p99_ms": 5000.0,
        "min_throughput_rps": 0.0,
    },
    "stress": {
        "label": "压力测试",
        "max_error_rate": 5.0,
        "max_p95_ms": 5000.0,
        "max_p99_ms": 8000.0,
        "min_throughput_rps": 0.0,
    },
    "soak": {
        "label": "稳定性测试",
        "max_error_rate": 0.5,
        "max_p95_ms": 2000.0,
        "max_p99_ms": 4000.0,
        "min_throughput_rps": 2.0,
    },
}


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def percentile(values: Iterable[Any], requested: float) -> float:
    numbers = sorted(_number(value) for value in values if value not in (None, ""))
    if not numbers:
        return 0.0
    index = (len(numbers) - 1) * requested / 100
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return round(numbers[int(index)], 2)
    return round(numbers[lower] + (numbers[upper] - numbers[lower]) * (index - lower), 2)


def classify_error(sample: dict[str, Any]) -> tuple[str, str]:
    code = str(sample.get("responseCode") or "UNKNOWN")
    message = " ".join(str(sample.get(key) or "") for key in ("responseMessage", "failureMessage"))
    lowered = f"{code} {message}".lower()
    if code in {"401", "403"}:
        return "authentication", "鉴权失败"
    if "connecttimeoutexception" in lowered or "connect timed out" in lowered:
        return "connect_timeout", "连接超时"
    if "sockettimeoutexception" in lowered or "read timed out" in lowered:
        return "read_timeout", "读取超时"
    if "socketexception" in lowered or "connection reset" in lowered:
        return "connection_reset", "连接被重置"
    if "unknownhost" in lowered or "name or service not known" in lowered:
        return "dns", "DNS解析失败"
    if code.isdigit() and 500 <= int(code) <= 599:
        return "http_5xx", "服务端HTTP 5xx"
    if code.isdigit() and 400 <= int(code) <= 499:
        return "http_4xx", "客户端或业务HTTP 4xx"
    if str(sample.get("failureMessage") or "").strip():
        return "assertion", "断言失败"
    return "other", "其他失败"


def _read_csv_samples(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_xml_samples(path: Path) -> list[dict[str, Any]]:
    root = ET.parse(path).getroot()
    samples: list[dict[str, Any]] = []
    for element in root.iter():
        if element.tag not in {"httpSample", "sample"}:
            continue
        samples.append({
            "timeStamp": element.get("ts", ""),
            "elapsed": element.get("t", ""),
            "label": element.get("lb", ""),
            "responseCode": element.get("rc", ""),
            "responseMessage": element.get("rm", ""),
            "success": element.get("s", ""),
            "failureMessage": "",
            "latency": element.get("lt", ""),
            "connect": element.get("ct", ""),
            "bytes": element.get("by", ""),
            "sentBytes": element.get("sby", ""),
            "allThreads": element.get("na", ""),
            "grpThreads": element.get("ng", ""),
            "threadName": element.get("tn", ""),
            "URL": element.findtext("java.net.URL", default=""),
        })
    return samples


def read_jtl_samples(jtl_path: str | Path) -> tuple[list[dict[str, Any]], str]:
    path = Path(jtl_path)
    if not path.is_file():
        return [], "missing"
    head = path.read_text(encoding="utf-8-sig", errors="replace")[:200].lstrip()
    if head.startswith("<"):
        return _read_xml_samples(path), "xml"
    return _read_csv_samples(path), "csv"


def _automatic_stop_artifact(sample: dict[str, Any]) -> bool:
    if str(sample.get("success") or "").lower() == "true":
        return False
    text = " ".join(
        str(sample.get(key) or "")
        for key in ("responseCode", "responseMessage", "failureMessage")
    ).lower()
    return (
        "socketexception" in text and "socket closed" in text
        or "interruptedexception" in text
        or "test stopped" in text
    )


def _sample_account_identity(sample: dict[str, Any]) -> tuple[str, str]:
    direct_fields = (
        ("applicant_uid", "applicant"),
        ("anchorUid", "applicant"),
        ("proxy_uid", "proxy"),
        ("proxyUid", "proxy"),
        ("agentUid", "proxy"),
        ("uid", ""),
    )
    for field, role in direct_fields:
        value = str(sample.get(field) or "").strip()
        if value:
            return value, role

    url = str(sample.get("URL") or sample.get("url") or "").strip()
    if not url:
        return "", ""
    try:
        parsed = urllib.parse.urlsplit(url)
        query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    except ValueError:
        return "", ""
    lowered = {str(key).lower(): values for key, values in query.items()}
    proxy_side = "/salary/trade/agent/" in parsed.path.lower()
    candidates = (
        (
            ("proxy_uid", "proxy"),
            ("proxyuid", "proxy"),
            ("agentuid", "proxy"),
            ("uid", "proxy"),
            ("applicant_uid", "applicant"),
            ("anchoruid", "applicant"),
        )
        if proxy_side
        else (
            ("applicant_uid", "applicant"),
            ("anchoruid", "applicant"),
            ("uid", "applicant"),
            ("proxy_uid", "proxy"),
            ("proxyuid", "proxy"),
            ("agentuid", "proxy"),
        )
    )
    for field, role in candidates:
        values = lowered.get(field) or []
        value = str(values[0] if values else "").strip()
        if value:
            return value, role
    return "", ""


def summarize_account_usage(
    samples: Iterable[dict[str, Any]],
    allocations: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    identity_index: dict[str, dict[str, str]] = {}
    allocation_by_slot: dict[int, dict[str, Any]] = {}
    for allocation in allocations or ():
        if not isinstance(allocation, dict):
            continue
        try:
            slot = int(allocation.get("slot") or 0)
        except (TypeError, ValueError):
            slot = 0
        if slot > 0:
            allocation_by_slot[slot] = allocation
        for role in ("applicant", "proxy"):
            uid = str(allocation.get(f"{role}_uid") or "").strip()
            if not uid:
                continue
            identity_index.setdefault(uid, {
                "role": role,
                "source": str(allocation.get(f"{role}_source") or "").strip(),
            })

    threads: dict[str, dict[str, Any]] = {}
    tracked_requests = 0
    untracked_requests = 0
    allocation_inferred_requests = 0
    for sample in samples:
        thread_name = str(
            sample.get("threadName")
            or sample.get("thread_name")
            or "unknown-thread"
        ).strip() or "unknown-thread"
        uid, hinted_role = _sample_account_identity(sample)
        identity_mode = "jtl"
        if not uid and allocation_by_slot:
            thread_match = re.search(r"(?:^|\s)(\d+)-(\d+)$", thread_name)
            slot = int(thread_match.group(2)) if thread_match else 0
            allocation = allocation_by_slot.get(slot)
            if allocation:
                url = str(sample.get("URL") or sample.get("url") or "")
                try:
                    proxy_side = "/salary/trade/agent/" in urllib.parse.urlsplit(url).path.lower()
                except ValueError:
                    proxy_side = False
                hinted_role = "proxy" if proxy_side else "applicant"
                uid = str(allocation.get(f"{hinted_role}_uid") or "").strip()
                if uid:
                    identity_mode = "thread_allocation"
                    allocation_inferred_requests += 1
        if not uid:
            untracked_requests += 1
            continue
        tracked_requests += 1
        metadata = identity_index.get(uid) or {}
        role = hinted_role or str(metadata.get("role") or "unknown")
        source = str(metadata.get("source") or "runtime_account_pool")
        thread = threads.setdefault(thread_name, {
            "thread_name": thread_name,
            "requests": 0,
            "errors": 0,
            "rotation_count": 0,
            "accounts": {},
            "uid_sequence": [],
        })
        thread["requests"] += 1
        failed = str(sample.get("success") or "").lower() != "true"
        if failed:
            thread["errors"] += 1
        if not thread["uid_sequence"] or thread["uid_sequence"][-1] != uid:
            if thread["uid_sequence"]:
                thread["rotation_count"] += 1
            thread["uid_sequence"].append(uid)
        account_key = f"{role}:{uid}"
        account = thread["accounts"].setdefault(account_key, {
            "role": role,
            "uid": uid,
            "source": source,
            "identity_mode": identity_mode,
            "requests": 0,
            "errors": 0,
        })
        account["requests"] += 1
        if failed:
            account["errors"] += 1

    by_thread: list[dict[str, Any]] = []
    unique_accounts: set[str] = set()
    total_rotations = 0
    for thread in threads.values():
        accounts = list(thread.pop("accounts").values())
        sequence = list(thread.pop("uid_sequence"))
        unique_accounts.update(f"{item['role']}:{item['uid']}" for item in accounts)
        total_rotations += int(thread["rotation_count"])
        by_thread.append({**thread, "uid_sequence": sequence, "accounts": accounts})
    by_thread.sort(key=lambda item: item["thread_name"])
    if tracked_requests and not untracked_requests:
        status = (
            "TRACKED_BY_ALLOCATION"
            if allocation_inferred_requests == tracked_requests
            else "TRACKED_MIXED"
            if allocation_inferred_requests
            else "TRACKED"
        )
    else:
        status = "PARTIAL" if tracked_requests else "UNAVAILABLE"
    return {
        "status": status,
        "threads": len(by_thread),
        "unique_accounts": len(unique_accounts),
        "tracked_requests": tracked_requests,
        "untracked_requests": untracked_requests,
        "allocation_inferred_requests": allocation_inferred_requests,
        "rotation_count": total_rotations,
        "by_thread": by_thread,
        "privacy": "仅记录UID、角色和数据来源，不记录ticket、token或密码。",
    }


def summarize_jtl(
    jtl_path: str | Path,
    warmup_samples_per_label: int = 0,
    account_allocations: Iterable[dict[str, Any]] = (),
    exclude_automatic_stop_artifacts: bool = False,
    include_transaction_metrics: bool = True,
) -> dict[str, Any]:
    samples, source_format = read_jtl_samples(jtl_path)
    raw_samples = len(samples)
    raw_transaction_samples = sum(
        str(sample.get("label") or "").startswith(("TX::", "TRANSACTION::"))
        for sample in samples
    )
    raw_requests = raw_samples - raw_transaction_samples
    automatic_stop_samples = (
        [sample for sample in samples if _automatic_stop_artifact(sample)]
        if exclude_automatic_stop_artifacts
        else []
    )
    if automatic_stop_samples:
        excluded_ids = {id(sample) for sample in automatic_stop_samples}
        samples = [sample for sample in samples if id(sample) not in excluded_ids]
    warmup_limit = max(0, int(warmup_samples_per_label or 0))
    warmup_samples: list[dict[str, Any]] = []
    if samples and warmup_limit:
        measured_samples: list[dict[str, Any]] = []
        label_totals: dict[str, int] = {}
        for sample in samples:
            label = str(sample.get("label") or "未命名请求")
            label_totals[label] = label_totals.get(label, 0) + 1
        warmup_by_label = {
            label: min(warmup_limit, max(0, total - 1))
            for label, total in label_totals.items()
        }
        label_counts: dict[str, int] = {}
        for sample in samples:
            label = str(sample.get("label") or "未命名请求")
            seen = label_counts.get(label, 0)
            label_counts[label] = seen + 1
            if seen < warmup_by_label[label]:
                warmup_samples.append(sample)
            else:
                measured_samples.append(sample)
        samples = measured_samples
    observed_transaction_samples = [
        sample for sample in samples
        if str(sample.get("label") or "").startswith(("TX::", "TRANSACTION::"))
    ]
    measured_transaction_samples = (
        observed_transaction_samples if include_transaction_metrics else []
    )
    request_samples = [
        sample for sample in samples
        if not str(sample.get("label") or "").startswith(("TX::", "TRANSACTION::"))
    ]
    account_usage = summarize_account_usage(request_samples, account_allocations)
    samples = request_samples or samples
    if not samples:
        return {
            "requests": 0,
            "raw_requests": raw_requests,
            "raw_samples": raw_samples,
            "measured_requests": 0,
            "observed_transaction_samples": len(observed_transaction_samples),
            "transaction_samples": len(measured_transaction_samples),
            "transaction_throughput_tps": 0.0 if measured_transaction_samples else None,
            "measurement_mode": (
                "business_transaction" if include_transaction_metrics else "request_only"
            ),
            "warmup_samples_excluded": len(warmup_samples),
            "warmup_errors": sum(
                str(item.get("success") or "").lower() != "true"
                for item in warmup_samples
            ),
            "automatic_stop_samples_excluded": len(automatic_stop_samples),
            "automatic_stop_errors_excluded": len(automatic_stop_samples),
            "errors": 0,
            "error_rate": 100.0,
            "response_codes": {},
            "failed_labels": [],
            "source_format": source_format,
            "duration_seconds": 0.0,
            "account_usage": account_usage,
            "measurement_policy": {
                "warmup_samples_per_label": warmup_limit,
                "raw_jtl_preserved": True,
                "retain_at_least_one_sample_per_label": True,
            },
        }

    elapsed_values: list[float] = []
    latency_values: list[float] = []
    connect_values: list[float] = []
    starts: list[float] = []
    ends: list[float] = []
    active_threads: list[float] = []
    errors: list[dict[str, Any]] = []
    failed_labels: list[str] = []
    response_codes: dict[str, int] = {}
    label_groups: dict[str, dict[str, Any]] = {}
    slow_samples: list[dict[str, Any]] = []
    error_categories: dict[str, dict[str, Any]] = {}
    total_bytes = 0.0
    sent_bytes = 0.0

    for sample in samples:
        code = str(sample.get("responseCode") or "UNKNOWN")
        response_codes[code] = response_codes.get(code, 0) + 1
        elapsed = _number(sample.get("elapsed"))
        latency = _number(sample.get("Latency") or sample.get("latency"))
        connect = _number(sample.get("Connect") or sample.get("connect"))
        started = _number(sample.get("timeStamp"))
        elapsed_values.append(elapsed)
        if latency:
            latency_values.append(latency)
        if connect:
            connect_values.append(connect)
        if started:
            starts.append(started)
            ends.append(started + elapsed)
        active = _number(sample.get("allThreads") or sample.get("grpThreads"))
        if active:
            active_threads.append(active)
        total_bytes += _number(sample.get("bytes"))
        sent_bytes += _number(sample.get("sentBytes"))

        label = str(sample.get("label") or "未命名请求")
        success = str(sample.get("success") or "").lower() == "true"
        group = label_groups.setdefault(label, {"elapsed": [], "errors": 0})
        group["elapsed"].append(elapsed)
        if not success:
            group["errors"] += 1
        slow_samples.append({
            "label": label,
            "elapsed_ms": elapsed,
            "response_code": code,
            "success": success,
        })

        if success:
            continue
        errors.append(sample)
        failed_labels.append(f"{label}({code})")
        category, category_label = classify_error(sample)
        record = error_categories.setdefault(category, {
            "category": category,
            "label": category_label,
            "count": 0,
            "response_codes": set(),
            "examples": set(),
        })
        record["count"] += 1
        record["response_codes"].add(code)
        example = str(sample.get("responseMessage") or sample.get("failureMessage") or "").strip()
        if example:
            record["examples"].add(example[:300])

    duration_seconds = 0.0
    if starts and ends:
        duration_seconds = max((max(ends) - min(starts)) / 1000, 0.001)

    transaction_elapsed = [_number(item.get("elapsed")) for item in measured_transaction_samples]
    transaction_starts = [_number(item.get("timeStamp")) for item in measured_transaction_samples if _number(item.get("timeStamp"))]
    transaction_ends = [
        _number(item.get("timeStamp")) + _number(item.get("elapsed"))
        for item in measured_transaction_samples
        if _number(item.get("timeStamp"))
    ]
    transaction_duration = (
        max((max(transaction_ends) - min(transaction_starts)) / 1000, 0.001)
        if transaction_starts and transaction_ends else 0.0
    )
    transaction_errors = sum(
        str(item.get("success") or "").lower() != "true"
        for item in measured_transaction_samples
    )

    by_label = []
    for label, group in label_groups.items():
        values = group["elapsed"]
        count = len(values)
        label_errors = int(group["errors"])
        by_label.append({
            "label": label,
            "samples": count,
            "errors": label_errors,
            "error_rate": round(label_errors / count * 100, 2) if count else 0.0,
            "average_ms": round(statistics.mean(values), 2) if values else 0.0,
            "min_ms": round(min(values), 2) if values else 0.0,
            "max_ms": round(max(values), 2) if values else 0.0,
            "p90_ms": percentile(values, 90),
            "p95_ms": percentile(values, 95),
            "p99_ms": percentile(values, 99),
            "throughput_rps": round(count / duration_seconds, 2) if duration_seconds else 0.0,
        })
    by_label.sort(key=lambda item: (item["p95_ms"], item["max_ms"]), reverse=True)

    average_ms = round(statistics.mean(elapsed_values), 2) if elapsed_values else 0.0
    p95_ms = percentile(elapsed_values, 95)
    return {
        "requests": len(samples),
        "raw_requests": raw_requests,
        "raw_samples": raw_samples,
        "measured_requests": len(samples),
        "warmup_samples_excluded": len(warmup_samples),
        "warmup_errors": sum(
            str(item.get("success") or "").lower() != "true"
            for item in warmup_samples
        ),
        "automatic_stop_samples_excluded": len(automatic_stop_samples),
        "automatic_stop_errors_excluded": len(automatic_stop_samples),
        "errors": len(errors),
        "error_rate": round(len(errors) / len(samples) * 100, 2),
        "response_codes": response_codes,
        "error_categories": [
            {
                **record,
                "response_codes": sorted(record["response_codes"]),
                "examples": sorted(record["examples"])[:3],
            }
            for record in sorted(error_categories.values(), key=lambda item: item["count"], reverse=True)
        ],
        "failed_labels": failed_labels[:20],
        "average_ms": average_ms,
        "min_ms": round(min(elapsed_values), 2) if elapsed_values else 0.0,
        "max_ms": round(max(elapsed_values), 2) if elapsed_values else 0.0,
        "p50_ms": percentile(elapsed_values, 50),
        "p90_ms": percentile(elapsed_values, 90),
        "p95_ms": p95_ms,
        "p99_ms": percentile(elapsed_values, 99),
        "stddev_ms": round(statistics.pstdev(elapsed_values), 2) if len(elapsed_values) > 1 else 0.0,
        "average_latency_ms": round(statistics.mean(latency_values), 2) if latency_values else 0.0,
        "average_connect_ms": round(statistics.mean(connect_values), 2) if connect_values else 0.0,
        "duration_seconds": round(duration_seconds, 3),
        "window_start_ms": int(min(starts)) if starts else None,
        "window_end_ms": int(max(ends)) if ends else None,
        "throughput_rps": round(len(samples) / duration_seconds, 2) if duration_seconds else 0.0,
        "request_throughput_rps": round(len(samples) / duration_seconds, 2) if duration_seconds else 0.0,
        "observed_transaction_samples": len(observed_transaction_samples),
        "transaction_samples": len(measured_transaction_samples),
        "transaction_errors": transaction_errors,
        "transaction_error_rate": round(transaction_errors / len(measured_transaction_samples) * 100, 2) if measured_transaction_samples else None,
        "transaction_average_ms": round(statistics.mean(transaction_elapsed), 2) if transaction_elapsed else None,
        "transaction_p95_ms": percentile(transaction_elapsed, 95) if transaction_elapsed else None,
        "transaction_p99_ms": percentile(transaction_elapsed, 99) if transaction_elapsed else None,
        "transaction_throughput_tps": round(len(measured_transaction_samples) / transaction_duration, 2) if transaction_duration else None,
        "measurement_mode": (
            "business_transaction" if include_transaction_metrics else "request_only"
        ),
        "throughput_semantics": "RPS只统计HTTP请求采样；TPS只统计TX::/TRANSACTION::业务事务父采样。",
        "transaction_note": (
            "当前预案未选择有效的多步业务事务，即使JTL中存在旧的TX父采样也不计算TPS。"
            if observed_transaction_samples and not include_transaction_metrics
            else ""
        ),
        "received_kbps": round(total_bytes / 1024 / duration_seconds, 2) if duration_seconds else 0.0,
        "sent_kbps": round(sent_bytes / 1024 / duration_seconds, 2) if duration_seconds else 0.0,
        "active_threads_peak": int(max(active_threads)) if active_threads else 0,
        "account_usage": account_usage,
        "slowest_samples": sorted(slow_samples, key=lambda item: item["elapsed_ms"], reverse=True)[:10],
        "by_label": by_label[:50],
        "source_format": source_format,
        "measurement_policy": {
            "warmup_samples_per_label": warmup_limit,
            "raw_jtl_preserved": True,
            "retain_at_least_one_sample_per_label": True,
            "automatic_stop_artifacts_excluded": bool(automatic_stop_samples),
            "note": "原始JTL和JMeter HTML保留全部样本；平台阈值只评估排除预热后的测量样本。",
        },
        "evidence_scope": {
            "confirmed": ["请求耗时", "错误率", "响应码", "吞吐量", "慢请求标签"],
            "not_confirmed": ["应用CPU/内存/GC", "数据库等待", "Redis命中率", "中间件积压", "网络链路资源"],
        },
        "tail_note": (
            "平均值高于P95，通常表示样本量较小或存在极端慢请求；请优先查看最慢样本。"
            if elapsed_values and average_ms > p95_ms else ""
        ),
    }


def thresholds_for(options: dict[str, Any] | None = None) -> dict[str, Any]:
    options = options or {}
    requested = str(options.get("performance_profile") or options.get("test_profile") or "smoke").strip().lower()
    profile = PROFILE_ALIASES.get(requested, requested)
    if profile not in PROFILE_THRESHOLDS:
        profile = "smoke"
    thresholds = {**PROFILE_THRESHOLDS[profile], "profile": profile}
    thresholds.setdefault("min_transaction_tps", 0.0)
    for key in ("max_error_rate", "max_p95_ms", "max_p99_ms", "min_throughput_rps", "min_transaction_tps"):
        if options.get(key) not in (None, ""):
            thresholds[key] = _number(options.get(key), thresholds[key])
    return thresholds


def evaluate_gate(summary: dict[str, Any], options: dict[str, Any] | None = None) -> dict[str, Any]:
    thresholds = thresholds_for(options)
    checks = [
        {"name": "错误率", "actual": _number(summary.get("error_rate")), "operator": "<=", "expected": thresholds["max_error_rate"], "passed": _number(summary.get("error_rate")) <= thresholds["max_error_rate"], "unit": "%"},
        {"name": "P95响应时间", "actual": _number(summary.get("p95_ms")), "operator": "<=", "expected": thresholds["max_p95_ms"], "passed": _number(summary.get("p95_ms")) <= thresholds["max_p95_ms"], "unit": "ms"},
        {"name": "P99响应时间", "actual": _number(summary.get("p99_ms")), "operator": "<=", "expected": thresholds["max_p99_ms"], "passed": _number(summary.get("p99_ms")) <= thresholds["max_p99_ms"], "unit": "ms"},
    ]
    if thresholds["min_throughput_rps"] > 0:
        checks.append({"name": "请求吞吐量", "actual": _number(summary.get("request_throughput_rps") or summary.get("throughput_rps")), "operator": ">=", "expected": thresholds["min_throughput_rps"], "passed": _number(summary.get("request_throughput_rps") or summary.get("throughput_rps")) >= thresholds["min_throughput_rps"], "unit": "req/s"})
    if thresholds["min_transaction_tps"] > 0:
        actual_tps = summary.get("transaction_throughput_tps")
        checks.append({
            "name": "业务事务吞吐量",
            "actual": _number(actual_tps),
            "operator": ">=",
            "expected": thresholds["min_transaction_tps"],
            "passed": actual_tps is not None and _number(actual_tps) >= thresholds["min_transaction_tps"],
            "unit": "tx/s",
        })
    failed = [item for item in checks if not item["passed"]]
    return {
        "profile": thresholds["profile"],
        "label": thresholds["label"],
        "status": "PASSED" if not failed else "FAILED",
        "thresholds": thresholds,
        "checks": checks,
        "summary": "性能阈值通过" if not failed else "性能阈值未达标：" + "、".join(item["name"] for item in failed),
    }


def diagnose_performance(summary: dict[str, Any], gate: dict[str, Any] | None = None) -> dict[str, Any]:
    gate = gate or {}
    requests = int(summary.get("requests") or 0)
    errors = int(summary.get("errors") or 0)
    error_rate = _number(summary.get("error_rate"))
    average = _number(summary.get("average_ms"))
    median = _number(summary.get("p50_ms"))
    p95 = _number(summary.get("p95_ms"))
    p99 = _number(summary.get("p99_ms"))
    max_ms = _number(summary.get("max_ms"))
    stddev = _number(summary.get("stddev_ms"))
    error_categories = [item for item in summary.get("error_categories") or [] if isinstance(item, dict)]
    findings: list[dict[str, Any]] = []
    warmup_excluded = int(summary.get("warmup_samples_excluded") or 0)
    warmup_errors = int(summary.get("warmup_errors") or 0)
    if warmup_excluded:
        findings.append({
            "severity": "INFO" if not warmup_errors else "P1",
            "title": "已应用预热样本策略",
            "detail": f"原始JTL保留全部样本；本次门槛计算排除 {warmup_excluded} 个预热样本，其中失败 {warmup_errors} 个。",
        })
    if requests < 30:
        findings.append({"severity": "INFO", "title": "样本量偏少", "detail": f"当前仅 {requests} 个样本，适合链路验证，不适合形成容量结论。"})
    if errors:
        failed_gate_names = {str(item.get("name") or "") for item in gate.get("checks") or [] if not item.get("passed")}
        severity = "P0" if "错误率" in failed_gate_names else "P1"
        category_text = "、".join(f"{item.get('label')} {item.get('count')} 次" for item in error_categories[:4])
        findings.append({"severity": severity, "title": "失败采样已分类", "detail": f"失败 {errors} 次，错误率 {error_rate}%；分类为：{category_text or '未分类错误'}。"})
    if median and average > median * 1.25:
        findings.append({"severity": "P1", "title": "平均值被慢请求拉高", "detail": f"平均 {average}ms 明显高于中位数 {median}ms，存在尾部慢请求或样本分布不均。"})
    if p95 and p99 and p99 > p95 * 1.4:
        findings.append({"severity": "P1", "title": "尾部延迟尖刺", "detail": f"P99 {p99}ms 明显高于P95 {p95}ms。"})
    if p95 and max_ms > p95 * 1.5:
        findings.append({"severity": "P2", "title": "最大值离群", "detail": f"最大耗时 {max_ms}ms 高于P95 {p95}ms。"})
    if stddev and average and stddev > average * 0.5:
        findings.append({"severity": "P2", "title": "耗时波动较大", "detail": f"标准差 {stddev}ms，接口耗时稳定性不足。"})

    bottlenecks = []
    for item in summary.get("by_label") or []:
        if not isinstance(item, dict):
            continue
        bottlenecks.append({
            "label": item.get("label") or "未命名请求",
            "samples": item.get("samples", 0),
            "errors": item.get("errors", 0),
            "average_ms": item.get("average_ms", 0),
            "p95_ms": item.get("p95_ms", 0),
            "p99_ms": item.get("p99_ms", 0),
            "max_ms": item.get("max_ms", 0),
            "score": _number(item.get("p95_ms") or item.get("max_ms") or item.get("average_ms")),
        })
    bottlenecks.sort(key=lambda item: item["score"], reverse=True)

    gate_status = gate.get("status") or "UNKNOWN"
    failed_names = [str(item.get("name") or "") for item in gate.get("checks") or [] if not item.get("passed")]
    category_summary = "、".join(f"{item.get('label')} {item.get('count')} 次" for item in error_categories[:3])
    if errors and gate_status == "FAILED":
        conclusion = f"当前未通过{'、'.join(failed_names) or '性能门槛'}；失败采样主要为{category_summary or '未分类错误'}。"
    elif errors:
        conclusion = f"性能门槛通过，但存在少量失败采样：{category_summary or '未分类错误'}。"
    elif gate_status == "FAILED":
        conclusion = "接口可用，但未达到当前性能准入阈值。"
    elif requests < 30:
        conclusion = "当前可作为链路验证结果，样本量不足以形成正式性能结论。"
    else:
        conclusion = "当前性能准入通过，可进入更高负载或稳定性验证。"

    return {
        "conclusion": conclusion,
        "sample_grade": "INSUFFICIENT" if requests < 30 else "OBSERVABLE" if requests < 100 else "BASELINE_READY",
        "findings": findings,
        "error_categories": error_categories,
        "bottlenecks": bottlenecks[:5],
        "slowest_samples": (summary.get("slowest_samples") or [])[:10],
        "evidence_boundary": {
            "confirmed_from_jtl": summary.get("evidence_scope", {}).get("confirmed", []),
            "requires_external_evidence": summary.get("evidence_scope", {}).get("not_confirmed", []),
            "rule": "没有DB、Redis、APM或主机监控证据时，瓶颈归因只能作为待验证假设。",
        },
        "bottleneck_hypotheses": [
            {
                "scope": "application_or_dependency",
                "confidence": "low",
                "reason": "JTL只能确认慢请求和失败分布，不能单独确认服务端资源瓶颈。",
                "required_evidence": ["应用日志/APM", "CPU/内存/GC", "数据库等待", "Redis/中间件指标"],
            }
        ] if findings else [],
    }
