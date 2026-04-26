"""Regression tests for KeeperStore database-boundary behavior."""

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from archive_keeper.store import KeeperStore
from common.database import ArchiveDatabase
from common.database import (
    FILE_STATUS_MISSING,
    FILE_STATUS_NEW,
    TASK_STATUS_DONE,
    TASK_STATUS_PENDING,
)
from common.provider import list_providers


class TestKeeperStore:
    """Covers the package-local DB boundary used by Keeper."""

    def setup_method(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.archive_path = Path(self.temp_dir.name)
        self.database = ArchiveDatabase(self.archive_path)

    def teardown_method(self) -> None:
        self.database.close_conn()
        self.temp_dir.cleanup()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def test_requeue_recovered_file_resets_status_and_reseeds_tasks(self) -> None:
        conn = self.database.get_conn()

        conn.execute(
            "INSERT INTO files (path, status, checksum, imported_at) VALUES (?, ?, ?, ?)",
            ("scan.tif", FILE_STATUS_MISSING, "stale-checksum", self._now()),
        )
        file_id = conn.execute(
            "SELECT id FROM files WHERE path = ?",
            ("scan.tif",),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO tasks (file_id, daemon, status, updated_at) VALUES (?, ?, ?, ?)",
            (file_id, "preview-maker", TASK_STATUS_DONE, self._now()),
        )
        conn.commit()

        self.database.close_conn()

        with KeeperStore(self.archive_path) as store:
            store.requeue_recovered_file(file_id)

        conn = self.database.get_conn()

        row = conn.execute(
            "SELECT status, checksum FROM files WHERE id = ?",
            (file_id,),
        ).fetchone()
        task_rows = conn.execute(
            "SELECT daemon, status FROM tasks WHERE file_id = ? ORDER BY daemon",
            (file_id,),
        ).fetchall()

        assert row["status"] == FILE_STATUS_NEW
        assert row["checksum"] is None
        assert [row["daemon"] for row in task_rows] == [
            provider.daemon_name for provider in list_providers()
        ]
        assert all(row["status"] == TASK_STATUS_PENDING for row in task_rows)

    def test_get_task_counts_returns_total_and_pending(self) -> None:
        conn = self.database.get_conn()

        conn.execute(
            "INSERT INTO files (path, status, imported_at) VALUES (?, ?, ?)",
            ("scan.tif", FILE_STATUS_NEW, self._now()),
        )
        file_id = conn.execute(
            "SELECT id FROM files WHERE path = ?",
            ("scan.tif",),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO tasks (file_id, daemon, status, updated_at) VALUES (?, ?, ?, ?)",
            (file_id, "preview-maker", TASK_STATUS_DONE, self._now()),
        )
        conn.execute(
            "INSERT INTO tasks (file_id, daemon, status, updated_at) VALUES (?, ?, ?, ?)",
            (file_id, "face-recognizer", "running", self._now()),
        )
        conn.commit()

        self.database.close_conn()

        with KeeperStore(self.archive_path) as store:
            counts = store.get_task_counts(file_id)

        assert counts.total == 2
        assert counts.pending == 1