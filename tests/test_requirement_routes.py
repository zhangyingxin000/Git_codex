from fastapi import FastAPI
from fastapi.testclient import TestClient

from quality_hub_backend.api.routes.requirement_execution import (
    build_requirement_execution_router,
)
from quality_hub_backend.api.routes.requirement_reports import build_requirement_report_router


class FakeLegacy:
    def generate_schema_api_test_cases(self, project_id, package_id, payload):
        return {"project_id": project_id, "package_id": package_id, "payload": payload}

    def generate_requirement_execution_plan(self, project_id, package_id, payload):
        return {"project_id": project_id, "package_id": package_id, "payload": payload}

    def requirement_package_report_index(self, project_id, package_id, refresh):
        return {"project_id": project_id, "package_id": package_id, "refresh": refresh}


def test_requirement_route_modules_keep_execution_and_report_paths() -> None:
    legacy = FakeLegacy()
    app = FastAPI()
    app.router.routes.extend(build_requirement_execution_router(legacy).routes)
    app.router.routes.extend(build_requirement_report_router(legacy).routes)
    paths = {route.path for route in app.routes}

    assert "/api/projects/{project_id}/requirement-packages/{package_id}/execution-plan" in paths
    assert "/api/projects/{project_id}/requirement-packages/{package_id}/api-test-cases" in paths
    assert "/api/projects/{project_id}/requirement-packages/{package_id}/pipeline/run" in paths
    assert "/api/projects/{project_id}/requirement-packages/{package_id}/jmeter-load-run" in paths
    assert "/api/projects/{project_id}/requirement-packages/{package_id}/report-index" in paths
    assert "/api/projects/{project_id}/requirement-packages/{package_id}/ai-review" in paths


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

    assert plan.json()["payload"] == {}
    assert report_index.json()["refresh"] is True


def test_requirement_report_router_preserves_openapi_tags() -> None:
    routes = build_requirement_report_router(FakeLegacy()).routes
    by_path = {route.path: route for route in routes}

    assert by_path[
        "/api/projects/{project_id}/requirement-packages/{package_id}/report-index"
    ].tags == ["Reports"]
    assert by_path[
        "/api/projects/{project_id}/requirement-packages/{package_id}/schema-audit"
    ].tags == ["Assets"]
