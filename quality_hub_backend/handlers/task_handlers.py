from __future__ import annotations

from typing import Any, Callable

from quality_hub_backend.demo.salary_trade import run_demo


class TaskDispatcher:
    def __init__(self, legacy: Any) -> None:
        self.legacy = legacy
        self._handlers: dict[str, Callable[[dict[str, Any]], Any]] = {
            "demo_salary_trade": lambda _: run_demo(),
            "requirement_pipeline": self._requirement_pipeline,
            "requirement_pytest": self._requirement_pytest,
            "requirement_newman": self._requirement_newman,
        }

    @property
    def task_types(self) -> tuple[str, ...]:
        return tuple(self._handlers)

    def resolve(self, task_type: str) -> Callable[[dict[str, Any]], Any]:
        try:
            return self._handlers[task_type]
        except KeyError as exc:
            raise ValueError(f"Unsupported task type: {task_type}") from exc

    @staticmethod
    def _scope(payload: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
        project_id = str(payload.get("project_id") or "").strip()
        package_id = str(payload.get("package_id") or "").strip()
        if not project_id or not package_id:
            raise ValueError("project_id and package_id are required")
        options = payload.get("options") if isinstance(payload.get("options"), dict) else {}
        return project_id, package_id, options

    def _requirement_pipeline(self, payload: dict[str, Any]) -> Any:
        project_id, package_id, options = self._scope(payload)
        options = {**options, "allow_mutations": False}
        return self.legacy.run_requirement_package_pipeline(project_id, package_id, options)

    def _requirement_pytest(self, payload: dict[str, Any]) -> Any:
        project_id, package_id, options = self._scope(payload)
        return self.legacy.run_requirement_package_pytest(project_id, package_id, options)

    def _requirement_newman(self, payload: dict[str, Any]) -> Any:
        project_id, package_id, options = self._scope(payload)
        options = {**options, "read_only_only": True}
        return self.legacy.run_requirement_package_newman(project_id, package_id, options)
