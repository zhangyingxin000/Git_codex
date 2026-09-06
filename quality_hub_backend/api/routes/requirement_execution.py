from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body


def build_requirement_execution_router(legacy: Any) -> APIRouter:
    router = APIRouter(tags=["Execution"])

    @router.post(
        "/api/projects/{project_id}/requirement-packages/{package_id}/api-test-cases",
        tags=["Assets"],
        summary="按Schema生成接口测试用例设计",
    )
    def schema_api_test_cases(
        project_id: str,
        package_id: str,
        payload: dict[str, Any] = Body(default_factory=dict),
    ) -> dict[str, Any]:
        return legacy.generate_schema_api_test_cases(project_id, package_id, payload)

    @router.post(
        "/api/projects/{project_id}/requirement-packages/{package_id}/interface-tests/compile",
        tags=["Assets"],
        summary="把接口测试用例编译为可执行Newman集合",
    )
    def compile_interface_tests(
        project_id: str,
        package_id: str,
        payload: dict[str, Any] = Body(default_factory=dict),
    ) -> dict[str, Any]:
        return legacy.compile_requirement_api_test_assets(project_id, package_id, payload)

    @router.post(
        "/api/projects/{project_id}/requirement-packages/{package_id}/interface-tests/newman/run",
        summary="执行接口测试用例Newman集合并按用例ID回收结果",
    )
    def run_interface_tests(
        project_id: str,
        package_id: str,
        payload: dict[str, Any] = Body(default_factory=dict),
    ) -> dict[str, Any]:
        return legacy.run_requirement_api_interface_tests(project_id, package_id, payload)

    @router.post(
        "/api/projects/{project_id}/requirement-packages/{package_id}/regression-selection",
        tags=["Assets"],
        summary="按变更范围选择需求回归用例",
    )
    def requirement_regression_selection(
        project_id: str,
        package_id: str,
        payload: dict[str, Any] = Body(default_factory=dict),
    ) -> dict[str, Any]:
        return legacy.generate_requirement_regression_selection(project_id, package_id, payload)

    @router.get("/api/projects/{project_id}/requirement-packages/{package_id}/execution-plan", summary="需求包场景计划")
    def requirement_execution_plan(project_id: str, package_id: str) -> dict[str, Any]:
        return legacy.generate_requirement_execution_plan(project_id, package_id, {})

    @router.post("/api/projects/{project_id}/requirement-packages/{package_id}/execution-plan", summary="生成需求包场景计划")
    def generate_requirement_execution_plan(project_id: str, package_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.generate_requirement_execution_plan(project_id, package_id, payload)

    @router.post("/api/projects/{project_id}/requirement-packages/{package_id}/tool-assets", summary="生成需求包工具资产")
    def requirement_tool_assets(project_id: str, package_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.generate_requirement_package_tool_assets(project_id, package_id, payload)

    @router.post("/api/projects/{project_id}/requirement-packages/{package_id}/runs", summary="创建需求包统一运行批次")
    def create_requirement_run(project_id: str, package_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.create_requirement_run_context(project_id, package_id, payload)

    @router.get("/api/projects/{project_id}/requirement-packages/{package_id}/runs", summary="需求包运行批次")
    def requirement_runs(project_id: str, package_id: str) -> dict[str, Any]:
        return legacy.list_requirement_run_contexts(project_id, package_id)

    @router.get("/api/projects/{project_id}/requirement-packages/{package_id}/runs/{run_id}", summary="需求包运行批次详情")
    def requirement_run(project_id: str, package_id: str, run_id: str) -> dict[str, Any]:
        return legacy.get_requirement_run_context(project_id, package_id, run_id)

    @router.post("/api/projects/{project_id}/requirement-packages/{package_id}/newman/run", summary="运行需求包Newman")
    def requirement_newman_run(project_id: str, package_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.run_requirement_package_newman(project_id, package_id, payload)

    @router.post("/api/projects/{project_id}/requirement-packages/{package_id}/pytest/run", summary="运行需求包pytest证据复核")
    def requirement_pytest_run(project_id: str, package_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.run_requirement_package_pytest(project_id, package_id, payload)

    @router.post("/api/projects/{project_id}/requirement-packages/{package_id}/pipeline/run", summary="一键执行当前需求包闭环")
    def requirement_pipeline_run(project_id: str, package_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.run_requirement_package_pipeline(project_id, package_id, payload)

    @router.post("/api/projects/{project_id}/salary-trade/jmeter-harvest", summary="回收工资交易JMeter执行报告")
    def salary_trade_jmeter_harvest(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.harvest_salary_trade_jmeter_mapping(project_id, payload)

    @router.post("/api/projects/{project_id}/requirement-packages/{package_id}/jmeter-load-plan", summary="生成可执行JMeter持续压测预案")
    def requirement_jmeter_load_plan(project_id: str, package_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.generate_requirement_jmeter_load_plan(project_id, package_id, payload)

    @router.get(
        "/api/projects/{project_id}/requirement-packages/{package_id}/performance-options",
        summary="读取性能Profile、目标接口与默认参数",
    )
    def requirement_performance_options(project_id: str, package_id: str) -> dict[str, Any]:
        return legacy.requirement_performance_options(project_id, package_id)

    @router.post("/api/projects/{project_id}/requirement-packages/{package_id}/jmeter-load-run", summary="执行JMeter持续压测阶梯并回收JTL与HTML")
    def requirement_jmeter_load_run(project_id: str, package_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.run_requirement_jmeter_load_stage(project_id, package_id, payload)

    return router
