"""
Polling-based daemon for Archive Keeper.

Periodically:
- Detects files in DB that are missing on disk → marks as 'missing'
- Calculates checksums for newly imported files (status 'new') → stores in DB
- Marks files as 'active' when all their tasks are done
- Resets 'missing' files back to 'new' when they reappear on disk
  (handles re-import after manual deletion)
"""

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from common.config_utils import get_archive_path
from common.db import get_conn, init_db, FILE_STATUS_NEW, FILE_STATUS_ACTIVE, FILE_STATUS_MISSING, TASK_STATUS_DONE, TASK_STATUS_SKIPPED
from common.logger import Logger
from archive_keeper.keeper import ArchiveKeeper

_POLL_INTERVAL = 60  # seconds


class KeeperWatcher:
    """
    Polls the database and performs archive integrity checks.

    On each poll cycle:
    1. Files with status 'missing' that now exist on disk → reset to 'new',
       delete their completed tasks so daemons re-process them.
    2. Files with status 'new' that have no checksum → calculate and store.
    3. Active files (all tasks done/skipped) → promote to 'active'.
    4. Active files not on disk → mark as 'missing'.
    """

    def __init__(
        self,
        logger: Logger,
        *,
        poll_interval: int = _POLL_INTERVAL,
    ) -> None:
        self._logger = logger
        self._keeper: ArchiveKeeper | None = None
        self._poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._path: Path | None = None

    def start(self) -> None:
        """Start polling loop. Runs until stop() is called or KeyboardInterrupt."""
        archive_path = get_archive_path()
        if archive_path is None or not archive_path.exists():
            self._logger.error("Archive path not configured or does not exist")
            return
        self._path = archive_path
        self._keeper = ArchiveKeeper(self._logger)

        init_db(self._path)
        self._logger.info(
            f"Started archive-keeper daemon, archive={self._path}, "
            f"polling every {self._poll_interval}s"
        )

        try:
            while not self._stop_event.is_set():
                self._poll()
                self._stop_event.wait(self._poll_interval)
        except KeyboardInterrupt:
            pass

        self._logger.info("Stopped archive-keeper daemon")

    def stop(self) -> None:
        """Signal the polling loop to stop. Safe to call from any thread."""
        self._stop_event.set()

    def scan(self, archive_path: Path) -> None:
        """One-shot integrity scan (used by the 'scan' CLI subcommand)."""
        self._path = archive_path
        self._keeper = ArchiveKeeper(self._logger)
        init_db(self._path)
        self._poll()

    def _poll(self) -> None:
        """One poll cycle."""
        try:
            conn = get_conn()
        except RuntimeError:
            self._logger.warning("Database not initialized, skipping poll")
            return

        assert self._path is not None
        assert self._keeper is not None

        self._recover_missing(conn)
        self._checksum_new_files(conn)
        self._promote_to_active(conn)
        self._detect_missing(conn)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _is_missing(self, rel_path: str) -> bool:
        assert self._path is not None
        return not (self._path / rel_path).exists()

    def _recover_missing(self, conn: sqlite3.Connection) -> None:
        """Reset files marked as 'missing' that have reappeared on disk."""
        assert self._path is not None
        rows = conn.execute(
            "SELECT id, path FROM files WHERE status = ?",
            (FILE_STATUS_MISSING,),
        ).fetchall()

        for row in rows:
            if not self._is_missing(row["path"]):
                self._logger.info(f"File recovered, resetting to new: {row['path']}")
                conn.execute(
                    "UPDATE files SET status = ? WHERE id = ?",
                    (FILE_STATUS_NEW, row["id"]),
                )
                conn.execute("DELETE FROM tasks WHERE file_id = ?", (row["id"],))

        conn.commit()

    def _checksum_new_files(self, conn: sqlite3.Connection) -> None:
        """Calculate checksums for new files that don't have one yet."""
        assert self._path is not None
        rows = conn.execute(
            "SELECT id, path FROM files WHERE status = ? AND checksum IS NULL",
            (FILE_STATUS_NEW,),
        ).fetchall()

        for row in rows:
            file_path = self._path / row["path"]
            if not file_path.exists():
                continue
            try:
                checksum = self._keeper.calculate(file_path)  # type: ignore[union-attr]
                conn.execute(
                    "UPDATE files SET checksum = ? WHERE id = ?",
                    (checksum, row["id"]),
                )
                self._logger.info(f"Checksum calculated: {row['path']}")
            except Exception as e:
                self._logger.error(f"Failed to calculate checksum for {row['path']}: {e}")

        conn.commit()

    def _promote_to_active(self, conn: sqlite3.Connection) -> None:
        """Promote files to 'active' when all their tasks are done or skipped."""
        rows = conn.execute(
            "SELECT id FROM files WHERE status = ?",
            (FILE_STATUS_NEW,),
        ).fetchall()

        for row in rows:
            pending = conn.execute(
                """
                SELECT COUNT(*) FROM tasks
                WHERE file_id = ? AND status NOT IN (?, ?)
                """,
                (row["id"], TASK_STATUS_DONE, TASK_STATUS_SKIPPED),
            ).fetchone()[0]

            if pending == 0:
                task_count = conn.execute(
                    "SELECT COUNT(*) FROM tasks WHERE file_id = ?",
                    (row["id"],),
                ).fetchone()[0]

                if task_count > 0:
                    conn.execute(
                        "UPDATE files SET status = ? WHERE id = ?",
                        (FILE_STATUS_ACTIVE, row["id"]),
                    )

        conn.commit()

    def _detect_missing(self, conn: sqlite3.Connection) -> None:
        """Mark active files that are no longer on disk as 'missing'."""
        assert self._path is not None
        rows = conn.execute(
            "SELECT id, path FROM files WHERE status = ?",
            (FILE_STATUS_ACTIVE,),
        ).fetchall()

        for row in rows:
            if self._is_missing(row["path"]):
                self._logger.warning(f"File missing: {row['path']}")
                conn.execute(
                    "UPDATE files SET status = ? WHERE id = ?",
                    (FILE_STATUS_MISSING, row["id"]),
                )

        conn.commit()
