from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from quality_hub_backend.services.performance_analysis import PROFILE_THRESHOLDS


PROFILE_ALIASES = {"stability": "soak", "concurrent": "concurrency"}

PROFILE_EXECUTION_DEFAULTS: dict[str, dict[str, Any]] = {
    "smoke": {"label": "冒烟验证", "threads": 2, "rampup_seconds": 2, "duration_seconds": 60, "warmup_samples_per_label": 0, "workload_model": "steady", "account_reuse_policy": "round_robin"},
    "baseline": {"label": "基准测试", "threads": 1, "rampup_seconds": 5, "duration_seconds": 180, "warmup_samples_per_label": 1, "workload_model": "single_user_steady", "account_reuse_policy": "strict_unique"},
    "load": {"label": "负载测试", "threads": 20, "rampup_seconds": 60, "duration_seconds": 600, "warmup_samples_per_label": 0, "workload_model": "stepped_load", "account_reuse_policy": "round_robin"},
    "concurrency": {"label": "并发测试", "threads": 50, "rampup_seconds": 1, "duration_seconds": 180, "warmup_samples_per_label": 0, "workload_model": "synchronized_release", "account_reuse_policy": "round_robin"},
    "spike": {"label": "突增测试", "threads": 100, "rampup_seconds": 1, "duration_seconds": 120, "warmup_samples_per_label": 0, "workload_model": "burst_and_recovery", "account_reuse_policy": "round_robin"},
    "stress": {"label": "压力测试", "threads": 100, "rampup_seconds": 120, "duration_seconds": 900, "warmup_samples_per_label": 0, "workload_model": "stepped_beyond_target", "account_reuse_policy": "round_robin"},
    "soak": {"label": "稳定性测试", "threads": 20, "rampup_seconds": 60, "duration_seconds": 43200, "warmup_samples_per_label": 0, "workload_model": "long_running_steady", "account_reuse_policy": "round_robin"},
}

DEFAULT_CAPACITY_STAGES = (
    {"code": "baseline", "name": "基线", "profile": "baseline", "threads": 1, "rampup_seconds": 5, "duration_seconds": 180},
    {"code": "light-load", "name": "轻负载", "profile": "load", "threads": 5, "rampup_seconds": 60, "duration_seconds": 300},
    {"code": "target-load", "name": "目标负载", "profile": "load", "threads": 10, "rampup_seconds": 120, "duration_seconds": 600},
    {"code": "capacity-search", "name": "容量探索", "profile": "stress", "threads": 20, "rampup_seconds": 180, "duration_seconds": 900},
)


def _bounded_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(parsed, maximum))


def normalize_profile(value: Any, default: str = "baseline") -> str:
    profile = str(value or default).strip().lower()
    profile = PROFILE_ALIASES.get(profile, profile)
    if profile not in PROFILE_EXECUTION_DEFAULTS:
        raise ValueError(
            f"不支持的性能Profile：{profile}；允许值：{', '.join(PROFILE_EXECUTION_DEFAULTS)}"
        )
    return profile


def profile_catalog() -> list[dict[str, Any]]:
    catalog = []
    for code, execution in PROFILE_EXECUTION_DEFAULTS.items():
        thresholds = PROFILE_THRESHOLDS.get(code, {})
        catalog.append({
            "profile": code,
            **deepcopy(execution),
            "thresholds": {
                "max_error_rate": thresholds.get("max_error_rate", 0),
                "max_p95_ms": thresholds.get("max_p95_ms", 0),
                "max_p99_ms": thresholds.get("max_p99_ms", 0),
                "min_throughput_rps": thresholds.get("min_throughput_rps", 0),
                "min_transaction_tps": thresholds.get("min_transaction_tps", 0),
            },
        })
    return catalog


def _normalized_stage(stage: dict[str, Any], index: int) -> dict[str, Any]:
    profile = normalize_profile(stage.get("profile"), "load")
    defaults = PROFILE_EXECUTION_DEFAULTS[profile]
    code = re.sub(
        r"[^a-zA-Z0-9_-]",
        "-",
        str(stage.get("code") or profile),
    ).strip("-") or f"stage-{index}"
    return {
        "code": code,
        "name": str(stage.get("name") or defaults["label"]),
        "profile": profile,
        "threads": _bounded_int(stage.get("threads"), defaults["threads"], 1, 500),
        "rampup_seconds": _bounded_int(
            stage.get("rampup_seconds"), defaults["rampup_seconds"], 0, 3600
        ),
        "duration_seconds": _bounded_int(
            stage.get("duration_seconds"), defaults["duration_seconds"], 10, 604800
        ),
        "warmup_samples_per_label": _bounded_int(
            stage.get("warmup_samples_per_label"),
            defaults["warmup_samples_per_label"],
            0,
            100,
        ),
        "workload_model": str(stage.get("workload_model") or defaults["workload_model"]),
        "account_reuse_policy": str(
            stage.get("account_reuse_policy") or defaults["account_reuse_policy"]
        ),
        "transaction_mode": str(stage.get("transaction_mode") or "request_only"),
        "pacing_ms": _bounded_int(stage.get("pacing_ms"), 300, 0, 60000),
    }


