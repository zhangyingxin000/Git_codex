from __future__ import annotations

import json
from typing import Any


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _failed_checks(gate: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in gate.get("checks") or [] if isinstance(item, dict) and not item.get("passed")]


def _risk_level(
    performance: dict[str, Any],
    gate: dict[str, Any],
    diagnosis: dict[str, Any],
    baseline_comparison: dict[str, Any],
) -> str:
    failed_checks = _failed_checks(gate)
    if failed_checks:
        return "P0"
    if str(baseline_comparison.get("result") or "").lower() == "regressed":
        return "P1"
    severities = {
        str(item.get("severity") or "").upper()
        for item in diagnosis.get("findings") or []
        if isinstance(item, dict)
    }
    if _number(performance.get("error_rate")) > 0 or "P1" in severities:
        return "P1"
    if "P2" in severities:
        return "P2"
    return "PASS"


def build_builtin_performance_review(
    performance: dict[str, Any],
    gate: dict[str, Any],
    diagnosis: dict[str, Any],
    baseline_comparison: dict[str, Any] | None = None,
    observability_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    baseline_comparison = baseline_comparison or {
        "status": "not_compared",
        "result": "unknown",
        "changes": {},
        "reason": "当前批次尚未建立可用的历史基线对比。",
    }
    failed_checks = _failed_checks(gate)
    observability_evidence = observability_evidence or diagnosis.get("observability") or {
        "status": "MISSING",
        "available_categories": [],
        "missing_core_categories": ["host", "apm", "database"],
        "signals": [],
        "statement": "当前没有外部监控证据，AI只能给出待验证的瓶颈假设。",
    }
    risk_level = _risk_level(performance, gate, diagnosis, baseline_comparison)
    findings = list(diagnosis.get("findings") or [])
    bottlenecks = list(diagnosis.get("bottlenecks") or [])
    if str(baseline_comparison.get("result") or "").lower() == "regressed":
        findings.append({
            "severity": "P1",
            "title": "历史基线对比出现回退",
            "detail": "回退指标：" + "、".join(baseline_comparison.get("regressed_metrics") or []),
        })

    recommendations: list[dict[str, Any]] = []
    if _number(performance.get("error_rate")) > 0:
        recommendations.append({
            "priority": "P0" if failed_checks else "P1",
            "action": "先按错误分类定位失败采样，区分断言、鉴权、网络和服务端错误。",
            "reason": f"当前失败 {int(performance.get('errors') or 0)} 次，错误率 {_number(performance.get('error_rate'))}% 。",
            "validation": "修正后使用相同环境、Profile和目标接口重新执行，确认错误率回到阈值内。",
        })
    if bottlenecks:
        recommendations.append({
            "priority": "P1",
            "action": "优先复核慢接口：" + "、".join(str(item.get("label") or "") for item in bottlenecks[:3]),
            "reason": "这些采样器的P95或最大耗时在当前批次中最高。",
            "validation": "结合JMeter HTML趋势图和同批应用日志/APM确认慢点是否稳定复现。",
        })
    recommendations.append({
        "priority": "P1" if baseline_comparison.get("result") == "regressed" else "P2",
        "action": "使用同一环境、Profile、目标指纹和独立JTL进行可比复测。",
        "reason": "不同环境、负载模型或接口集合的数据不能直接形成性能回归结论。",
        "validation": "批准首个候选基线后，检查后续批次的P95、P99、错误率和吞吐量变化。",
    })

    conclusion = diagnosis.get("conclusion") or (
        "性能阈值全部通过。" if not failed_checks else "存在未通过的性能阈值。"
    )
    evidence_boundary = diagnosis.get("evidence_boundary") or {}
    hypotheses = list(diagnosis.get("bottleneck_hypotheses") or [])
    confirmed = [
        {
            "label": item.get("label"),
            "samples": item.get("samples", 0),
            "errors": item.get("errors", 0),
            "p95_ms": item.get("p95_ms", 0),
            "p99_ms": item.get("p99_ms", 0),
            "max_ms": item.get("max_ms", 0),
        }
        for item in bottlenecks[:5]
    ]
    return {
        "mode": "built_in_rules",
        "risk_level": risk_level,
        "conclusion": conclusion,
        "findings": findings[:20],
        "recommendations": [item["action"] for item in recommendations],
        "performance_assessment": {
            "status": gate.get("status") or "UNKNOWN",
            "profile": gate.get("profile") or "unknown",
            "conclusion": conclusion,
            "threshold_results": gate.get("checks") or [],
            "key_metrics": {
                "requests": performance.get("requests", 0),
                "errors": performance.get("errors", 0),
                "error_rate": performance.get("error_rate", 0),
                "average_ms": performance.get("average_ms", 0),
                "p95_ms": performance.get("p95_ms", 0),
                "p99_ms": performance.get("p99_ms", 0),
                "request_throughput_rps": performance.get("request_throughput_rps", performance.get("throughput_rps", 0)),
                "transaction_throughput_tps": performance.get("transaction_throughput_tps"),
            },
        },
        "bottleneck_analysis": {
            "confirmed_from_jtl": confirmed,
            "hypotheses": hypotheses,
            "evidence_required": evidence_boundary.get("requires_external_evidence") or [],
            "observability_status": observability_evidence.get("status") or "MISSING",
            "observability_signals": observability_evidence.get("signals") or [],
            "statement": "JTL只能确认慢请求、失败分布和客户端观测耗时；应用、数据库、中间件或网络根因必须由外部证据确认。",
        },
        "optimization_recommendations": recommendations,
        "baseline_comparison": baseline_comparison,
        "evidence_boundary": evidence_boundary,
        "observability_evidence": observability_evidence,
    }


def build_performance_ai_prompt(
    performance: dict[str, Any],
    gate: dict[str, Any],
    diagnosis: dict[str, Any],
    baseline_comparison: dict[str, Any],
    observability_evidence: dict[str, Any] | None = None,
) -> str:
    contract = {
        "risk_level": "PASS/P2/P1/P0",
        "conclusion": "是否达标的简明结论",
        "findings": [{"severity": "P0/P1/P2/INFO", "title": "标题", "detail": "证据化说明"}],
        "performance_assessment": {
            "status": "PASSED/FAILED",
            "conclusion": "性能评估",
        },
        "bottleneck_analysis": {
            "confirmed_from_jtl": [],
            "hypotheses": [],
            "evidence_required": [],
        },
        "optimization_recommendations": [
            {"priority": "P0/P1/P2", "action": "动作", "reason": "原因", "validation": "验证方法"}
        ],
    }
    evidence = {
        "performance": performance,
        "gate": gate,
        "diagnosis": diagnosis,
        "baseline_comparison": baseline_comparison,
        "observability_evidence": observability_evidence or diagnosis.get("observability") or {
            "status": "MISSING",
            "available_categories": [],
        },
    }
    return (
        "你是性能测试分析师。请只依据提供的JMeter指标、规则诊断和历史基线对比输出JSON。"
        "必须区分已确认事实与待验证假设；没有DB、Redis、APM、主机或网络监控证据时，"
        "不得断言瓶颈位于数据库、应用、中间件或网络。建议必须包含动作、原因和验证方式。"
        "不要输出Markdown。输出结构参考："
        + json.dumps(contract, ensure_ascii=False)
        + "\n输入证据："
        + json.dumps(evidence, ensure_ascii=False, default=str)[:30000]
    )


def merge_model_performance_review(
    built_in: dict[str, Any],
    model_payload: dict[str, Any],
    model: str,
) -> dict[str, Any]:
    if not isinstance(model_payload, dict):
        return built_in
    merged = dict(built_in)
    merged["mode"] = "configured_model"
    merged["model"] = model
    for key in (
        "risk_level",
        "conclusion",
        "findings",
        "recommendations",
        "performance_assessment",
        "bottleneck_analysis",
        "optimization_recommendations",
    ):
        value = model_payload.get(key)
        if value not in (None, "", [], {}):
            merged[key] = value
    merged["baseline_comparison"] = built_in.get("baseline_comparison") or {}
    merged["evidence_boundary"] = built_in.get("evidence_boundary") or {}
    merged["observability_evidence"] = built_in.get("observability_evidence") or {}
    return merged
