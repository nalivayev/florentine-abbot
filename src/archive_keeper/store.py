"""Database boundary for Archive Keeper state transitions."""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from common.database import ArchiveDatabase
from common.database import FILE_STATUS_ACTIVE, FILE_STATUS_MISSING, FILE_STATUS_MODIFIED, FILE_STATUS_NEW
from common.database import TASK_STATUS_DONE, TASK_STATUS_PENDING, TASK_STATUS_SKIPPED
from common.provider import list_providers


@dataclass(slots=True)
class ArchiveFileRecord:
    """Minimal file state needed by Archive Keeper orchestration."""

    file_id: int
    rel_path: str
    status: str
    checksum: str | None = None


@dataclass(slots=True)
class TaskCounts:
    """Task counters for one file in the shared archive database."""

    total: int
    pending: int


class KeeperStore:
    """Thin package-local wrapper around the shared archive database."""

    def __init__(self, archive_path: str | Path) -> None:
        self._archive_path = Path(archive_path)
        self._database = ArchiveDatabase(self._archive_path)
        self._conn: sqlite3.Connection | None = None

    def _open(self) -> "KeeperStore":
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

    def __enter__(self) -> "KeeperStore":
        return self._open()

    def __exit__(self, *_) -> None:
        self._close()

    @property
    def _c(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("KeeperStore is not open")
        return self._conn

    def _commit(self) -> None:
        self._c.commit()

    def _seed_tasks_for_file(self, *, file_id: int, updated_at: str) -> None:
        for provider in list_providers():
            self._c.execute(
                "INSERT OR IGNORE INTO daemon_tasks (file_id, daemon, status, updated_at) VALUES (?, ?, ?, ?)",
                (file_id, provider.daemon_name, TASK_STATUS_PENDING, updated_at),
            )

    def list_missing_files(self) -> list[ArchiveFileRecord]:
        """Return files currently marked as missing."""
        rows = self._c.execute(
            "SELECT id, path, status, checksum FROM files WHERE status = ?",
            (FILE_STATUS_MISSING,),
        ).fetchall()
        return [self._record_from_row(row) for row in rows]

    def requeue_recovered_file(self, file_id: int) -> None:
        """Reset a recovered missing file to new, clear checksum, and drop tasks."""
        self._c.execute(
            "UPDATE files SET status = ?, checksum = NULL WHERE id = ?",
            (FILE_STATUS_NEW, file_id),
        )
        self._c.execute("DELETE FROM daemon_tasks WHERE file_id = ?", (file_id,))
        self._seed_tasks_for_file(
            file_id=file_id,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        self._commit()

    def list_new_files_without_checksum(self) -> list[ArchiveFileRecord]:
        """Return new files that still need an initial checksum."""
        rows = self._c.execute(
            "SELECT id, path, status, checksum FROM files WHERE status = ? AND checksum IS NULL",
            (FILE_STATUS_NEW,),
        ).fetchall()
        return [self._record_from_row(row) for row in rows]

    def update_checksum(self, file_id: int, checksum: str) -> None:
        """Store the freshly calculated checksum for a file."""
        self._c.execute(
            "UPDATE files SET checksum = ? WHERE id = ?",
            (checksum, file_id),
        )
        self._commit()

    def list_activation_candidates(self) -> list[ArchiveFileRecord]:
        """Return new and modified files that may be ready for activation."""
        rows = self._c.execute(
            "SELECT id, path, status, checksum FROM files WHERE status IN (?, ?)",
            (FILE_STATUS_NEW, FILE_STATUS_MODIFIED),
        ).fetchall()
        return [self._record_from_row(row) for row in rows]

    def get_task_counts(self, file_id: int) -> TaskCounts:
        """Return total and unfinished task counts for one file."""
        row = self._c.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status NOT IN (?, ?) THEN 1 ELSE 0 END) AS pending
            FROM daemon_tasks
            WHERE file_id = ?
            """,
            (TASK_STATUS_DONE, TASK_STATUS_SKIPPED, file_id),
        ).fetchone()
        assert row is not None
        return TaskCounts(
            total=int(row["total"] or 0),
            pending=int(row["pending"] or 0),
        )

    def mark_active(self, file_id: int, *, checksum: str | None = None) -> None:
        """Promote a file to active, optionally replacing its checksum."""
        if checksum is None:
            self._c.execute(
                "UPDATE files SET status = ? WHERE id = ?",
                (FILE_STATUS_ACTIVE, file_id),
            )
            self._commit()
            return

        self._c.execute(
            "UPDATE files SET status = ?, checksum = ? WHERE id = ?",
            (FILE_STATUS_ACTIVE, checksum, file_id),
        )
        self._commit()

    def list_active_files(self) -> list[ArchiveFileRecord]:
        """Return files currently marked as active."""
        rows = self._c.execute(
            "SELECT id, path, status, checksum FROM files WHERE status = ?",
            (FILE_STATUS_ACTIVE,),
        ).fetchall()
        return [self._record_from_row(row) for row in rows]

    def mark_missing(self, file_id: int) -> None:
        """Mark an active file as missing on disk."""
        self._c.execute(
            "UPDATE files SET status = ? WHERE id = ?",
            (FILE_STATUS_MISSING, file_id),
        )
        self._commit()

    @staticmethod
    def _record_from_row(row: sqlite3.Row) -> ArchiveFileRecord:
        """Convert a shared-db row to the local record type."""
        return ArchiveFileRecord(
            file_id=int(row["id"]),
            rel_path=str(row["path"]),
            status=str(row["status"]),
            checksum=row["checksum"],
        )