def _profile_stages(profile: str, options: dict[str, Any]) -> list[dict[str, Any]]:
    defaults = PROFILE_EXECUTION_DEFAULTS[profile]
    target_threads = _bounded_int(
        options.get("jmeter_threads", options.get("threads")), defaults["threads"], 1, 500
    )
    rampup = _bounded_int(
        options.get("jmeter_rampup", options.get("rampup_seconds")),
        defaults["rampup_seconds"],
        0,
        3600,
    )
    duration = _bounded_int(
        options.get("duration_seconds", options.get("jmeter_duration_seconds")),
        defaults["duration_seconds"],
        10,
        604800,
    )
    common = {
        "profile": profile,
        "warmup_samples_per_label": options.get("warmup_samples_per_label"),
        "account_reuse_policy": options.get("account_reuse_policy"),
        "transaction_mode": options.get("transaction_mode"),
        "pacing_ms": options.get("pacing_ms"),
    }
    if profile == "load":
        stage_duration = max(10, duration // 3)
        return [
            _normalized_stage({**common, "code": code, "name": name, "threads": max(1, round(target_threads * ratio)), "rampup_seconds": max(1, rampup // 3), "duration_seconds": stage_duration}, index)
            for index, (code, name, ratio) in enumerate((
                ("light-load", "轻负载", 0.25),
                ("medium-load", "中负载", 0.5),
                ("target-load", "目标负载", 1.0),
            ), start=1)
        ]
    if profile == "stress":
        stage_duration = max(10, duration // 4)
        return [
            _normalized_stage({**common, "code": code, "name": name, "threads": min(500, max(1, round(target_threads * ratio))), "rampup_seconds": max(1, rampup // 4), "duration_seconds": stage_duration}, index)
            for index, (code, name, ratio) in enumerate((
                ("stress-25", "压力25%", 0.25),
                ("stress-50", "压力50%", 0.5),
                ("stress-100", "压力100%", 1.0),
                ("stress-beyond", "超目标压力", 1.5),
            ), start=1)
        ]
    if profile == "spike":
        recovery_threads = max(1, round(target_threads * 0.1))
        stage_duration = max(10, duration // 3)
        return [
            _normalized_stage({**common, "code": "pre-spike", "name": "突增前稳态", "threads": recovery_threads, "rampup_seconds": max(1, rampup), "duration_seconds": stage_duration}, 1),
            _normalized_stage({**common, "code": "spike", "name": "瞬时突增", "threads": target_threads, "rampup_seconds": 0, "duration_seconds": stage_duration}, 2),
            _normalized_stage({**common, "code": "recovery", "name": "突增后恢复", "threads": recovery_threads, "rampup_seconds": max(1, rampup), "duration_seconds": stage_duration}, 3),
        ]
    return [_normalized_stage({
        **common,
        "code": profile,
        "name": defaults["label"],
        "threads": target_threads,
        "rampup_seconds": rampup,
        "duration_seconds": duration,
    }, 1)]


def build_profile_stages(options: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    options = options or {}
    supplied = options.get("stages")
    if isinstance(supplied, list) and supplied:
        return [_normalized_stage(stage, index) for index, stage in enumerate(supplied, start=1)]

    explicit_profile = options.get("performance_profile") or options.get("test_type")
    if explicit_profile:
        profile = normalize_profile(explicit_profile)
        return _profile_stages(profile, options)

    return [
        _normalized_stage(deepcopy(stage), index)
        for index, stage in enumerate(DEFAULT_CAPACITY_STAGES, start=1)
    ]


def validate_transaction_stage_durations(
    stages: list[dict[str, Any]],
    step_count: int,
) -> int:
    count = max(2, int(step_count or 0))
    minimum_seconds = max(30, count * 20 + 10)
    too_short = [
        stage for stage in stages
        if int(stage.get("duration_seconds") or 0) < minimum_seconds
    ]
    if too_short:
        details = "、".join(
            f"{stage.get('name') or stage.get('code')}={stage.get('duration_seconds')}秒"
            for stage in too_short
        )
        raise ValueError(
            f"业务事务包含{count}个有序步骤，单阶段至少需要{minimum_seconds}秒以避免在事务中途停止；"
            f"当前{details}。请提高持续时间后重新生成JMX。"
        )
    return minimum_seconds


def build_execution_context(
    *,
    stages: list[dict[str, Any]],
    targets: list[dict[str, Any]],
    environment: str,
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    first = stages[0] if stages else {}
    target_values = [
        f"{str(item.get('method') or '').upper()} {str(item.get('path') or '')}".strip()
        for item in targets
    ]
    return {
        "status": "PLANNED",
        "test_type": first.get("profile") or "unknown",
        "profile": first.get("profile") or "unknown",
        "profiles": [stage.get("profile") for stage in stages],
        "target_api": target_values[0] if len(target_values) == 1 else "",
        "target_apis": target_values,
        "env": str(environment or "default"),
        "stages": deepcopy(stages),
        "thresholds": deepcopy(thresholds),
    }
