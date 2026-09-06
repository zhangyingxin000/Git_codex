from quality_hub_backend.services.performance_skill_generator import (
    build_execution_context,
    build_profile_stages,
    profile_catalog,
    validate_transaction_stage_durations,
)
import pytest


def test_profile_catalog_exposes_constrained_performance_profiles():
    profiles = {item["profile"]: item for item in profile_catalog()}

    assert {"baseline", "load", "concurrency", "spike", "stress", "soak"} <= set(profiles)
    assert profiles["baseline"]["threads"] == 1
    assert profiles["baseline"]["warmup_samples_per_label"] == 1
    assert profiles["soak"]["duration_seconds"] >= 1800


def test_explicit_profile_builds_one_bounded_stage():
    stages = build_profile_stages({
        "performance_profile": "concurrency",
        "threads": 800,
        "rampup_seconds": -1,
        "duration_seconds": 5,
    })

    assert len(stages) == 1
    assert stages[0]["code"] == "concurrency"
    assert stages[0]["profile"] == "concurrency"
    assert stages[0]["threads"] == 500
    assert stages[0]["rampup_seconds"] == 0
    assert stages[0]["duration_seconds"] == 10
    assert stages[0]["workload_model"] == "synchronized_release"
    assert stages[0]["transaction_mode"] == "request_only"


def test_execution_context_keeps_profile_target_and_thresholds_together():
    stages = build_profile_stages({"performance_profile": "baseline"})
    context = build_execution_context(
        stages=stages,
        targets=[{"method": "GET", "path": "/api/health"}],
        environment="https://test.example",
        thresholds={"max_error_rate": 1, "max_p95_ms": 1500},
    )

    assert context["profile"] == "baseline"
    assert context["target_api"] == "GET /api/health"
    assert context["env"] == "https://test.example"
    assert context["thresholds"]["max_p95_ms"] == 1500


def test_transaction_duration_gate_blocks_stage_that_can_end_mid_flow():
    stages = build_profile_stages({
        "performance_profile": "baseline",
        "duration_seconds": 10,
    })

    with pytest.raises(ValueError, match="2个有序步骤.*至少需要50秒"):
        validate_transaction_stage_durations(stages, 2)


def test_transaction_duration_gate_accepts_complete_flow_window():
    stages = build_profile_stages({
        "performance_profile": "baseline",
        "duration_seconds": 60,
    })

    assert validate_transaction_stage_durations(stages, 2) == 50
