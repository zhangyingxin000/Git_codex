from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from ...services.mobile_automation import MobileAutomationService


def build_mobile_router(service: MobileAutomationService) -> APIRouter:
    router = APIRouter(prefix="/api/mobile", tags=["Execution"])

    @router.get("/catalog", summary="移动端设备、页面对象和场景目录")
    def mobile_catalog(config_path: str = Query(default="", max_length=260)) -> dict[str, Any]:
        return service.catalog(config_path)

    return router
