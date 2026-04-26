"""Database boundary for Tile Cutter task orchestration."""

from dataclasses import dataclass
from pathlib import Path
import sqlite3

from common.database import ArchiveDatabase
from common.database import FILE_STATUS_MODIFIED, FILE_STATUS_NEW
from common.database import TASK_STATUS_DONE, TASK_STATUS_FAILED, TASK_STATUS_PENDING, TASK_STATUS_RUNNING, TASK_STATUS_SKIPPED
from tile_cutter.constants import DAEMON_NAME


@dataclass(slots=True)
class CutterTaskRecord:
    """Minimal task candidate state needed by Tile Cutter orchestration."""

    file_id: int
    rel_path: str
    status: str


class CutterStore:
    """Thin package-local wrapper around shared tile-cutter task state."""

    def __init__(self, archive_path: str | Path) -> None:
        self._archive_path = Path(archive_path)
        self._database = ArchiveDatabase(self._archive_path)
        self._conn: sqlite3.Connection | None = None

    def _open(self) -> "CutterStore":
        if self._conn is not None:
            return self
        self._conn = self._database.get_conn()
        return self

    def _close(self) -> None:
        if self._conn is None:
            return
        self._conn.commit()
        self._conn = None
        self._database.close_conn()

    def __enter__(self) -> "CutterStore":
        return self._open()

    def __exit__(self, *_) -> None:
        self._close()

    @property
    def _c(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("CutterStore is not open")
        return self._conn

    def _commit(self) -> None:
        self._c.commit()

    def list_pending_files(self) -> list[CutterTaskRecord]:
        """Return this daemon's pending tasks for new/modified files."""
        rows = self._c.execute(
            """
            SELECT f.id, f.path, f.status
            FROM tasks t
            JOIN files f ON f.id = t.file_id
            WHERE t.daemon = ?
              AND t.status = ?
              AND f.status IN (?, ?)
            """,
            (DAEMON_NAME, TASK_STATUS_PENDING, FILE_STATUS_NEW, FILE_STATUS_MODIFIED),
        ).fetchall()
        return [
            CutterTaskRecord(
                file_id=int(row["id"]),
                rel_path=str(row["path"]),
                status=str(row["status"]),
            )
            for row in rows
        ]

    def start_task(self, file_id: int, updated_at: str) -> None:
        """Create or reset the tile-cutter task to running."""
        self._c.execute(
            "INSERT OR IGNORE INTO tasks (file_id, daemon, status, updated_at) VALUES (?, ?, ?, ?)",
            (file_id, DAEMON_NAME, TASK_STATUS_RUNNING, updated_at),
        )
        self._c.execute(
            "UPDATE tasks SET status = ?, error = NULL, updated_at = ? WHERE file_id = ? AND daemon = ?",
            (TASK_STATUS_RUNNING, updated_at, file_id, DAEMON_NAME),
        )
        self._commit()

    def mark_done(self, file_id: int, updated_at: str) -> None:
        """Mark a tile-cutter task as done."""
        self._c.execute(
            "UPDATE tasks SET status = ?, error = NULL, updated_at = ? WHERE file_id = ? AND daemon = ?",
            (TASK_STATUS_DONE, updated_at, file_id, DAEMON_NAME),
        )
        self._commit()

    def mark_skipped(self, file_id: int, updated_at: str) -> None:
        """Mark a tile-cutter task as skipped."""
        self._c.execute(
            "UPDATE tasks SET status = ?, error = NULL, updated_at = ? WHERE file_id = ? AND daemon = ?",
            (TASK_STATUS_SKIPPED, updated_at, file_id, DAEMON_NAME),
        )
        self._commit()

    def mark_failed(self, file_id: int, error: str, updated_at: str) -> None:
        """Mark a tile-cutter task as failed with an error message."""
        self._c.execute(
            "UPDATE tasks SET status = ?, error = ?, updated_at = ? WHERE file_id = ? AND daemon = ?",
            (TASK_STATUS_FAILED, error, updated_at, file_id, DAEMON_NAME),
        )
        self._commit()
