from quality_hub_backend.services.performance_review import (
    build_builtin_performance_review,
    build_performance_ai_prompt,
)


def test_performance_review_does_not_mark_tolerated_error_as_p0():
    performance = {
        "requests": 500,
        "errors": 1,
        "error_rate": 0.2,
        "average_ms": 100,
        "p95_ms": 150,
        "p99_ms": 400,
        "throughput_rps": 8.0,
        "by_label": [{"label": "GET health", "samples": 500, "errors": 1, "p95_ms": 150, "p99_ms": 400, "max_ms": 8000}],
    }
    gate = {
        "status": "PASSED",
        "profile": "smoke",
        "checks": [{"name": "错误率", "actual": 0.2, "expected": 1.0, "passed": True}],
    }
    diagnosis = {
        "conclusion": "性能门槛通过，但存在少量失败采样。",
        "findings": [{"severity": "P1", "title": "失败采样", "detail": "1次"}],
        "bottlenecks": performance["by_label"],
        "evidence_boundary": {"requires_external_evidence": ["应用日志/APM", "数据库等待"]},
        "bottleneck_hypotheses": [{"scope": "application_or_dependency", "confidence": "low"}],
    }

    review = build_builtin_performance_review(performance, gate, diagnosis)

    assert review["risk_level"] == "P1"
    assert review["performance_assessment"]["status"] == "PASSED"
    assert review["bottleneck_analysis"]["confirmed_from_jtl"][0]["label"] == "GET health"
    assert review["optimization_recommendations"][0]["validation"]


def test_performance_review_marks_failed_gate_as_p0_and_prompt_guards_evidence():
    performance = {"requests": 100, "errors": 10, "error_rate": 10, "p95_ms": 5000, "p99_ms": 8000}
    gate = {
        "status": "FAILED",
        "profile": "load",
        "checks": [{"name": "错误率", "actual": 10, "expected": 1, "passed": False}],
    }
    diagnosis = {"conclusion": "性能门槛未通过。", "findings": [], "bottlenecks": []}

    review = build_builtin_performance_review(performance, gate, diagnosis)
    prompt = build_performance_ai_prompt(performance, gate, diagnosis, review["baseline_comparison"])

    assert review["risk_level"] == "P0"
    assert "不得断言瓶颈位于数据库、应用、中间件或网络" in prompt
    assert "optimization_recommendations" in prompt


def test_performance_review_preserves_observability_evidence_for_ai_and_reports():
    performance = {"requests": 100, "errors": 0, "error_rate": 0, "p95_ms": 300, "p99_ms": 500}
    gate = {"status": "PASSED", "profile": "load", "checks": []}
    observability = {
        "status": "PARTIAL",
        "available_categories": ["host", "database"],
        "missing_core_categories": ["apm"],
        "signals": [
            {
                "category": "host",
                "severity": "P1",
                "signal": "cpu_saturation",
                "value": 92,
                "unit": "%",
            }
        ],
    }
    diagnosis = {
        "conclusion": "性能门槛通过，但主机CPU出现高水位。",
        "findings": [],
        "bottlenecks": [],
        "observability": observability,
    }

    review = build_builtin_performance_review(
        performance,
        gate,
        diagnosis,
        observability_evidence=observability,
    )
    prompt = build_performance_ai_prompt(
        performance,
        gate,
        diagnosis,
        review["baseline_comparison"],
        observability,
    )

    assert review["observability_evidence"]["status"] == "PARTIAL"
    assert review["bottleneck_analysis"]["observability_signals"][0]["signal"] == "cpu_saturation"
    assert '"observability_evidence"' in prompt
    assert "cpu_saturation" in prompt


def test_performance_review_marks_missing_observability_without_inventing_root_cause():
    review = build_builtin_performance_review(
        {"requests": 10, "errors": 0, "error_rate": 0},
        {"status": "PASSED", "profile": "baseline", "checks": []},
        {"conclusion": "性能阈值全部通过。", "findings": [], "bottlenecks": []},
    )

    assert review["observability_evidence"]["status"] == "MISSING"
    assert review["bottleneck_analysis"]["observability_status"] == "MISSING"
    assert "根因必须由外部证据确认" in review["bottleneck_analysis"]["statement"]
