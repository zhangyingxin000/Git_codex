from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _enabled(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() == "true"


@dataclass(frozen=True)
class AppSettings:
    root: Path
    demo_mode: bool
    allow_mutations: bool
    allow_high_risk: bool
    allowed_hosts: tuple[str, ...]
    task_workers: int
    task_database: Path

    @classmethod
    def from_environment(cls, root: Path) -> "AppSettings":
        hosts = tuple(
            value.strip()
            for value in os.getenv("AUTOTEST_ALLOWED_HOSTS", "").split(",")
            if value.strip()
        )
        workers = max(1, min(int(os.getenv("AUTOTEST_TASK_WORKERS", "2")), 8))
        database_value = os.getenv("AUTOTEST_TASK_DATABASE", "data/task_queue.db")
        database = Path(database_value)
        if not database.is_absolute():
            database = root / database
        return cls(
            root=root,
            demo_mode=_enabled("AUTOTEST_DEMO_MODE"),
            allow_mutations=_enabled("AUTOTEST_ALLOW_MUTATIONS"),
            allow_high_risk=_enabled("AUTOTEST_ALLOW_HIGH_RISK"),
            allowed_hosts=hosts,
            task_workers=workers,
            task_database=database,
        )
