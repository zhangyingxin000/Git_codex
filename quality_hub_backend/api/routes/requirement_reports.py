from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body


def build_requirement_report_router(legacy: Any) -> APIRouter:
    router = APIRouter()

    @router.post("/api/projects/{project_id}/requirement-packages/{package_id}/scenario-report", tags=["Reports"], summary="生成需求包统一场景报告")
    def requirement_scenario_report(project_id: str, package_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.generate_requirement_package_unified_scenario_report(project_id, package_id, payload)

    @router.get("/api/projects/{project_id}/requirement-packages/{package_id}/report-index", tags=["Reports"], summary="需求包运行批次与报告索引")
    def requirement_report_index(project_id: str, package_id: str) -> dict[str, Any]:
        return legacy.requirement_package_report_index(project_id, package_id, True)

    @router.get(
        "/api/projects/{project_id}/requirement-packages/{package_id}/report-retention-preview",
        tags=["Reports"],
        summary="需求包报告保留与清理预览",
    )
    def requirement_report_retention_preview(project_id: str, package_id: str) -> dict[str, Any]:
        return legacy.requirement_package_report_retention_preview(project_id, package_id)

    @router.get(
        "/api/projects/{project_id}/requirement-packages/{package_id}/schema-audit",
        tags=["Assets"],
        summary="需求包Schema校验",
    )
    def requirement_schema_audit(project_id: str, package_id: str) -> dict[str, Any]:
        return legacy.validate_requirement_package_schemas(project_id, package_id, True)

    @router.post(
        "/api/projects/{project_id}/requirement-packages/{package_id}/schema-upgrade",
        tags=["Assets"],
        summary="需求包Schema兼容升级",
    )
    def requirement_schema_upgrade(project_id: str, package_id: str) -> dict[str, Any]:
        return legacy.upgrade_requirement_package_schemas(project_id, package_id)

    @router.post("/api/projects/{project_id}/requirement-packages/{package_id}/ai-review", tags=["Reports"], summary="生成需求包AI复盘")
    def requirement_ai_review(project_id: str, package_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.generate_requirement_package_ai_review(project_id, package_id, payload)

    @router.post("/api/projects/{project_id}/requirement-packages/{package_id}/performance-ai-review", tags=["Reports"], summary="生成当前批次性能报告AI分析")
    def requirement_performance_ai_review(project_id: str, package_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.generate_requirement_performance_ai_review(project_id, package_id, payload)

    @router.post(
        "/api/projects/{project_id}/requirement-packages/{package_id}/performance-baselines/{run_id}/approve",
        tags=["Reports"],
        summary="批准当前性能批次为正式基线",
    )
    def requirement_performance_baseline_approve(
        project_id: str,
        package_id: str,
        run_id: str,
        payload: dict[str, Any] = Body(default_factory=dict),
    ) -> dict[str, Any]:
        return legacy.approve_requirement_performance_baseline(
            project_id,
            package_id,
            run_id,
            payload.get("approved_by") or "manual",
        )

    @router.post("/api/projects/{project_id}/requirement-packages/{package_id}/newman-analysis", tags=["Reports"], summary="生成当前批次Newman接口冒烟分析")
    def requirement_newman_analysis(project_id: str, package_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.generate_requirement_newman_analysis(project_id, package_id, payload)

    return router
