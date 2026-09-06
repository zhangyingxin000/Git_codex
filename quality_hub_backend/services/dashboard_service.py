from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..repositories.sqlite_read_model import QualityReadModelRepository
from .diagnosis_service import ProjectDiagnosisService

if TYPE_CHECKING:
    from .control_plane_service import AIQualityControlPlaneService


class ProjectDashboardService:
    """Build the workspace read model consumed by the frontend."""

    def __init__(
        self,
        repository: QualityReadModelRepository,
        diagnosis_service: ProjectDiagnosisService,
        control_plane_service: AIQualityControlPlaneService,
    ) -> None:
        self._repository = repository
        self._diagnosis_service = diagnosis_service
        self._control_plane_service = control_plane_service

    def dashboard(self, project_id: str) -> dict[str, Any]:
        project = self._repository.project(project_id)
        if not project:
            raise ValueError("项目不存在")

        workflows = self._repository.rows(
            "SELECT * FROM workflows WHERE project_id=? ORDER BY priority,risk_level DESC,name",
            (project_id,),
        )
        return {
            "project": project,
            "sources": self._repository.rows(
                "SELECT id,name,kind,created_at FROM sources WHERE project_id=? ORDER BY created_at DESC",
                (project_id,),
            ),
            "requirement_items": self._repository.rows(
                "SELECT * FROM requirement_items WHERE project_id=? ORDER BY created_at DESC",
                (project_id,),
            ),
            "trace_links": self._repository.rows(
                """
                SELECT id,requirement_id,target_type,target_id,confidence,reason,selected,sort_order
                FROM trace_links
                WHERE project_id=? AND target_type='endpoint'
                ORDER BY confidence DESC
                """,
                (project_id,),
            ),
            "points": self._repository.rows(
                "SELECT * FROM test_points WHERE project_id=? ORDER BY created_at DESC",
                (project_id,),
            ),
            "cases": self._repository.rows(
                "SELECT * FROM test_cases WHERE project_id=? ORDER BY created_at DESC",
                (project_id,),
            ),
            "endpoints": self._repository.rows(
                "SELECT * FROM api_endpoints WHERE project_id=? ORDER BY danger_score DESC,path",
                (project_id,),
            ),
            "db_tables": self._repository.rows(
                "SELECT table_name,table_comment,approx_rows,module FROM db_tables WHERE project_id=? ORDER BY table_name",
                (project_id,),
            ),
            "mappings": self._repository.rows(
                "SELECT * FROM api_db_mappings WHERE project_id=? ORDER BY confidence DESC LIMIT 500",
                (project_id,),
            ),
            "redis_sources": self._repository.rows(
                "SELECT * FROM redis_sources WHERE project_id=? ORDER BY created_at DESC",
                (project_id,),
            ),
            "redis_snapshots": self._repository.rows(
                "SELECT id,redis_source_id,key_name,key_type,ttl,value_hash,captured_at FROM redis_key_snapshots WHERE project_id=? ORDER BY captured_at DESC LIMIT 100",
                (project_id,),
            ),
            "workflows": workflows,
            "workflow_steps": self._repository.rows(
                """
                SELECT s.*
                FROM workflow_steps s
                JOIN workflows w ON w.id=s.workflow_id
                WHERE w.project_id=?
                ORDER BY s.workflow_id,s.step_order
                """,
                (project_id,),
            ),
            "workflow_runs": self._repository.rows(
                """
                SELECT r.*,w.name workflow_name
                FROM workflow_runs r
                JOIN workflows w ON w.id=r.workflow_id
                WHERE r.project_id=?
                ORDER BY r.created_at DESC
                LIMIT 100
                """,
                (project_id,),
            ),
            "batches": self._repository.rows(
                "SELECT * FROM import_batches WHERE project_id=? ORDER BY version_no DESC",
                (project_id,),
            ),
            "changes": self._repository.rows(
                "SELECT * FROM endpoint_changes WHERE project_id=? ORDER BY created_at DESC LIMIT 1000",
                (project_id,),
            ),
            "automation_suites": self._repository.rows(
                "SELECT * FROM automation_suites WHERE project_id=? ORDER BY name",
                (project_id,),
            ),
            "performance_plans": self._repository.rows(
                "SELECT * FROM performance_plans WHERE project_id=? ORDER BY danger_score DESC,name",
                (project_id,),
            ),
            "performance_runs": self._repository.rows(
                """
                SELECT r.*,p.name plan_name
                FROM performance_runs r
                JOIN performance_plans p ON p.id=r.plan_id
                WHERE r.project_id=?
                ORDER BY r.created_at DESC
                LIMIT 100
                """,
                (project_id,),
            ),
            "fault_scenarios": self._repository.rows(
                "SELECT * FROM fault_scenarios WHERE project_id=? ORDER BY danger_score DESC,name",
                (project_id,),
            ),
            "security_scans": self._repository.rows(
                "SELECT * FROM security_scans WHERE project_id=? ORDER BY created_at DESC LIMIT 50",
                (project_id,),
            ),
            "security_findings": self._repository.rows(
                """
                SELECT *
                FROM security_findings
                WHERE project_id=?
                ORDER BY CASE severity
                  WHEN 'critical' THEN 1
                  WHEN 'high' THEN 2
                  WHEN 'medium' THEN 3
                  ELSE 4
                END
                """,
                (project_id,),
            ),
            "ui_test_plans": self._repository.rows(
                "SELECT * FROM ui_test_plans WHERE project_id=? ORDER BY name",
                (project_id,),
            ),
            "scheduled_jobs": self._repository.rows(
                "SELECT * FROM scheduled_jobs WHERE project_id=? ORDER BY enabled DESC,name",
                (project_id,),
            ),
            "runs": self._repository.rows(
                """
                SELECT r.*, c.title case_title
                FROM runs r
                LEFT JOIN test_cases c ON c.id=r.case_id
                WHERE r.project_id=?
                ORDER BY r.created_at DESC
                LIMIT 100
                """,
                (project_id,),
            ),
            "diagnosis": self._diagnosis_service.diagnose(project_id).model_dump(mode="json"),
            "control_plane": self._control_plane_service.control_plane(project_id),
        }
