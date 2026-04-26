"""Regression tests for MakerStore database-boundary behavior."""

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from common.database import ArchiveDatabase
from common.database import FILE_STATUS_MODIFIED, FILE_STATUS_NEW, TASK_STATUS_DONE, TASK_STATUS_PENDING
from preview_maker.store import MakerStore


class TestMakerStore:
    """Covers the package-local DB boundary used by Maker."""

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

    def test_list_pending_files_returns_only_pending_preview_tasks(self) -> None:
        conn = self.database.get_conn()

        conn.execute(
            "INSERT INTO files (path, status, imported_at) VALUES (?, ?, ?)",
            ("a.tif", FILE_STATUS_NEW, self._now()),
        )
        conn.execute(
            "INSERT INTO files (path, status, imported_at) VALUES (?, ?, ?)",
            ("b.tif", FILE_STATUS_MODIFIED, self._now()),
        )
        file_id = conn.execute(
            "SELECT id FROM files WHERE path = ?",
            ("a.tif",),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO tasks (file_id, daemon, status, updated_at) VALUES (?, ?, ?, ?)",
            (file_id, "preview-maker", TASK_STATUS_PENDING, self._now()),
        )
        file_id = conn.execute(
            "SELECT id FROM files WHERE path = ?",
            ("b.tif",),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO tasks (file_id, daemon, status, updated_at) VALUES (?, ?, ?, ?)",
            (file_id, "preview-maker", TASK_STATUS_DONE, self._now()),
        )
        conn.commit()

        self.database.close_conn()

        with MakerStore(self.archive_path) as store:
            rows = store.list_pending_files()

        assert len(rows) == 1
        assert rows[0].rel_path == "a.tif"
        assert rows[0].status == FILE_STATUS_NEW

    def test_mark_failed_updates_preview_task_row(self) -> None:
        conn = self.database.get_conn()

        conn.execute(
            "INSERT INTO files (path, status, imported_at) VALUES (?, ?, ?)",
            ("scan.tif", FILE_STATUS_NEW, self._now()),
        )
        file_id = conn.execute(
            "SELECT id FROM files WHERE path = ?",
            ("scan.tif",),
        ).fetchone()[0]
        conn.commit()

        self.database.close_conn()

        with MakerStore(self.archive_path) as store:
            store.start_task(file_id, self._now())
            store.mark_failed(file_id, "boom", self._now())

        conn = self.database.get_conn()

        row = conn.execute(
            "SELECT status, error FROM tasks WHERE file_id = ? AND daemon = ?",
            (file_id, "preview-maker"),
        ).fetchone()

        assert row["status"] == "failed"
        assert row["error"] == "boom"