from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_jmeter_execution_progress(
    progress_path: str | Path,
    fallback: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge the bridge progress file into a polling fallback payload."""
    payload = dict(fallback or {})
    path = Path(progress_path)
    if not path.is_file():
        return payload
    try:
        progress = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return payload
    if not isinstance(progress, dict):
        return payload
    payload.update(progress)
    if payload.get("percent") is not None:
        try:
            payload["percent"] = max(0, min(int(payload["percent"]), 100))
        except (TypeError, ValueError):
            payload.pop("percent", None)
    return payload


def build_jmeter_mcp_import_workflow(
    *,
    project_id: str,
    package_id: str,
    project_name: str,
    source_jmx: str,
    max_error_rate_pct: float = 0,
    max_p95_ms: int = 1000,
    max_p99_ms: int = 2000,
    auto_stop: dict[str, Any] | None = None,
    generation_skill: dict[str, Any] | None = None,
    correction_skill: dict[str, Any] | None = None,
    preflight_path: str = "",
    preflight_status: str = "PASS",
    source_kind: str = "skill_generated",
) -> dict:
    if not str(source_jmx or "").strip():
        raise ValueError("A source JMX path is required for MCP import.")
    return {
        "schema_version": "2.0",
        "name": f"{project_name} - {package_id}",
        "metadata": {
            "project_id": project_id,
            "package_id": package_id,
            "source": source_kind,
            "generation_skill": generation_skill or {},
            "correction_skill": correction_skill or {},
            "preflight_path": preflight_path,
            "preflight_status": preflight_status,
            "execution_engine": "jmeter-mcp-server@0.3.1",
            "execution_mode": "import_only",
        },
        "source_jmx": str(source_jmx),
        "thresholds": {
            "max_error_rate_pct": float(max_error_rate_pct),
            "max_p95_ms": int(max_p95_ms),
            "max_p99_ms": int(max_p99_ms),
        },
        "auto_stop": {
            "enabled": True,
            "sample_interval_seconds": 2,
            "grace_period_seconds": 5,
            "min_samples": 10,
            "latency_consecutive_windows": 2,
            "error_consecutive_windows": 1,
            "warmup_samples_per_label": 0,
            **(auto_stop or {}),
        },
    }


def build_jmeter_mcp_workflow(**_: Any) -> dict:
    raise RuntimeError(
        "Typed MCP JMX generation has been retired. Generate and validate a JMX first, then use build_jmeter_mcp_import_workflow()."
    )
