from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from sqlite3 import Connection
from typing import Any

from .repositories.sqlite_read_model import QualityReadModelRepository
from .services.control_plane_service import AIQualityControlPlaneService
from .services.dashboard_service import ProjectDashboardService
from .services.diagnosis_service import ProjectDiagnosisService


class QualityHubRuntime:
    """Application service registry for the quality platform backend."""

    def __init__(
        self,
        *,
        connection_factory: Callable[[], Connection],
        data_dir: Path,
        report_lister: Callable[[str], list[dict[str, Any]]],
        credential_loader: Callable[[str], dict[str, Any]] | None = None,
    ) -> None:
        self.repository = QualityReadModelRepository(
            connection_factory,
            data_dir=data_dir,
            report_lister=report_lister,
            credential_loader=credential_loader,
        )
        self.diagnosis = ProjectDiagnosisService(self.repository)
        self.control_plane = AIQualityControlPlaneService(self.repository, self.diagnosis)
        self.dashboard = ProjectDashboardService(self.repository, self.diagnosis, self.control_plane)
