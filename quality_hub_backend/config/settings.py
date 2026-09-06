from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml


def _enabled(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() == "true"


def _configured_bool(name: str, configured: object, default: bool = False) -> bool:
    if configured is not None:
        return bool(configured)
    raw = os.getenv(name)
    return raw.strip().lower() == "true" if raw is not None else default


def _environment_yaml(root: Path) -> dict:
    path = root / "config" / "env.test.yaml"
    if not path.is_file():
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return payload if isinstance(payload, dict) else {}


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
        configured = _environment_yaml(root)
        execution = configured.get("execution") if isinstance(configured.get("execution"), dict) else {}
        configured_hosts = execution.get("allowed_hosts") or []
        raw_hosts = os.getenv("AUTOTEST_ALLOWED_HOSTS")
        host_values = raw_hosts.split(",") if raw_hosts is not None else configured_hosts
        hosts = tuple(str(value).strip() for value in host_values if str(value).strip())
        workers = max(1, min(int(os.getenv("AUTOTEST_TASK_WORKERS", "2")), 8))
        database_value = os.getenv("AUTOTEST_TASK_DATABASE", "data/task_queue.db")
        database = Path(database_value)
        if not database.is_absolute():
            database = root / database
        demo_mode = _enabled("AUTOTEST_DEMO_MODE")
        return cls(
            root=root,
            demo_mode=demo_mode,
            allow_mutations=False if demo_mode else _configured_bool("AUTOTEST_ALLOW_MUTATIONS", execution.get("allow_mutations")),
            allow_high_risk=_configured_bool("AUTOTEST_ALLOW_HIGH_RISK", execution.get("allow_high_risk")),
            allowed_hosts=hosts,
            task_workers=workers,
            task_database=database,
        )
