from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from sqlite3 import Connection
from typing import Any


class QualityReadModelRepository:
    """Read/write access to platform-owned SQLite data.

    External company data sources remain readonly adapters; this repository only
    persists platform assets such as diagnosis snapshots and evidence metadata.
    """

    def __init__(
        self,
        connection_factory: Callable[[], Connection],
        *,
        data_dir: Path,
        report_lister: Callable[[str], list[dict[str, Any]]],
        credential_loader: Callable[[str], dict[str, Any]] | None = None,
    ) -> None:
        self._connection_factory = connection_factory
        self._data_dir = data_dir
        self._report_lister = report_lister
        self._credential_loader = credential_loader

    def rows(self, sql: str, args: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self._connection_factory() as conn:
            return [dict(item) for item in conn.execute(sql, args).fetchall()]

    def row(self, sql: str, args: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self._connection_factory() as conn:
            item = conn.execute(sql, args).fetchone()
            return dict(item) if item else None

    def project(self, project_id: str) -> dict[str, Any] | None:
        return self.row("SELECT * FROM projects WHERE id=?", (project_id,))

    def sources(self, project_id: str) -> list[dict[str, Any]]:
        return self.rows("SELECT * FROM sources WHERE project_id=?", (project_id,))

    def project_settings(self, project_id: str) -> dict[str, str]:
        prefix = f"project:{project_id}:"
        return {
            item["key"].removeprefix(prefix): item["value"]
            for item in self.rows(
                "SELECT key,value FROM settings WHERE key LIKE ?", (prefix + "%",)
            )
        }

    def requirements(self, project_id: str) -> list[dict[str, Any]]:
        return self.rows(
            "SELECT * FROM requirement_items WHERE project_id=?", (project_id,)
        )

    def trace_links(self, project_id: str) -> list[dict[str, Any]]:
        return self.rows("SELECT * FROM trace_links WHERE project_id=?", (project_id,))

    def endpoints(self, project_id: str) -> list[dict[str, Any]]:
        return self.rows(
            "SELECT * FROM api_endpoints WHERE project_id=? ORDER BY path",
            (project_id,),
        )

    def test_cases(self, project_id: str) -> list[dict[str, Any]]:
        return self.rows(
            "SELECT * FROM test_cases WHERE project_id=? ORDER BY created_at DESC",
            (project_id,),
        )

    def consistency_rules(self, project_id: str) -> list[dict[str, Any]]:
        return self.rows(
            "SELECT * FROM consistency_rules WHERE project_id=?", (project_id,)
        )

    def consistency_runs(self, project_id: str) -> list[dict[str, Any]]:
        return self.rows(
            "SELECT * FROM consistency_runs WHERE project_id=? ORDER BY created_at DESC",
            (project_id,),
        )

    def db_tables(self, project_id: str) -> list[dict[str, Any]]:
        return self.rows(
            "SELECT table_name FROM db_tables WHERE project_id=?", (project_id,)
        )

    def db_mappings(self, project_id: str) -> list[dict[str, Any]]:
        return self.rows(
            "SELECT * FROM api_db_mappings WHERE project_id=?", (project_id,)
        )

    def redis_sources(self, project_id: str) -> list[dict[str, Any]]:
        return self.rows(
            "SELECT * FROM redis_sources WHERE project_id=?", (project_id,)
        )

    def redis_mappings(self, project_id: str) -> list[dict[str, Any]]:
        return self.rows(
            "SELECT * FROM api_redis_mappings WHERE project_id=?", (project_id,)
        )

    def accounts(self, project_id: str) -> list[dict[str, Any]]:
        accounts = self.rows(
            "SELECT * FROM test_accounts WHERE project_id=? ORDER BY mutable DESC,wealth_level,short_id",
            (project_id,),
        )
        for account in accounts:
            secret = (
                self._credential_loader(account["id"])
                if self._credential_loader
                else {}
            )
            if not secret:
                credential = self._data_dir / f"test-account-{account['id']}.bin"
                secret = (
                    {"ticket": "", "encrypted_password": ""}
                    if not credential.is_file()
                    else secret
                )
            account["has_ticket"] = bool(secret.get("ticket"))
            account["has_password"] = bool(secret.get("encrypted_password"))
        return accounts

    def reports(self, project_id: str) -> list[dict[str, Any]]:
        return self._report_lister(project_id)

    def failed_runs(self, project_id: str) -> list[dict[str, Any]]:
        return self.rows(
            """
            SELECT c.title,r.status,r.http_status,r.error
            FROM runs r
            LEFT JOIN test_cases c ON c.id=r.case_id
            WHERE r.project_id=? AND r.status IN ('FAILED','ERROR')
            ORDER BY r.created_at DESC
            LIMIT 10
            """,
            (project_id,),
        )

    def save_diagnosis(
        self, project_id: str, generated_at: str, items: list[dict[str, Any]]
    ) -> None:
        values = [
            (
                item["id"],
                project_id,
                item["severity"],
                item["module"],
                item["title"],
                item["description"],
                item["action_label"],
                item["action_target"],
                json.dumps(item.get("details", []), ensure_ascii=False),
                "open",
                generated_at,
            )
            for item in items
        ]
        with self._connection_factory() as conn:
            conn.execute(
                "DELETE FROM quality_diagnosis WHERE project_id=?", (project_id,)
            )
            conn.executemany(
                "INSERT INTO quality_diagnosis VALUES (?,?,?,?,?,?,?,?,?,?,?)", values
            )
