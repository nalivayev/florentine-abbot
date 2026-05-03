"""Regression tests for Cutter database-backed orchestration."""

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from common.database import ArchiveDatabase
from common.database import FILE_STATUS_MODIFIED, TASK_STATUS_DONE, TASK_STATUS_PENDING
from common.logger import Logger
from tile_cutter.cutter import Cutter


class TestCutterDb:
    """Covers DB/task orchestration now owned by Cutter."""

    @staticmethod
    def _now() -> str:
        """Return the current UTC timestamp in the DB storage format."""
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _close_conn(database: ArchiveDatabase) -> None:
        """Close the shared SQLite connection between setup and verification."""
        database.close_conn()

    def test_modified_file_uses_overwrite_for_existing_tile_set(self) -> None:
        """Modified files are processed with overwrite enabled by the cutter cycle."""
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            database = ArchiveDatabase(tmp_path)
            source_file = tmp_path / "scan.tif"
            source_file.write_bytes(b"scan data")

            conn = database.get_conn()

            try:
                conn.execute(
                    "INSERT INTO files (path, status, imported_at) VALUES (?, ?, ?)",
                    ("scan.tif", FILE_STATUS_MODIFIED, self._now()),
                )
                file_id = conn.execute(
                    "SELECT id FROM files WHERE path = ?",
                    ("scan.tif",),
                ).fetchone()[0]
                conn.execute(
                    "INSERT INTO daemon_tasks (file_id, daemon, status, updated_at) VALUES (?, ?, ?, ?)",
                    (file_id, "tile-cutter", TASK_STATUS_PENDING, self._now()),
                )
                conn.commit()

                self._close_conn(database)

                logger = Logger("test")
                with patch.object(Cutter, "_should_process", return_value=True), patch.object(
                    Cutter,
                    "_process_single_file",
                    return_value=True,
                ) as mock_process:
                    cutter = Cutter(logger)
                    cutter.poll(tmp_path)

                conn = database.get_conn()
                row = conn.execute(
                    "SELECT status FROM daemon_tasks WHERE file_id = ? AND daemon = ?",
                    (file_id, "tile-cutter"),
                ).fetchone()

                assert row["status"] == TASK_STATUS_DONE
                mock_process.assert_called_once_with(
                    source_file,
                    archive_path=tmp_path,
                    overwrite=True,
                )
            finally:
                self._close_conn(database)
