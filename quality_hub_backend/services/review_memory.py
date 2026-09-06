from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_review_memory(path: Path) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        return {"schema_version": "1.0", "latest": {}, "history": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": "1.0", "latest": {}, "history": []}
    return payload if isinstance(payload, dict) else {"schema_version": "1.0", "latest": {}, "history": []}


def persist_review_memory(path: Path, review: dict[str, Any], keep: int = 20) -> dict[str, Any]:
    path = Path(path)
    existing = load_review_memory(path)
    entry = {
        "run_id": review.get("run_id"),
        "status": review.get("status"),
        "created_at": review.get("created_at"),
        "conclusion": review.get("conclusion"),
        "summary": review.get("summary") or {},
        "root_cause_categories": review.get("root_cause_categories") or {},
        "next_actions": list(review.get("next_actions") or [])[:10],
        "findings": [
            {
                "level": item.get("level"),
                "category": item.get("category"),
                "title": item.get("title"),
                "recommendation": item.get("recommendation") or item.get("owner"),
            }
            for item in (review.get("findings") or [])[:20]
            if isinstance(item, dict)
        ],
    }
    history = [item for item in (existing.get("history") or []) if item.get("run_id") != entry["run_id"]]
    history.insert(0, entry)
    payload = {
        "schema_version": "1.0",
        "report_type": "REQUIREMENT_PACKAGE_AI_REVIEW_MEMORY",
        "package_id": review.get("package_id"),
        "updated_at": entry["created_at"],
        "latest": entry,
        "history": history[:max(1, int(keep))],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)
    return payload
