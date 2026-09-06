import time
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from quality_hub_backend.api.fastapi_app import create_app
from quality_hub_backend.config import AppSettings
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


def test_task_dispatcher_allows_explicit_test_environment_mutations() -> None:
    legacy = FakeLegacy()
    dispatcher = TaskDispatcher(legacy, SimpleNamespace(allow_mutations=True))
    payload = {"project_id": "project", "package_id": "package", "options": {"allow_mutations": True}}

    dispatcher.resolve("requirement_pipeline")(payload)
    dispatcher.resolve("requirement_newman")(payload)

    assert legacy.calls[0][3]["allow_mutations"] is True
    assert legacy.calls[0][3]["mutations_allowed_by_platform"] is True
    assert legacy.calls[1][3]["read_only_only"] is False


def test_yaml_enables_real_test_mode_but_demo_stays_readonly(tmp_path: Path, monkeypatch) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "env.test.yaml").write_text(
        "execution:\n  allow_mutations: true\n  allow_high_risk: false\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("AUTOTEST_ALLOW_MUTATIONS", "false")
    monkeypatch.delenv("AUTOTEST_DEMO_MODE", raising=False)

    assert AppSettings.from_environment(tmp_path).allow_mutations is True

    monkeypatch.setenv("AUTOTEST_DEMO_MODE", "true")
    assert AppSettings.from_environment(tmp_path).allow_mutations is False


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


def test_task_queue_persists_progress_and_cancels_running_task(tmp_path: Path) -> None:
    queue = PersistentTaskQueue(tmp_path / "tasks.db", max_workers=1)

    def handler(payload):
        context = payload["_task_context"]
        context["progress"]({"phase": "running", "percent": 25, "message": "started"})
        deadline = time.time() + 3
        while time.time() < deadline:
            if context["is_cancelled"]():
                return {"status": "CANCELLED"}
            time.sleep(0.02)
        return {"status": "PASSED"}

    submitted = queue.submit("cancel-test", {}, handler)
    task_id = submitted["task_id"]
    deadline = time.time() + 2
    running = None
    while time.time() < deadline:
        running = queue.get(task_id)
        if running and running["status"] == "RUNNING" and running["progress"].get("percent") == 25:
            break
        time.sleep(0.02)

    queue.request_cancel(task_id)
    deadline = time.time() + 2
    cancelled = None
    while time.time() < deadline:
        cancelled = queue.get(task_id)
        if cancelled and cancelled["status"] == "CANCELLED":
            break
        time.sleep(0.02)
    queue.shutdown()

    assert running is not None
    assert running["progress"]["phase"] == "running"
    assert cancelled is not None
    assert cancelled["status"] == "CANCELLED"
    assert cancelled["cancel_requested"] == 1


def test_task_queue_propagates_failed_business_result(tmp_path: Path) -> None:
    queue = PersistentTaskQueue(tmp_path / "tasks.db", max_workers=1)
    task = queue.submit("failed-result", {}, lambda _: {"status": "FAILED", "message": "gate failed"})
    finished = _wait(queue, task["task_id"])
    queue.shutdown()

    assert finished["status"] == "FAILED"
    assert finished["result"]["message"] == "gate failed"
