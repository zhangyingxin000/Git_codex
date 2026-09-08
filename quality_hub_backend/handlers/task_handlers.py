from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from quality_hub_backend.demo.salary_trade import run_demo
from quality_hub_backend.services.mobile_automation import MobileAutomationService


class TaskDispatcher:
    def __init__(
        self,
        legacy: Any,
        settings: Any = None,
        mobile_automation: MobileAutomationService | None = None,
    ) -> None:
        self.legacy = legacy
        self.allow_mutations = bool(getattr(settings, "allow_mutations", False))
        self._handlers: dict[str, Callable[[dict[str, Any]], Any]] = {
            "demo_salary_trade": lambda _: run_demo(),
            "requirement_pipeline": self._requirement_pipeline,
            "requirement_pytest": self._requirement_pytest,
            "requirement_newman": self._requirement_newman,
            "requirement_performance": self._requirement_performance,
        }
        root = getattr(legacy, "ROOT", None)
        self.mobile_automation = mobile_automation or (
            MobileAutomationService(Path(root)) if root is not None else None
        )
        if self.mobile_automation is not None:
            self._handlers["mobile_appium"] = self._mobile_appium

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
        if isinstance(payload.get("_task_context"), dict):
            options = {**options, "_task_context": payload["_task_context"]}
        return project_id, package_id, options

    def _requirement_pipeline(self, payload: dict[str, Any]) -> Any:
        project_id, package_id, options = self._scope(payload)
        requested = bool(options.get("allow_mutations"))
        options = {
            **options,
            "allow_mutations": requested and self.allow_mutations,
            "mutations_requested": requested,
            "mutations_allowed_by_platform": self.allow_mutations,
        }
        return self.legacy.run_requirement_package_pipeline(project_id, package_id, options)

    def _requirement_pytest(self, payload: dict[str, Any]) -> Any:
        project_id, package_id, options = self._scope(payload)
        return self.legacy.run_requirement_package_pytest(project_id, package_id, options)

    def _requirement_newman(self, payload: dict[str, Any]) -> Any:
        project_id, package_id, options = self._scope(payload)
        requested = bool(options.get("allow_mutations"))
        mutations_enabled = requested and self.allow_mutations
        options = {
            **options,
            "allow_mutations": mutations_enabled,
            "read_only_only": not mutations_enabled,
        }
        return self.legacy.run_requirement_package_newman(project_id, package_id, options)

    def _requirement_performance(self, payload: dict[str, Any]) -> Any:
        project_id, package_id, options = self._scope(payload)
        context = options.get("_task_context") if isinstance(options.get("_task_context"), dict) else {}
        progress = context.get("progress") if callable(context.get("progress")) else None
        is_cancelled = context.get("is_cancelled") if callable(context.get("is_cancelled")) else None
        if not options.get("all_stages"):
            return self.legacy.run_requirement_jmeter_load_stage(project_id, package_id, options)

        plan = self.legacy.generate_requirement_jmeter_load_plan(project_id, package_id, options)
        stages = plan.get("stages") or []
        results = []
        for index, stage in enumerate(stages, start=1):
            if is_cancelled and is_cancelled():
                return {"status": "CANCELLED", "stages": results, "message": "用户停止了性能任务。"}
            if progress:
                progress({
                    "phase": "stage",
                    "percent": int((index - 1) / max(len(stages), 1) * 100),
                    "message": f"正在执行第{index}/{len(stages)}阶段：{stage.get('name') or stage.get('code')}",
                })
            result = self.legacy.run_requirement_jmeter_load_stage(
                project_id,
                package_id,
                {**options, "stage": stage.get("stage") or index},
            )
            results.append(result)
            if str(result.get("status") or "").upper() != "PASSED":
                return {
                    "status": str(result.get("status") or "FAILED").upper(),
                    "stages": results,
                    "message": "性能门槛或执行状态未通过，后续阶梯已停止。",
                }
        return {"status": "PASSED", "stages": results, "message": "全部性能阶梯执行完成。"}

    def _mobile_appium(self, payload: dict[str, Any]) -> Any:
        if self.mobile_automation is None:
            return {"status": "BLOCKED", "message": "移动端自动化服务尚未初始化。"}
        return self.mobile_automation.run(payload)
