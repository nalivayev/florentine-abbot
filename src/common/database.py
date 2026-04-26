"""Shared SQLite database runtime for Florentine Abbot."""

import sqlite3
from pathlib import Path

from common.constants import ARCHIVE_DB_FILENAME, ARCHIVE_SYSTEM_DIR
from common.schema import SCHEMA_SQL

# File lifecycle statuses
FILE_STATUS_NEW       = "new"
FILE_STATUS_ACTIVE    = "active"
FILE_STATUS_MODIFIED  = "modified"
FILE_STATUS_DELETED   = "deleted"
FILE_STATUS_CORRUPTED = "corrupted"
FILE_STATUS_MISSING   = "missing"

# Task statuses
TASK_STATUS_PENDING = "pending"
TASK_STATUS_RUNNING = "running"
TASK_STATUS_DONE    = "done"
TASK_STATUS_FAILED  = "failed"
TASK_STATUS_SKIPPED = "skipped"


class ArchiveDatabase:
    """Path-bound runtime wrapper around one archive SQLite database connection."""

    def __init__(self, archive_path: str | Path) -> None:
        self._db_path = Path(archive_path) / ARCHIVE_SYSTEM_DIR / ARCHIVE_DB_FILENAME
        self._conn: sqlite3.Connection | None = None

    def _open_conn(self) -> None:
        """Open or create the bound archive database and ensure core tables exist."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables(self._conn)

    def get_conn(self) -> sqlite3.Connection:
        """Return the active connection, opening the bound archive lazily on demand."""
        if self._conn is None:
            self._open_conn()
        assert self._conn is not None
        return self._conn

    def close_conn(self) -> None:
        """Close the active connection for the bound archive, if it is open."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    @staticmethod
    def _create_tables(conn: sqlite3.Connection) -> None:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
