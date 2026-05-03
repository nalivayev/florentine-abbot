"""Data access layer for tasks and task_steps tables."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common.database import ArchiveDatabase


class TaskStore:
    """Shared store for creating and updating tasks and their steps."""

    def __init__(self, archive_path: str | Path) -> None:
        self._database = ArchiveDatabase(Path(archive_path))
        self._conn: sqlite3.Connection | None = None

    def __enter__(self) -> "TaskStore":
        if self._conn is None:
            self._conn = self._database.get_conn()
        return self

    def __exit__(self, *_: Any) -> None:
        if self._conn is not None:
            self._conn.commit()
            self._conn = None
            self._database.close_conn()

    @property
    def _c(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("TaskStore is not open")
        return self._conn

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # -- tasks --

    def create_task(self, *, domain: str, action: str, payload: dict[str, Any]) -> int:
        cur = self._c.execute(
            "INSERT INTO tasks (domain, action, status, payload, created_at)"
            " VALUES (?, ?, 'pending', ?, ?)",
            (domain, action, json.dumps(payload), self._now()),
        )
        self._c.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def start_task(self, task_id: int) -> None:
        self._c.execute(
            "UPDATE tasks SET status = 'running', started_at = ? WHERE id = ?",
            (self._now(), task_id),
        )
        self._c.commit()

    def finish_task(self, task_id: int) -> None:
        self._c.execute(
            "UPDATE tasks SET status = 'done', finished_at = ? WHERE id = ?",
            (self._now(), task_id),
        )
        self._c.commit()

    def fail_task(self, task_id: int) -> None:
        self._c.execute(
            "UPDATE tasks SET status = 'failed', finished_at = ? WHERE id = ?",
            (self._now(), task_id),
        )
        self._c.commit()

    # -- task_steps --

    def create_step(self, *, task_id: int, kind: str, payload: dict[str, Any]) -> int:
        cur = self._c.execute(
            "INSERT INTO task_steps (task_id, kind, status, payload) VALUES (?, ?, 'pending', ?)",
            (task_id, kind, json.dumps(payload)),
        )
        self._c.execute(
            "UPDATE tasks SET steps = steps + 1 WHERE id = ?",
            (task_id,),
        )
        self._c.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def start_step(self, step_id: int) -> None:
        self._c.execute(
            "UPDATE task_steps SET status = 'running', started_at = ? WHERE id = ?",
            (self._now(), step_id),
        )
        self._c.commit()

    def finish_step(self, step_id: int) -> None:
        self._c.execute(
            "UPDATE task_steps SET status = 'done', finished_at = ? WHERE id = ?",
            (self._now(), step_id),
        )
        self._c.execute(
            "UPDATE tasks SET done = done + 1"
            " WHERE id = (SELECT task_id FROM task_steps WHERE id = ?)",
            (step_id,),
        )
        self._c.commit()

    def fail_step(self, step_id: int, error: str) -> None:
        self._c.execute(
            "UPDATE task_steps SET status = 'failed', error = ?, finished_at = ? WHERE id = ?",
            (error, self._now(), step_id),
        )
        self._c.execute(
            "UPDATE tasks SET failed = failed + 1"
            " WHERE id = (SELECT task_id FROM task_steps WHERE id = ?)",
            (step_id,),
        )
        self._c.commit()
