from quality_hub_backend.services.performance_history import build_performance_trends


def _context(run_id, created_at, *, baseline_status, comparison_result, p95, rps, tps):
    return {
        "run_id": run_id,
        "created_at": created_at,
        "status": "PASSED",
        "performance": {
            "baseline": {
                "status": baseline_status,
                "profile": "load",
                "environment": "https://test.example.com",
                "target_fingerprint": "target-1",
                "metrics": {
                    "p95_ms": p95,
                    "p99_ms": p95 + 100,
                    "error_rate": 0,
                    "request_throughput_rps": rps,
                    "transaction_throughput_tps": tps,
                },
            },
            "comparison": {"result": comparison_result, "reference_run_id": "run-1"},
        },
    }


def test_build_performance_trends_groups_comparable_runs_and_marks_baseline():
    trends = build_performance_trends([
        _context("run-2", "2026-09-05T11:00:00+08:00", baseline_status="unset", comparison_result="regressed", p95=800, rps=12, tps=4),
        _context("run-1", "2026-09-05T10:00:00+08:00", baseline_status="active", comparison_result="unknown", p95=500, rps=15, tps=5),
    ])

    assert trends["status"] == "READY"
    assert trends["summary"] == {
        "series": 1,
        "runs": 2,
        "active_baselines": 1,
        "regressed_runs": 1,
    }
    series = trends["series"][0]
    assert series["active_baseline_run_id"] == "run-1"
    assert series["latest_run_id"] == "run-2"
    assert series["points"][1]["metrics"]["transaction_throughput_tps"] == 4.0


def test_build_performance_trends_does_not_mix_different_targets():
    first = _context("run-1", "2026-09-05T10:00:00+08:00", baseline_status="active", comparison_result="unknown", p95=500, rps=15, tps=5)
    second = _context("run-2", "2026-09-05T11:00:00+08:00", baseline_status="candidate", comparison_result="unknown", p95=600, rps=14, tps=4)
    second["performance"]["baseline"]["target_fingerprint"] = "target-2"

    trends = build_performance_trends([first, second])

    assert trends["summary"]["series"] == 2
