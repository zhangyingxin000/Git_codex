from __future__ import annotations

from typing import Any, Iterable


_TREND_METRICS = (
    "p95_ms",
    "p99_ms",
    "error_rate",
    "request_throughput_rps",
    "transaction_throughput_tps",
)


def _metric_value(metrics: dict[str, Any], key: str) -> float | None:
    value = metrics.get(key)
    if value in (None, "") and key == "request_throughput_rps":
        value = metrics.get("throughput_rps")
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None


def build_performance_trends(
    contexts: Iterable[dict[str, Any]],
    *,
    max_points_per_series: int = 20,
) -> dict[str, Any]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for context in contexts:
        performance = context.get("performance") or {}
        baseline = performance.get("baseline") or {}
        metrics = baseline.get("metrics") or {}
        if not metrics:
            continue
        identity = (
            str(baseline.get("profile") or "unknown"),
            str(baseline.get("environment") or "default"),
            str(baseline.get("target_fingerprint") or ""),
        )
        if not identity[2]:
            continue
        comparison = performance.get("comparison") or {}
        point = {
            "run_id": context.get("run_id") or "",
            "created_at": context.get("created_at") or context.get("updated_at") or "",
            "run_status": context.get("status") or "UNKNOWN",
            "baseline_status": baseline.get("status") or "unset",
            "comparison_result": comparison.get("result") or "unknown",
            "reference_run_id": comparison.get("reference_run_id"),
            "metrics": {key: _metric_value(metrics, key) for key in _TREND_METRICS},
        }
        grouped.setdefault(identity, []).append(point)

    series: list[dict[str, Any]] = []
    for identity, points in grouped.items():
        points.sort(key=lambda item: (item.get("created_at") or "", item.get("run_id") or ""))
        points = points[-max(1, int(max_points_per_series or 20)):]
        active = next((item for item in reversed(points) if item.get("baseline_status") == "active"), None)
        latest = points[-1]
        series.append({
            "profile": identity[0],
            "environment": identity[1],
            "target_fingerprint": identity[2],
            "run_count": len(points),
            "active_baseline_run_id": active.get("run_id") if active else None,
            "latest_run_id": latest.get("run_id"),
            "latest_result": latest.get("comparison_result") or "unknown",
            "points": points,
        })

    series.sort(
        key=lambda item: (
            item.get("points", [{}])[-1].get("created_at") or "",
            item.get("profile") or "",
        ),
        reverse=True,
    )
    all_points = [point for item in series for point in item.get("points") or []]
    return {
        "schema_version": "1.0",
        "status": "READY" if series else "NOT_RUN",
        "summary": {
            "series": len(series),
            "runs": len(all_points),
            "active_baselines": sum(1 for item in series if item.get("active_baseline_run_id")),
            "regressed_runs": sum(1 for item in all_points if item.get("comparison_result") == "regressed"),
        },
        "series": series,
    }
