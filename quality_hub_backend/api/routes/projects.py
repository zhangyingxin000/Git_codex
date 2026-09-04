from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from ...schemas.requests import ProjectCreateRequest


def build_project_router(legacy: Any) -> APIRouter:
    router = APIRouter()

    @router.get("/api/projects/{project_id}/environment-config", tags=["Projects"], summary="项目YAML环境配置状态")
    def project_environment_config(project_id: str) -> dict[str, Any]:
        try:
            return legacy.environment_config_status(project_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get(
        "/api/projects/{project_id}/multi-account-context",
        tags=["Execution"],
        summary="多账号运行上下文",
    )
    def multi_account_context(project_id: str) -> dict[str, Any]:
        try:
            return legacy.multi_account_context_status(project_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get(
        "/api/projects/{project_id}/jmeter/generation-skill",
        tags=["Execution"],
        summary="JMeter脚本生成Skill",
    )
    def jmeter_generation_skill(project_id: str) -> dict[str, Any]:
        try:
            return legacy.jmeter_generation_skill_status(project_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/api/projects", tags=["Projects"], summary="项目列表")
    def projects() -> list[dict[str, Any]]:
        return legacy.rows("SELECT * FROM projects ORDER BY updated_at DESC")

    @router.post("/api/projects", status_code=201, tags=["Projects"], summary="创建项目")
    def create_project(payload: ProjectCreateRequest) -> dict[str, Any] | None:
        project_id = legacy.uid("prj")
        created_at = legacy.now()
        legacy.execute(
            "INSERT INTO projects VALUES (?,?,?,?,?,?)",
            (
                project_id,
                payload.name,
                payload.description,
                payload.base_url,
                created_at,
                created_at,
            ),
        )
        return legacy.row("SELECT * FROM projects WHERE id=?", (project_id,))

    @router.put("/api/projects/{project_id}", tags=["Projects"], summary="更新项目配置")
    def update_project(
        project_id: str,
        payload: dict[str, Any] = Body(default_factory=dict),
    ) -> dict[str, bool]:
        legacy.execute(
            "UPDATE projects SET name=?,description=?,base_url=?,updated_at=? WHERE id=?",
            (
                payload.get("name", ""),
                payload.get("description", ""),
                payload.get("base_url", ""),
                legacy.now(),
                project_id,
            ),
        )
        return {"ok": True}

    @router.get("/api/projects/{project_id}/dashboard", tags=["Projects"], summary="项目工作台聚合数据")
    def dashboard(project_id: str) -> dict[str, Any]:
        try:
            return legacy.project_dashboard(project_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/api/projects/{project_id}/diagnosis", tags=["Projects"], summary="平台自动缺口诊断")
    def diagnosis(project_id: str) -> dict[str, Any]:
        try:
            return legacy.project_quality_diagnosis(project_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/api/projects/{project_id}/control-plane", tags=["Projects"], summary="AI 自动化质量中枢控制面")
    def control_plane(project_id: str) -> dict[str, Any]:
        try:
            return legacy.project_control_plane(project_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get(
        "/api/projects/{project_id}/requirement-packages",
        tags=["Assets"],
        summary="需求包目录",
    )
    def requirement_packages(project_id: str) -> dict[str, Any]:
        return legacy.requirement_package_catalog(project_id)

    @router.post(
        "/api/projects/{project_id}/requirement-packages",
        status_code=201,
        tags=["Assets"],
        summary="创建需求包",
    )
    def create_requirement_package(
        project_id: str,
        payload: dict[str, Any] = Body(default_factory=dict),
    ) -> dict[str, Any]:
        return legacy.create_requirement_package(project_id, payload)

    @router.get(
        "/api/projects/{project_id}/requirement-packages/{package_id}/account-model",
        tags=["Assets"],
        summary="需求包账号模型",
    )
    def requirement_account_model(project_id: str, package_id: str) -> dict[str, Any]:
        return legacy.generate_requirement_account_model(project_id, package_id, True)

    @router.post(
        "/api/projects/{project_id}/requirement-packages/{package_id}/account-model",
        tags=["Assets"],
        summary="生成需求包账号模型",
    )
    def generate_requirement_account_model(project_id: str, package_id: str) -> dict[str, Any]:
        return legacy.generate_requirement_account_model(project_id, package_id, True)

    @router.get(
        "/api/projects/{project_id}/requirement-packages/{package_id}/resource-manifest",
        tags=["Data Validation"],
        summary="需求包资源登记",
    )
    def resource_manifest(project_id: str, package_id: str) -> dict[str, Any]:
        return legacy.requirement_resource_manifest(project_id, package_id, True)

    @router.post(
        "/api/projects/{project_id}/requirement-packages/{package_id}/resource-manifest",
        tags=["Data Validation"],
        summary="保存需求包资源登记",
    )
    def save_resource_manifest(
        project_id: str,
        package_id: str,
        payload: dict[str, Any] = Body(default_factory=dict),
    ) -> dict[str, Any]:
        return legacy.save_requirement_resource_manifest(project_id, package_id, payload)

    @router.get(
        "/api/projects/{project_id}/requirement-packages/{package_id}/resource-preflight",
        tags=["Data Validation"],
        summary="需求包资源预检",
    )
    def resource_preflight(project_id: str, package_id: str) -> dict[str, Any]:
        return legacy.requirement_resource_preflight(project_id, package_id)

    @router.post(
        "/api/projects/{project_id}/requirement-packages/{package_id}/resource-preflight",
        tags=["Data Validation"],
        summary="重新执行需求包资源预检",
    )
    def rerun_resource_preflight(project_id: str, package_id: str) -> dict[str, Any]:
        return legacy.requirement_resource_preflight(project_id, package_id)

    @router.get(
        "/api/projects/{project_id}/requirement-packages/{package_id}/evidence-rules",
        tags=["Data Validation"],
        summary="需求包证据规则",
    )
    def requirement_evidence_rules(project_id: str, package_id: str) -> dict[str, Any]:
        return legacy.requirement_evidence_rules(project_id, package_id)

    return router
