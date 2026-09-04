import time
from pathlib import Path

from fastapi.testclient import TestClient

from quality_hub_backend.api.fastapi_app import create_app
from quality_hub_backend.handlers import TaskDispatcher
from quality_hub_backend.services.task_queue import PersistentTaskQueue


def _wait(queue: PersistentTaskQueue, task_id: str) -> dict:
    deadline = time.time() + 5
    while time.time() < deadline:
        task = queue.get(task_id)
        if task and task["status"] in {"PASSED", "FAILED"}:
            return task
        time.sleep(0.02)
    raise AssertionError("background task did not finish")


def test_task_queue_persists_result(tmp_path: Path) -> None:
    database = tmp_path / "tasks.db"
    queue = PersistentTaskQueue(database, max_workers=1)
    task = queue.submit("example", {"value": 4}, lambda payload: {"answer": payload["value"] * 2})
    finished = _wait(queue, task["task_id"])
    queue.shutdown()

    reopened = PersistentTaskQueue(database, max_workers=1)
    persisted = reopened.get(task["task_id"])
    reopened.shutdown()

    assert finished["status"] == "PASSED"
    assert persisted is not None
    assert persisted["result"] == {"answer": 8}


class FakeLegacy:
    def __init__(self) -> None:
        self.calls = []

    def run_requirement_package_pipeline(self, project_id, package_id, options):
        self.calls.append(("pipeline", project_id, package_id, options))

    def run_requirement_package_pytest(self, project_id, package_id, options):
        self.calls.append(("pytest", project_id, package_id, options))

    def run_requirement_package_newman(self, project_id, package_id, options):
        self.calls.append(("newman", project_id, package_id, options))


def test_task_dispatcher_applies_safe_defaults() -> None:
    legacy = FakeLegacy()
    dispatcher = TaskDispatcher(legacy)
    payload = {"project_id": "project", "package_id": "package", "options": {"allow_mutations": True}}

    dispatcher.resolve("requirement_pipeline")(payload)
    dispatcher.resolve("requirement_newman")(payload)

    assert legacy.calls[0][3]["allow_mutations"] is False
    assert legacy.calls[1][3]["read_only_only"] is True


def test_task_routes_are_available() -> None:
    with TestClient(create_app()) as client:
        health = client.get("/api/health")
        task_types = client.get("/api/tasks/types")
        submitted = client.post("/api/tasks", json={"task_type": "demo_salary_trade"})
        task_id = submitted.json()["task_id"]
        deadline = time.time() + 5
        task_detail = None
        while time.time() < deadline:
            task_detail = client.get(f"/api/tasks/{task_id}")
            if task_detail.json()["status"] in {"PASSED", "FAILED"}:
                break
            time.sleep(0.05)

    assert health.status_code == 200
    assert health.json()["architecture"] == "modular-foundation"
    assert health.json()["task_queue"]["enabled"] is True
    assert task_types.status_code == 200
    assert "demo_salary_trade" in task_types.json()["task_types"]
    assert submitted.status_code == 202
    assert task_detail is not None
    assert task_detail.json()["status"] == "PASSED"
