from fastapi import FastAPI
from fastapi.testclient import TestClient

from quality_hub_backend.api.routes.projects import build_project_router


class FakeLegacy:
    def __init__(self) -> None:
        self.executed = []

    def rows(self, query):
        assert "FROM projects" in query
        return [{"id": "project-1", "name": "Demo"}]

    def execute(self, query, parameters):
        self.executed.append((query, parameters))

    def row(self, query, parameters):
        return {"id": parameters[0], "name": "Created"}

    def uid(self, prefix):
        return f"{prefix}-created"

    def now(self):
        return "2026-09-04T00:00:00Z"

    def project_dashboard(self, project_id):
        if project_id == "missing":
            raise ValueError("项目不存在")
        return {"project": {"id": project_id}}

    def project_quality_diagnosis(self, project_id):
        return {"project_id": project_id, "status": "READY"}

    def project_control_plane(self, project_id):
        return {"project_id": project_id, "status": "READY"}

    def environment_config_status(self, project_id):
        return {"project_id": project_id, "status": "READY"}

    def multi_account_context_status(self, project_id):
        return {"project_id": project_id, "roles": []}

    def jmeter_generation_skill_status(self, project_id):
        return {"project_id": project_id, "status": "READY"}

    def requirement_package_catalog(self, project_id):
        return {"project_id": project_id, "packages": []}

    def create_requirement_package(self, project_id, payload):
        return {"project_id": project_id, "package": payload}

    def generate_requirement_account_model(self, project_id, package_id, write):
        return {"project_id": project_id, "package_id": package_id, "write": write}

    def requirement_resource_manifest(self, project_id, package_id, write):
        return {"project_id": project_id, "package_id": package_id, "write": write}

    def save_requirement_resource_manifest(self, project_id, package_id, payload):
        return {"project_id": project_id, "package_id": package_id, "payload": payload}

    def requirement_resource_preflight(self, project_id, package_id):
        return {"project_id": project_id, "package_id": package_id, "status": "READY"}

    def requirement_evidence_rules(self, project_id, package_id):
        return {"project_id": project_id, "package_id": package_id, "rules": []}


def _client() -> tuple[TestClient, FakeLegacy]:
    legacy = FakeLegacy()
    app = FastAPI()
    app.router.routes.extend(build_project_router(legacy).routes)
    return TestClient(app), legacy


def test_project_router_preserves_project_endpoints() -> None:
    client, legacy = _client()

    assert client.get("/api/projects").json()[0]["id"] == "project-1"
    assert client.get("/api/projects/project-1/dashboard").status_code == 200
    assert client.get("/api/projects/missing/dashboard").status_code == 404
    assert client.put(
        "/api/projects/project-1",
        json={"name": "Updated", "description": "Desc", "base_url": "http://localhost"},
    ).json() == {"ok": True}
    assert legacy.executed[-1][1][-1] == "project-1"


def test_project_router_preserves_requirement_package_endpoints() -> None:
    client, _ = _client()

    catalog = client.get("/api/projects/project-1/requirement-packages")
    preflight = client.get(
        "/api/projects/project-1/requirement-packages/salary-trade/resource-preflight"
    )
    saved = client.post(
        "/api/projects/project-1/requirement-packages/salary-trade/resource-manifest",
        json={"datasets": []},
    )

    assert catalog.status_code == 200
    assert preflight.json()["status"] == "READY"
    assert saved.json()["payload"] == {"datasets": []}


def test_project_router_preserves_openapi_tags() -> None:
    legacy = FakeLegacy()
    routes = build_project_router(legacy).routes
    by_path = {route.path: route for route in routes}

    assert by_path["/api/projects"].tags == ["Projects"]
    assert by_path["/api/projects/{project_id}/requirement-packages"].tags == ["Assets"]
    assert by_path["/api/projects/{project_id}/multi-account-context"].tags == ["Execution"]
