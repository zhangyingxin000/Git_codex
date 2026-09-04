from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from ...config import AppSettings
from ...services.route_coverage import build_route_coverage


def build_system_router(legacy: Any, settings: AppSettings) -> APIRouter:
    router = APIRouter(tags=["System"])

    @router.get("/api/health", summary="平台健康检查")
    def health(request: Request) -> dict[str, Any]:
        task_queue = getattr(request.app.state, "task_queue", None)
        return {
            "ok": True,
            "time": legacy.now(),
            "build": legacy.BUILD_ID,
            "frontend_build": legacy.BUILD_ID,
            "backend": "fastapi",
            "architecture": "modular-foundation",
            "demo_mode": settings.demo_mode,
            "external_mutations_allowed": settings.allow_mutations,
            "allowed_hosts": list(settings.allowed_hosts),
            "task_queue": {
                "enabled": task_queue is not None,
                "workers": settings.task_workers,
                "storage": str(settings.task_database),
            },
        }

    @router.get("/api/system/storage-policy", summary="查看平台存储与只读边界")
    def storage_policy() -> dict[str, Any]:
        return legacy.platform_storage_policy()

    @router.get("/api/system/environment-config", summary="查看YAML环境配置状态")
    def environment_config() -> dict[str, Any]:
        return legacy.environment_config_status()

    @router.get("/api/system/route-coverage", summary="路由与测试覆盖矩阵")
    def route_coverage(request: Request) -> dict[str, Any]:
        return build_route_coverage(request.app, settings.root / "tests")

    return router
