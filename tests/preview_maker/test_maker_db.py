"""Regression tests for Maker database-backed orchestration."""

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from archive_keeper.keeper import Keeper
from common.database import ArchiveDatabase
from common.database import FILE_STATUS_MODIFIED, FILE_STATUS_NEW, TASK_STATUS_DONE, TASK_STATUS_PENDING
from common.logger import Logger
from common.provider import list_providers
from preview_maker.maker import Maker


class TestMakerDb:
    """Covers DB/task orchestration now owned by Maker."""

    @staticmethod
    def _now() -> str:
        """Return the current UTC timestamp in the DB storage format."""
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _close_conn(database: ArchiveDatabase) -> None:
        """Close the shared SQLite connection between setup and verification."""
        database.close_conn()

    def test_modified_file_uses_overwrite_for_existing_preview(self) -> None:
        """Modified files are processed with overwrite enabled by the maker cycle."""
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
                    "INSERT INTO tasks (file_id, daemon, status, updated_at) VALUES (?, ?, ?, ?)",
                    (file_id, "preview-maker", TASK_STATUS_PENDING, self._now()),
                )
                conn.commit()

                self._close_conn(database)

                logger = Logger("test")
                with patch.object(Maker, "_should_process", return_value=True), patch.object(
                    Maker,
                    "_process_single_file",
                    return_value=True,
                ) as mock_process:
                    maker = Maker(logger)
                    maker.poll(tmp_path)

                conn = database.get_conn()
                row = conn.execute(
                    "SELECT status FROM tasks WHERE file_id = ? AND daemon = ?",
                    (file_id, "preview-maker"),
                ).fetchone()

                assert row["status"] == TASK_STATUS_DONE
                mock_process.assert_called_once_with(
                    source_file,
                    archive_path=tmp_path,
                    overwrite=True,
                )
            finally:
                self._close_conn(database)

    def test_preview_maker_still_sees_new_file_after_keeper_runs_first(self) -> None:
        """Keeper must not starve preview-maker when another daemon finishes first.

        This reproduces the import-time race reported in the web workflow:
        a freshly imported file gets a completed tile-cutter task, keeper runs,
        and preview-maker must still be able to poll and process that same file.
        """
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            database = ArchiveDatabase(tmp_path)
            source_file = tmp_path / "scan.tif"
            source_file.write_bytes(b"scan data")

            conn = database.get_conn()

            try:
                conn.execute(
                    "INSERT INTO files (path, status, imported_at) VALUES (?, ?, ?)",
                    ("scan.tif", FILE_STATUS_NEW, self._now()),
                )
                file_id = conn.execute(
                    "SELECT id FROM files WHERE path = ?",
                    ("scan.tif",),
                ).fetchone()[0]
                for provider in list_providers():
                    status = TASK_STATUS_DONE if provider.daemon_name == "tile-cutter" else TASK_STATUS_PENDING
                    conn.execute(
                        "INSERT INTO tasks (file_id, daemon, status, updated_at) VALUES (?, ?, ?, ?)",
                        (file_id, provider.daemon_name, status, self._now()),
                    )
                conn.commit()

                self._close_conn(database)

                keeper = Keeper(Logger("test-keeper"))
                keeper.poll(tmp_path)

                logger = Logger("test-maker")
                with patch.object(Maker, "_should_process", return_value=True), patch.object(
                    Maker,
                    "_process_single_file",
                    return_value=True,
                ) as mock_process:
                    maker = Maker(logger)
                    processed = maker.poll(tmp_path)

                conn = database.get_conn()
                file_row = conn.execute(
                    "SELECT status FROM files WHERE id = ?",
                    (file_id,),
                ).fetchone()
                task_row = conn.execute(
                    "SELECT status FROM tasks WHERE file_id = ? AND daemon = ?",
                    (file_id, "preview-maker"),
                ).fetchone()

                assert processed == 1
                assert file_row["status"] == FILE_STATUS_NEW
                assert task_row["status"] == TASK_STATUS_DONE
                mock_process.assert_called_once_with(
                    source_file,
                    archive_path=tmp_path,
                    overwrite=False,
                )
            finally:
                self._close_conn(database)
