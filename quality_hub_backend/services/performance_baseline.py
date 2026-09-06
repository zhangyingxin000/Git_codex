from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Iterable


BASELINE_METRICS = (
    "average_ms",
    "p50_ms",
    "p90_ms",
    "p95_ms",
    "p99_ms",
    "max_ms",
    "error_rate",
    "request_throughput_rps",
    "transaction_throughput_tps",
)


def normalize_performance_state(context: dict[str, Any]) -> dict[str, Any]:
    performance = context.setdefault("performance", {})
    baseline = performance.setdefault("baseline", {})
    comparison = performance.setdefault("comparison", {})
    baseline.setdefault("status", "unset")
    baseline.setdefault("baseline_run_id", None)
    baseline.setdefault("profile", None)
    baseline.setdefault("environment", None)
    baseline.setdefault("target_fingerprint", None)
    if not baseline.get("measurement_mode"):
        try:
            transaction_tps = float((baseline.get("metrics") or {}).get("transaction_throughput_tps") or 0)
        except (TypeError, ValueError):
            transaction_tps = 0.0
        baseline["measurement_mode"] = (
            "business_transaction" if transaction_tps > 0 else "request_only"
        )
    baseline.setdefault("approved_by", None)
    baseline.setdefault("approved_at", None)
    baseline.setdefault("metrics", {})
    comparison.setdefault("status", "not_compared")
    comparison.setdefault("reference_run_id", None)
    comparison.setdefault("result", "unknown")
    comparison.setdefault("changes", {})
    comparison.setdefault("reason", "")
    return context


def target_fingerprint(summary: dict[str, Any], target_hint: str = "") -> str:
    labels = sorted(
        str(item.get("label") or "").strip()
        for item in summary.get("by_label") or []
        if isinstance(item, dict) and str(item.get("label") or "").strip()
    )
    payload = {"target_hint": str(target_hint or "").strip(), "labels": labels}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:20]


def baseline_identity(
    profile: str,
    environment: str,
    fingerprint: str,
    measurement_mode: str = "request_only",
) -> dict[str, str]:
    return {
        "profile": str(profile or "smoke").strip().lower(),
        "environment": str(environment or "default").strip(),
        "target_fingerprint": str(fingerprint or "").strip(),
        "measurement_mode": str(measurement_mode or "request_only").strip().lower(),
    }


def _metric_snapshot(summary: dict[str, Any]) -> dict[str, float]:
    snapshot: dict[str, float] = {}
    for key in BASELINE_METRICS:
        source_key = "throughput_rps" if key == "request_throughput_rps" and key not in summary else key
        try:
            snapshot[key] = round(float(summary.get(source_key) or 0), 4)
        except (TypeError, ValueError):
            snapshot[key] = 0.0
    return snapshot


def matching_active_baseline(
    contexts: Iterable[dict[str, Any]],
    identity: dict[str, str],
    *,
    exclude_run_id: str = "",
) -> dict[str, Any] | None:
    for candidate in contexts:
        if str(candidate.get("run_id") or "") == str(exclude_run_id or ""):
            continue
        state = normalize_performance_state(deepcopy(candidate))["performance"]["baseline"]
        if state.get("status") != "active":
            continue
        if all(str(state.get(key) or "") == str(identity.get(key) or "") for key in identity):
            return candidate
    return None


def compare_metrics(current: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    current_metrics = _metric_snapshot(current)
    reference_metrics = _metric_snapshot(reference)
    changes: dict[str, dict[str, float | str]] = {}
    regressions: list[str] = []
    improvements: list[str] = []
    for metric in BASELINE_METRICS:
        current_value = current_metrics[metric]
        reference_value = reference_metrics[metric]
        if reference_value == 0:
            delta_pct = 0.0 if current_value == 0 else 100.0
        else:
            delta_pct = round((current_value - reference_value) / reference_value * 100, 2)
        direction = (
            "higher_is_better"
            if metric in {"request_throughput_rps", "transaction_throughput_tps"}
            else "lower_is_better"
        )
        regressed = delta_pct < -10 if direction == "higher_is_better" else delta_pct > 10
        improved = delta_pct > 10 if direction == "higher_is_better" else delta_pct < -10
        if metric == "error_rate":
            regressed = current_value - reference_value > 0.5
            improved = reference_value - current_value > 0.5
        if regressed:
            regressions.append(metric)
        elif improved:
            improvements.append(metric)
        changes[metric] = {
            "current": current_value,
            "baseline": reference_value,
            "delta_pct": delta_pct,
            "direction": direction,
            "assessment": "regressed" if regressed else "improved" if improved else "stable",
        }
    result = "regressed" if regressions else "improved" if improvements else "pass"
    return {
        "status": result,
        "result": result,
        "changes": changes,
        "regressed_metrics": regressions,
        "improved_metrics": improvements,
    }


def build_run_performance_state(
    *,
    run_id: str,
    summary: dict[str, Any],
    profile: str,
    environment: str,
    fingerprint: str,
    measurement_mode: str = "request_only",
    active_baseline: dict[str, Any] | None = None,
    gate_status: str = "PASSED",
) -> dict[str, Any]:
    identity = baseline_identity(profile, environment, fingerprint, measurement_mode)
    metrics = _metric_snapshot(summary)
    if active_baseline:
        active_state = normalize_performance_state(deepcopy(active_baseline))["performance"]["baseline"]
        comparison = compare_metrics(summary, active_state.get("metrics") or {})
        comparison.update({
            "reference_run_id": active_baseline.get("run_id"),
            "reason": "已与相同环境、Profile、目标指纹和测量模式的人工批准基线比较。",
        })
        baseline = {
            "status": "unset",
            "baseline_run_id": active_baseline.get("run_id"),
            **identity,
            "approved_by": None,
            "approved_at": None,
            "metrics": metrics,
        }
    else:
        candidate = gate_status == "PASSED" and int(summary.get("requests") or 0) > 0
        baseline = {
            "status": "candidate" if candidate else "unset",
            "baseline_run_id": run_id if candidate else None,
            **identity,
            "approved_by": None,
            "approved_at": None,
            "metrics": metrics,
        }
        comparison = {
            "status": "not_compared",
            "reference_run_id": None,
            "result": "unknown",
            "changes": {},
            "reason": "尚无相同环境、Profile、目标指纹和测量模式的已批准基线。",
        }
    return {"baseline": baseline, "comparison": comparison}


def approve_candidate(context: dict[str, Any], *, approved_by: str, approved_at: str) -> dict[str, Any]:
    updated = normalize_performance_state(deepcopy(context))
    baseline = updated["performance"]["baseline"]
    if baseline.get("status") not in {"candidate", "active"}:
        raise ValueError("当前批次没有可批准的性能基线候选。")
    baseline["status"] = "active"
    baseline["baseline_run_id"] = updated.get("run_id")
    baseline["approved_by"] = str(approved_by or "manual")
    baseline["approved_at"] = approved_at
    updated["baseline"] = True
    return updated
