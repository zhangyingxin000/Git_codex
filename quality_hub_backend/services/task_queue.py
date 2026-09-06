from __future__ import annotations

import json
import sqlite3
import threading
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable


TaskHandler = Callable[[dict[str, Any]], Any]


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class PersistentTaskQueue:
    """Small local task queue with SQLite state and bounded worker threads."""

    def __init__(self, database: Path, max_workers: int = 2) -> None:
        self.database = database
        self.max_workers = max_workers
        self._executor: ThreadPoolExecutor | None = None
        self._lock = threading.Lock()
        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_database(self) -> None:
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS background_tasks (
                    task_id TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    result_json TEXT NOT NULL DEFAULT '',
                    error TEXT NOT NULL DEFAULT '',
                    progress_json TEXT NOT NULL DEFAULT '',
                    cancel_requested INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    started_at TEXT NOT NULL DEFAULT '',
                    finished_at TEXT NOT NULL DEFAULT ''
                )
                """
            )
            columns = {
                str(row[1]) for row in connection.execute("PRAGMA table_info(background_tasks)").fetchall()
            }
            if "progress_json" not in columns:
                connection.execute("ALTER TABLE background_tasks ADD COLUMN progress_json TEXT NOT NULL DEFAULT ''")
            if "cancel_requested" not in columns:
                connection.execute("ALTER TABLE background_tasks ADD COLUMN cancel_requested INTEGER NOT NULL DEFAULT 0")
            connection.execute(
                "UPDATE background_tasks SET status='INTERRUPTED', finished_at=? WHERE status='RUNNING'",
                (_now(),),
            )

    def start(self) -> None:
        with self._lock:
            if self._executor is None:
                self._executor = ThreadPoolExecutor(
                    max_workers=self.max_workers,
                    thread_name_prefix="quality-hub-task",
                )

    def shutdown(self) -> None:
        with self._lock:
            executor, self._executor = self._executor, None
        if executor is not None:
            executor.shutdown(wait=False, cancel_futures=False)

    def submit(self, task_type: str, payload: dict[str, Any], handler: TaskHandler) -> dict[str, Any]:
        self.start()
        task_id = f"task_{uuid.uuid4().hex}"
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO background_tasks(task_id,task_type,status,payload_json,created_at) VALUES(?,?,?,?,?)",
                (task_id, task_type, "PENDING", json.dumps(payload, ensure_ascii=False), _now()),
            )
        assert self._executor is not None
        self._executor.submit(self._execute, task_id, payload, handler)
        return self.get(task_id) or {"task_id": task_id, "status": "PENDING"}

    def _execute(self, task_id: str, payload: dict[str, Any], handler: TaskHandler) -> None:
        if self.is_cancel_requested(task_id):
            with self._connect() as connection:
                connection.execute(
                    "UPDATE background_tasks SET status='CANCELLED', finished_at=? WHERE task_id=?",
                    (_now(), task_id),
                )
            return
        with self._connect() as connection:
            connection.execute(
                "UPDATE background_tasks SET status='RUNNING', started_at=? WHERE task_id=?",
                (_now(), task_id),
            )
        try:
            task_payload = dict(payload)
            task_payload["_task_context"] = {
                "task_id": task_id,
                "is_cancelled": lambda: self.is_cancel_requested(task_id),
                "progress": lambda value: self.update_progress(task_id, value),
            }
            result = handler(task_payload)
            serialized = json.dumps(result, ensure_ascii=False, default=str)
            if len(serialized) > 200_000:
                serialized = json.dumps(
                    {"status": "COMPLETED", "message": "Result was truncated", "size": len(serialized)}
                )
            with self._connect() as connection:
                result_status = (
                    str(result.get("status") or "").upper()
                    if isinstance(result, dict)
                    else ""
                )
                if self.is_cancel_requested(task_id) or result_status == "CANCELLED":
                    final_status = "CANCELLED"
                elif result_status in {"FAILED", "BLOCKED", "ERROR", "INTERRUPTED"}:
                    final_status = "FAILED"
                else:
                    final_status = "PASSED"
                connection.execute(
                    "UPDATE background_tasks SET status=?, result_json=?, finished_at=? WHERE task_id=?",
                    (final_status, serialized, _now(), task_id),
                )
        except Exception as exc:
            detail = "".join(traceback.format_exception_only(type(exc), exc)).strip()
            with self._connect() as connection:
                connection.execute(
                    "UPDATE background_tasks SET status='FAILED', error=?, finished_at=? WHERE task_id=?",
                    (detail[:4000], _now(), task_id),
                )

    @staticmethod
    def _record(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        for source, target in (("payload_json", "payload"), ("result_json", "result"), ("progress_json", "progress")):
            raw = item.pop(source, "")
            try:
                item[target] = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                item[target] = {"raw": raw}
        return item

    def update_progress(self, task_id: str, progress: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE background_tasks SET progress_json=? WHERE task_id=?",
                (json.dumps(progress or {}, ensure_ascii=False, default=str), task_id),
            )

    def is_cancel_requested(self, task_id: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT cancel_requested FROM background_tasks WHERE task_id=?", (task_id,)
            ).fetchone()
        return bool(row and row[0])

    def request_cancel(self, task_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT status FROM background_tasks WHERE task_id=?", (task_id,)
            ).fetchone()
            if row is None:
                return None
            status = str(row[0])
            if status in {"PASSED", "FAILED", "CANCELLED", "INTERRUPTED"}:
                return self.get(task_id)
            next_status = "CANCELLED" if status == "PENDING" else status
            finished_at = _now() if status == "PENDING" else ""
            connection.execute(
                "UPDATE background_tasks SET cancel_requested=1,status=?,finished_at=? WHERE task_id=?",
                (next_status, finished_at, task_id),
            )
        return self.get(task_id)

    def get(self, task_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM background_tasks WHERE task_id=?", (task_id,)
            ).fetchone()
        return self._record(row) if row else None

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 200))
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM background_tasks ORDER BY created_at DESC LIMIT ?", (safe_limit,)
            ).fetchall()
        return [self._record(row) for row in rows]
