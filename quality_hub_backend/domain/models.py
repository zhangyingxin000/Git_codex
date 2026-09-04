from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class EvidenceStatus(StrEnum):
    pending = "PENDING"
    passed = "PASSED"
    failed = "FAILED"
    blocked = "BLOCKED"
    error = "ERROR"


class ToolKind(StrEnum):
    ai = "AI"
    newman = "NEWMAN"
    pytest = "PYTEST"
    jmeter = "JMETER"
    mysql = "MYSQL"
    redis = "REDIS"
    playwright = "PLAYWRIGHT"


class QualityArtifact(BaseModel):
    id: str
    project_id: str
    name: str
    artifact_type: Literal[
        "requirement",
        "test_point",
        "test_case",
        "postman_collection",
        "pytest_script",
        "jmeter_plan",
        "raw_report",
        "summary_report",
    ]
    source_path: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class ExecutionEvidence(BaseModel):
    id: str
    project_id: str
    tool: ToolKind
    command: list[str]
    status: EvidenceStatus
    started_at: datetime
    ended_at: datetime | None = None
    raw_report_path: str | None = None
    summary: str = ""
    redacted: bool = True


class DataValidationRule(BaseModel):
    id: str
    project_id: str
    api_endpoint_id: str
    mysql_table: str | None = None
    mysql_condition_template: str | None = None
    redis_key_pattern: str | None = None
    expectation: Literal["unchanged", "changed", "equals_api_response", "exists"] = (
        "unchanged"
    )
    readonly: bool = True


class QualityClosure(BaseModel):
    project_id: str
    requirement_count: int = 0
    test_case_count: int = 0
    interface_evidence_count: int = 0
    performance_evidence_count: int = 0
    data_validation_count: int = 0
    report_count: int = 0

    @property
    def maturity_score(self) -> int:
        checks = [
            self.requirement_count > 0,
            self.test_case_count > 0,
            self.interface_evidence_count > 0,
            self.performance_evidence_count > 0,
            self.data_validation_count > 0,
            self.report_count > 0,
        ]
        return round(sum(checks) / len(checks) * 100)
