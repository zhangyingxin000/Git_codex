from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class DiagnosisSeverity(StrEnum):
    p0 = "P0"
    p1 = "P1"
    p2 = "P2"
    passed = "PASSED"


QualityModule = Literal["overview", "sources", "automation", "dataquality", "reports"]


class DiagnosisItem(BaseModel):
    id: str
    severity: DiagnosisSeverity
    module: QualityModule
    title: str
    description: str
    action_label: str
    action_target: QualityModule
    details: list[dict[str, Any]] = Field(default_factory=list)


class DiagnosisSummary(BaseModel):
    total: int = 0
    p0: int = 0
    p1: int = 0
    p2: int = 0
    modules: dict[str, int] = Field(default_factory=dict)


class ReadonlyPolicy(BaseModel):
    external_mysql: bool = True
    external_redis: bool = True
    platform_local_storage: bool = True


class ProjectDiagnosis(BaseModel):
    project_id: str
    generated_at: datetime
    status: Literal["PASSED", "ATTENTION", "BLOCKED"]
    summary: DiagnosisSummary
    items: list[DiagnosisItem]
    readonly_policy: ReadonlyPolicy = Field(default_factory=ReadonlyPolicy)
