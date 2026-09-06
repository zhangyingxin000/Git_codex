from fastapi import FastAPI
from fastapi.testclient import TestClient

from quality_hub_backend.api.routes.requirement_execution import (
    build_requirement_execution_router,
)
from quality_hub_backend.api.routes.requirement_reports import build_requirement_report_router


class FakeLegacy:
    def generate_schema_api_test_cases(self, project_id, package_id, payload):
        return {"project_id": project_id, "package_id": package_id, "payload": payload}

    def compile_requirement_api_test_assets(self, project_id, package_id, payload):
        return {"project_id": project_id, "package_id": package_id, "kind": "compiled", "payload": payload}

    def run_requirement_api_interface_tests(self, project_id, package_id, payload):
        return {"project_id": project_id, "package_id": package_id, "kind": "executed", "payload": payload}

    def generate_requirement_regression_selection(self, project_id, package_id, payload):
        return {"project_id": project_id, "package_id": package_id, "kind": "regression", "payload": payload}

    def generate_requirement_execution_plan(self, project_id, package_id, payload):
        return {"project_id": project_id, "package_id": package_id, "payload": payload}

    def requirement_package_report_index(self, project_id, package_id, refresh):
        return {"project_id": project_id, "package_id": package_id, "refresh": refresh}

    def approve_requirement_performance_baseline(self, project_id, package_id, run_id, approved_by):
        return {
            "project_id": project_id,
            "package_id": package_id,
            "run_id": run_id,
            "approved_by": approved_by,
        }

    def requirement_performance_options(self, project_id, package_id):
        return {"project_id": project_id, "package_id": package_id, "profiles": ["baseline"]}


def test_requirement_route_modules_keep_execution_and_report_paths() -> None:
    legacy = FakeLegacy()
    app = FastAPI()
    app.router.routes.extend(build_requirement_execution_router(legacy).routes)
    app.router.routes.extend(build_requirement_report_router(legacy).routes)
    paths = {route.path for route in app.routes}

    assert "/api/projects/{project_id}/requirement-packages/{package_id}/execution-plan" in paths
    assert "/api/projects/{project_id}/requirement-packages/{package_id}/api-test-cases" in paths
    assert "/api/projects/{project_id}/requirement-packages/{package_id}/interface-tests/compile" in paths
    assert "/api/projects/{project_id}/requirement-packages/{package_id}/interface-tests/newman/run" in paths
    assert "/api/projects/{project_id}/requirement-packages/{package_id}/regression-selection" in paths
    assert "/api/projects/{project_id}/requirement-packages/{package_id}/pipeline/run" in paths
    assert "/api/projects/{project_id}/requirement-packages/{package_id}/jmeter-load-run" in paths
    assert "/api/projects/{project_id}/requirement-packages/{package_id}/performance-options" in paths
    assert "/api/projects/{project_id}/requirement-packages/{package_id}/report-index" in paths
    assert "/api/projects/{project_id}/requirement-packages/{package_id}/ai-review" in paths
    assert "/api/projects/{project_id}/requirement-packages/{package_id}/performance-baselines/{run_id}/approve" in paths


def test_requirement_route_modules_preserve_read_behavior() -> None:
    legacy = FakeLegacy()
    app = FastAPI()
    app.router.routes.extend(build_requirement_execution_router(legacy).routes)
    app.router.routes.extend(build_requirement_report_router(legacy).routes)
    client = TestClient(app)

    plan = client.get(
        "/api/projects/project-1/requirement-packages/salary-trade/execution-plan"
    )
    report_index = client.get(
        "/api/projects/project-1/requirement-packages/salary-trade/report-index"
    )
    performance_options = client.get(
        "/api/projects/project-1/requirement-packages/salary-trade/performance-options"
    )

    assert plan.json()["payload"] == {}
    assert report_index.json()["refresh"] is True
    assert performance_options.json()["profiles"] == ["baseline"]


def test_interface_test_routes_keep_design_compile_execute_order() -> None:
    app = FastAPI()
    app.router.routes.extend(build_requirement_execution_router(FakeLegacy()).routes)
    client = TestClient(app)

    compiled = client.post(
        "/api/projects/project-1/requirement-packages/salary-trade/interface-tests/compile",
        json={"regenerate_cases": False},
    )
    executed = client.post(
        "/api/projects/project-1/requirement-packages/salary-trade/interface-tests/newman/run",
        json={"run_id": "run-1"},
    )

    assert compiled.json()["kind"] == "compiled"
    assert executed.json()["kind"] == "executed"


def test_requirement_regression_selection_route_preserves_change_scope() -> None:
    app = FastAPI()
    app.router.routes.extend(build_requirement_execution_router(FakeLegacy()).routes)
    client = TestClient(app)

    response = client.post(
        "/api/projects/project-1/requirement-packages/salary-trade/regression-selection",
        json={"changed_tables": ["anchor_salary_trade_order"]},
    )

    assert response.json()["kind"] == "regression"
    assert response.json()["payload"]["changed_tables"] == ["anchor_salary_trade_order"]


def test_requirement_report_router_preserves_openapi_tags() -> None:
    routes = build_requirement_report_router(FakeLegacy()).routes
    by_path = {route.path: route for route in routes}

    assert by_path[
        "/api/projects/{project_id}/requirement-packages/{package_id}/report-index"
    ].tags == ["Reports"]
    assert by_path[
        "/api/projects/{project_id}/requirement-packages/{package_id}/schema-audit"
    ].tags == ["Assets"]


def test_performance_baseline_approval_route_keeps_manual_actor() -> None:
    app = FastAPI()
    app.router.routes.extend(build_requirement_report_router(FakeLegacy()).routes)
    client = TestClient(app)

    response = client.post(
        "/api/projects/project-1/requirement-packages/salary-trade/performance-baselines/run-1/approve",
        json={"approved_by": "tester"},
    )

    assert response.status_code == 200
    assert response.json()["run_id"] == "run-1"
    assert response.json()["approved_by"] == "tester"
