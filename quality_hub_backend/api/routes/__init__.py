"""FastAPI router modules."""

from .mobile import build_mobile_router
from .projects import build_project_router
from .requirement_execution import build_requirement_execution_router
from .requirement_reports import build_requirement_report_router
from .system import build_system_router
from .tasks import build_task_router

__all__ = [
    "build_mobile_router",
    "build_project_router",
    "build_requirement_execution_router",
    "build_requirement_report_router",
    "build_system_router",
    "build_task_router",
]
