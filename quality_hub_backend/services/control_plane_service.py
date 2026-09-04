from __future__ import annotations

from typing import Any

from ..repositories.sqlite_read_model import QualityReadModelRepository
from .diagnosis_service import ProjectDiagnosisService


class AIQualityControlPlaneService:
    """Describe the AI-led quality workflow for a project."""

    def __init__(
        self,
        repository: QualityReadModelRepository,
        diagnosis_service: ProjectDiagnosisService,
    ) -> None:
        self._repository = repository
        self._diagnosis_service = diagnosis_service

    def control_plane(self, project_id: str) -> dict[str, Any]:
        project = self._repository.project(project_id)
        if not project:
            raise ValueError("项目不存在")
        diagnosis = self._diagnosis_service.diagnose(project_id)
        counts = {
            "sources": len(self._repository.sources(project_id)),
            "requirements": len(self._repository.requirements(project_id)),
            "endpoints": len(self._repository.endpoints(project_id)),
            "cases": len(self._repository.test_cases(project_id)),
            "workflows": self._count(project_id, "workflows"),
            "suites": self._count(project_id, "automation_suites"),
            "performance_plans": self._count(project_id, "performance_plans"),
            "db_tables": len(self._repository.db_tables(project_id)),
            "redis_sources": len(self._repository.redis_sources(project_id)),
            "consistency_rules": len(self._repository.consistency_rules(project_id)),
            "consistency_runs": len(self._repository.consistency_runs(project_id)),
            "reports": len(self._repository.reports(project_id)),
        }
        stages = [
            self._stage(
                "资料理解",
                "识别需求、接口文档、HAR抓包、图片和描述",
                counts["sources"],
                "sources",
            ),
            self._stage(
                "资产生成",
                "生成测试点、用例、接口覆盖和风险",
                counts["requirements"] and counts["cases"],
                "sources",
            ),
            self._stage(
                "执行编排",
                "组织接口套件、业务流程、性能计划",
                counts["workflows"] or counts["suites"] or counts["performance_plans"],
                "automation",
            ),
            self._stage(
                "数据核对",
                "建立 MySQL/Redis 只读映射和一致性规则",
                counts["consistency_rules"],
                "dataquality",
            ),
            self._stage(
                "证据归档",
                "沉淀原始报告、失败归因和质量结论",
                counts["reports"],
                "reports",
            ),
        ]
        blockers = [item for item in diagnosis.items if item.severity.value == "P0"]
        attention = [item for item in diagnosis.items if item.severity.value == "P1"]
        next_item = blockers[0] if blockers else attention[0] if attention else None
        return {
            "project_id": project_id,
            "mode": "AI_ORCHESTRATION",
            "status": diagnosis.status,
            "counts": counts,
            "stages": stages,
            "next_action": {
                "title": next_item.title if next_item else "扩大测试范围",
                "description": (
                    next_item.description
                    if next_item
                    else "当前基础闭环已建立，可继续导入更多接口或执行回归。"
                ),
                "target": next_item.action_target if next_item else "sources",
                "severity": next_item.severity.value if next_item else "PASSED",
            },
            "principles": [
                "AI 负责理解、诊断、生成、编排和归纳",
                "接口、性能、数据校验由企业认可工具或只读数据源执行",
                "外部 MySQL/Redis 不写入，平台只沉淀本地资产与证据",
            ],
        }

    def _stage(
        self, name: str, description: str, ready: Any, target: str
    ) -> dict[str, Any]:
        return {
            "name": name,
            "description": description,
            "status": "READY" if ready else "PENDING",
            "target": target,
        }

    def _count(self, project_id: str, table: str) -> int:
        return self._repository.row(
            f"SELECT COUNT(*) n FROM {table} WHERE project_id=?", (project_id,)
        )["n"]
