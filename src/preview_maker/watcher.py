"""
Polling-based daemon for Preview Maker.

Periodically queries the database for files that need preview generation,
processes them, and records the result.
"""

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from common.config_utils import get_archive_path
from common.db import (
    get_conn, init_db,
    FILE_STATUS_NEW, FILE_STATUS_MODIFIED,
    TASK_STATUS_RUNNING, TASK_STATUS_DONE, TASK_STATUS_FAILED, TASK_STATUS_SKIPPED,
)
from common.logger import Logger
from preview_maker.maker import PreviewMaker

_DAEMON_NAME = "preview-maker"
_POLL_INTERVAL = 30  # seconds


class PreviewWatcher:
    """
    Polls the database for new/modified files and generates previews.

    On each poll cycle:
    1. Query files with status 'new' or 'modified' that have no preview-maker task.
    2. Create a 'running' task for each.
    3. Process each file, update task to 'done', 'skipped', or 'failed'.
    """

    def __init__(
        self,
        logger: Logger,
        *,
        config_path: str | Path | None = None,
        poll_interval: int = _POLL_INTERVAL,
    ) -> None:
        self._logger = logger
        self._maker = PreviewMaker(logger, config_path)
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

        init_db(self._path)
        self._logger.info(
            f"Started preview-maker daemon, archive={self._path}, "
            f"polling every {self._poll_interval}s"
        )

        try:
            while not self._stop_event.is_set():
                self._poll()
                self._stop_event.wait(self._poll_interval)
        except KeyboardInterrupt:
            pass

        self._logger.info("Stopped preview-maker daemon")

    def stop(self) -> None:
        """Signal the polling loop to stop. Safe to call from any thread."""
        self._stop_event.set()

    def _poll(self) -> None:
        """One poll cycle: find pending files, process them."""
        try:
            conn = get_conn()
        except RuntimeError:
            self._logger.warning("Database not initialized, skipping poll")
            return

        rows = conn.execute(
            """
            SELECT f.id, f.path FROM files f
            WHERE f.status IN (?, ?)
              AND NOT EXISTS (
                  SELECT 1 FROM tasks t
                  WHERE t.file_id = f.id AND t.daemon = ?
              )
            """,
            (FILE_STATUS_NEW, FILE_STATUS_MODIFIED, _DAEMON_NAME),
        ).fetchall()

        if not rows:
            return

        self._logger.info(f"Found {len(rows)} file(s) to process")

        for row in rows:
            self._process_file(conn, file_id=row["id"], rel_path=row["path"])

    def _process_file(
        self,
        conn: sqlite3.Connection,
        file_id: int,
        rel_path: str,
    ) -> None:
        def now() -> str:
            return datetime.now(timezone.utc).isoformat()

        conn.execute(
            "INSERT OR IGNORE INTO tasks (file_id, daemon, status, updated_at) VALUES (?, ?, ?, ?)",
            (file_id, _DAEMON_NAME, TASK_STATUS_RUNNING, now()),
        )
        conn.commit()

        assert self._path is not None
        src_path = self._path / rel_path

        if not src_path.exists():
            self._logger.warning(f"File not found, skipping: {src_path}")
            conn.execute(
                "UPDATE tasks SET status=?, error=?, updated_at=? WHERE file_id=? AND daemon=?",
                (TASK_STATUS_FAILED, "File not found", now(), file_id, _DAEMON_NAME),
            )
            conn.commit()
            return

        try:
            if not self._maker.should_process(src_path):
                conn.execute(
                    "UPDATE tasks SET status=?, updated_at=? WHERE file_id=? AND daemon=?",
                    (TASK_STATUS_SKIPPED, now(), file_id, _DAEMON_NAME),
                )
            else:
                self._maker.process_single_file(src_path, archive_path=self._path)
                conn.execute(
                    "UPDATE tasks SET status=?, updated_at=? WHERE file_id=? AND daemon=?",
                    (TASK_STATUS_DONE, now(), file_id, _DAEMON_NAME),
                )
        except Exception as e:
            self._logger.error(f"Error processing {src_path.name}: {e}")
            conn.execute(
                "UPDATE tasks SET status=?, error=?, updated_at=? WHERE file_id=? AND daemon=?",
                (TASK_STATUS_FAILED, str(e), now(), file_id, _DAEMON_NAME),
            )

        conn.commit()
