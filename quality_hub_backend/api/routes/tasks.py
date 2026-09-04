from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from ...handlers import TaskDispatcher
from ...schemas.requests import BackgroundTaskCreateRequest
from ...services.task_queue import PersistentTaskQueue


def build_task_router(
    task_queue: PersistentTaskQueue,
    dispatcher: TaskDispatcher,
) -> APIRouter:
    router = APIRouter(prefix="/api/tasks", tags=["Execution"])

    @router.get("", summary="后台任务列表")
    def list_tasks(limit: int = Query(default=50, ge=1, le=200)) -> list[dict[str, Any]]:
        return task_queue.list(limit)

    @router.get("/types", summary="后台任务类型")
    def task_types() -> dict[str, Any]:
        return {"task_types": dispatcher.task_types}

    @router.get("/{task_id}", summary="后台任务详情")
    def get_task(task_id: str) -> dict[str, Any]:
        task = task_queue.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="后台任务不存在")
        return task

    @router.post("", status_code=202, summary="提交后台任务")
    def submit_task(payload: BackgroundTaskCreateRequest) -> dict[str, Any]:
        task_payload = payload.model_dump(exclude={"task_type"})
        try:
            handler = dispatcher.resolve(payload.task_type)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return task_queue.submit(payload.task_type, task_payload, handler)

    return router
