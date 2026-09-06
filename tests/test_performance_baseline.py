from quality_hub_backend.services.performance_baseline import (
    approve_candidate,
    build_run_performance_state,
    compare_metrics,
    matching_active_baseline,
    normalize_performance_state,
    target_fingerprint,
)


def _summary(p95=100, p99=150, error_rate=0, throughput=10):
    return {
        "requests": 100,
        "average_ms": 80,
        "p50_ms": 70,
        "p90_ms": 90,
        "p95_ms": p95,
        "p99_ms": p99,
        "max_ms": 200,
        "error_rate": error_rate,
        "request_throughput_rps": throughput,
        "by_label": [{"label": "GET /health"}],
    }


def test_first_eligible_run_becomes_candidate_not_automatic_active_baseline():
    fingerprint = target_fingerprint(_summary(), "health")
    state = build_run_performance_state(
        run_id="run-1",
        summary=_summary(),
        profile="baseline",
        environment="test",
        fingerprint=fingerprint,
        gate_status="PASSED",
    )

    assert state["baseline"]["status"] == "candidate"
    assert state["comparison"]["status"] == "not_compared"


def test_approved_baseline_is_matched_by_environment_profile_and_target():
    fingerprint = target_fingerprint(_summary(), "health")
    context = normalize_performance_state({"run_id": "run-1", "performance": {}})
    context["performance"] = build_run_performance_state(
        run_id="run-1",
        summary=_summary(),
        profile="baseline",
        environment="test",
        fingerprint=fingerprint,
    )
    active = approve_candidate(context, approved_by="tester", approved_at="2026-09-05T10:00:00+08:00")

    matched = matching_active_baseline([active], {
        "profile": "baseline",
        "environment": "test",
        "target_fingerprint": fingerprint,
    })

    assert matched["run_id"] == "run-1"
    assert active["baseline"] is True


def test_regression_is_reported_against_active_baseline():
    fingerprint = target_fingerprint(_summary(), "health")
    active = {
        "run_id": "run-1",
        "performance": build_run_performance_state(
            run_id="run-1",
            summary=_summary(),
            profile="load",
            environment="test",
            fingerprint=fingerprint,
        ),
    }
    active = approve_candidate(active, approved_by="tester", approved_at="2026-09-05T10:00:00+08:00")

    state = build_run_performance_state(
        run_id="run-2",
        summary=_summary(p95=130, p99=210, error_rate=1, throughput=8),
        profile="load",
        environment="test",
        fingerprint=fingerprint,
        active_baseline=active,
    )

    assert state["comparison"]["result"] == "regressed"
    assert "p95_ms" in state["comparison"]["regressed_metrics"]
    assert state["comparison"]["reference_run_id"] == "run-1"


def test_transaction_throughput_tps_is_higher_is_better():
    comparison = compare_metrics(
        {**_summary(), "transaction_throughput_tps": 12},
        {**_summary(), "transaction_throughput_tps": 10},
    )

    change = comparison["changes"]["transaction_throughput_tps"]
    assert change["direction"] == "higher_is_better"
    assert change["assessment"] == "improved"


def test_request_and_business_transaction_baselines_do_not_match():
    fingerprint = target_fingerprint(_summary(), "health")
    context = normalize_performance_state({"run_id": "run-tx", "performance": {}})
    context["performance"] = build_run_performance_state(
        run_id="run-tx",
        summary={**_summary(), "transaction_throughput_tps": 2},
        profile="baseline",
        environment="test",
        fingerprint=fingerprint,
        measurement_mode="business_transaction",
    )
    active = approve_candidate(
        context,
        approved_by="tester",
        approved_at="2026-09-06T10:00:00+08:00",
    )

    matched = matching_active_baseline([active], {
        "profile": "baseline",
        "environment": "test",
        "target_fingerprint": fingerprint,
        "measurement_mode": "request_only",
    })

    assert matched is None
