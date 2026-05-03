"""Regression tests for Keeper batch-mode behavior."""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from archive_keeper.keeper import Keeper
from common.database import (
    ArchiveDatabase,
    FILE_STATUS_ACTIVE,
    FILE_STATUS_MISSING,
    FILE_STATUS_MODIFIED,
    FILE_STATUS_NEW,
    TASK_STATUS_DONE,
    TASK_STATUS_PENDING,
)
from common.logger import Logger
from common.provider import list_providers


class TestKeeper:
    """Covers one-shot archive reconciliation performed by Keeper."""

    def setup_method(self) -> None:
        self.database: ArchiveDatabase | None = None

    def teardown_method(self) -> None:
        if self.database is not None:
            self.database.close_conn()

    @staticmethod
    def _checksum(file_path: Path) -> str:
        """Return the SHA-256 checksum of a test file."""
        return hashlib.sha256(file_path.read_bytes()).hexdigest()

    @staticmethod
    def _now() -> str:
        """Return the current UTC timestamp in the DB storage format."""
        return datetime.now(timezone.utc).isoformat()

    def _close_conn(self) -> None:
        """Close the shared SQLite connection before reopening the archive DB."""
        if self.database is not None:
            self.database.close_conn()

    def _reopen_conn(self, archive_path: Path):
        """Reattach the explicit test database wrapper to an existing archive DB."""
        if self.database is None:
            self.database = ArchiveDatabase(archive_path)
        return self.database.get_conn()

    def _insert_terminal_tasks(self, conn, file_id: int) -> None:
        for provider in list_providers():
            conn.execute(
                "INSERT INTO daemon_tasks (file_id, daemon, status, updated_at) VALUES (?, ?, ?, ?)",
                (file_id, provider.daemon_name, TASK_STATUS_DONE, self._now()),
            )

    def test_new_file_with_completed_tasks_is_hashed_and_promoted_to_active(self) -> None:
        """New files become active once keeper has a checksum and no pending tasks."""
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "scan.tif"
            source_file.write_bytes(b"new scan data")

            self.database = ArchiveDatabase(tmp_path)
            conn = self.database.get_conn()

            try:
                conn.execute(
                    "INSERT INTO files (path, status, imported_at) VALUES (?, ?, ?)",
                    ("scan.tif", FILE_STATUS_NEW, self._now()),
                )
                file_id = conn.execute(
                    "SELECT id FROM files WHERE path = ?",
                    ("scan.tif",),
                ).fetchone()[0]
                self._insert_terminal_tasks(conn, file_id)
                conn.commit()

                self._close_conn()

                logger = Logger("test")
                keeper = Keeper(logger)
                keeper.execute(path=tmp_path)

                conn = self._reopen_conn(tmp_path)
                row = conn.execute(
                    "SELECT status, checksum FROM files WHERE id = ?",
                    (file_id,),
                ).fetchone()

                assert row["status"] == FILE_STATUS_ACTIVE
                assert row["checksum"] == self._checksum(source_file)
            finally:
                self._close_conn()

    def test_modified_file_gets_rehashed_before_activation(self) -> None:
        """Modified files are rehashed before keeper promotes them back to active.

        This test seeds the DB with a file that already has status ``modified``,
        a stale checksum, and a completed downstream task. The expected behavior
        is that batch-mode ``Keeper`` recalculates the checksum from the
        file on disk and only then switches the file status to ``active``.
        """
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "scan.tif"
            source_file.write_bytes(b"updated scan data")

            self.database = ArchiveDatabase(tmp_path)
            conn = self.database.get_conn()

            try:
                conn.execute(
                    "INSERT INTO files (path, status, checksum, imported_at) VALUES (?, ?, ?, ?)",
                    ("scan.tif", FILE_STATUS_MODIFIED, "stale-checksum", self._now()),
                )
                file_id = conn.execute(
                    "SELECT id FROM files WHERE path = ?",
                    ("scan.tif",),
                ).fetchone()[0]
                self._insert_terminal_tasks(conn, file_id)
                conn.commit()

                self._close_conn()

                logger = Logger("test")
                keeper = Keeper(logger)
                keeper.execute(path=tmp_path)

                conn = self._reopen_conn(tmp_path)
                row = conn.execute(
                    "SELECT status, checksum FROM files WHERE id = ?",
                    (file_id,),
                ).fetchone()

                assert row["status"] == FILE_STATUS_ACTIVE
                assert row["checksum"] == self._checksum(source_file)
            finally:
                self._close_conn()

    def test_new_file_without_checksum_stays_new(self) -> None:
        """New files are not promoted to active until checksum calculation succeeds."""
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "scan.tif"
            source_file.write_bytes(b"new scan data")

            self.database = ArchiveDatabase(tmp_path)
            conn = self.database.get_conn()

            try:
                conn.execute(
                    "INSERT INTO files (path, status, imported_at) VALUES (?, ?, ?)",
                    ("scan.tif", FILE_STATUS_NEW, self._now()),
                )
                file_id = conn.execute(
                    "SELECT id FROM files WHERE path = ?",
                    ("scan.tif",),
                ).fetchone()[0]
                self._insert_terminal_tasks(conn, file_id)
                conn.commit()

                self._close_conn()

                logger = Logger("test")
                with patch("archive_keeper.keeper.KeeperProcessor.process", side_effect=RuntimeError("boom")):
                    keeper = Keeper(logger)
                    keeper.execute(path=tmp_path)

                conn = self._reopen_conn(tmp_path)
                row = conn.execute(
                    "SELECT status, checksum FROM files WHERE id = ?",
                    (file_id,),
                ).fetchone()

                assert row["status"] == FILE_STATUS_NEW
                assert row["checksum"] is None
            finally:
                self._close_conn()

    def test_active_file_missing_on_disk_is_marked_missing(self) -> None:
        """Active files that disappear from disk are marked missing."""
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "scan.tif"
            source_file.write_bytes(b"archive content")
            checksum = self._checksum(source_file)

            self.database = ArchiveDatabase(tmp_path)
            conn = self.database.get_conn()

            try:
                conn.execute(
                    "INSERT INTO files (path, status, checksum, imported_at) VALUES (?, ?, ?, ?)",
                    ("scan.tif", FILE_STATUS_ACTIVE, checksum, self._now()),
                )
                file_id = conn.execute(
                    "SELECT id FROM files WHERE path = ?",
                    ("scan.tif",),
                ).fetchone()[0]
                conn.commit()

                source_file.unlink()
                self._close_conn()

                logger = Logger("test")
                keeper = Keeper(logger)
                keeper.execute(path=tmp_path)

                conn = self._reopen_conn(tmp_path)
                row = conn.execute(
                    "SELECT status FROM files WHERE id = ?",
                    (file_id,),
                ).fetchone()

                assert row["status"] == FILE_STATUS_MISSING
            finally:
                self._close_conn()

    def test_recovered_missing_file_is_requeued_with_fresh_checksum(self) -> None:
        """Recovered files are requeued as new, reseeded with tasks, and rehashed."""
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "scan.tif"
            source_file.write_bytes(b"recovered scan data")

            self.database = ArchiveDatabase(tmp_path)
            conn = self.database.get_conn()

            try:
                conn.execute(
                    "INSERT INTO files (path, status, checksum, imported_at) VALUES (?, ?, ?, ?)",
                    ("scan.tif", FILE_STATUS_MISSING, "stale-checksum", self._now()),
                )
                file_id = conn.execute(
                    "SELECT id FROM files WHERE path = ?",
                    ("scan.tif",),
                ).fetchone()[0]
                conn.execute(
                    "INSERT INTO daemon_tasks (file_id, daemon, status, updated_at) VALUES (?, ?, ?, ?)",
                    (file_id, "preview-maker", TASK_STATUS_DONE, self._now()),
                )
                conn.commit()

                self._close_conn()

                logger = Logger("test")
                keeper = Keeper(logger)
                keeper.execute(path=tmp_path)

                conn = self._reopen_conn(tmp_path)
                row = conn.execute(
                    "SELECT status, checksum FROM files WHERE id = ?",
                    (file_id,),
                ).fetchone()
                task_rows = conn.execute(
                    "SELECT daemon, status FROM daemon_tasks WHERE file_id = ? ORDER BY daemon",
                    (file_id,),
                ).fetchall()

                assert row["status"] == FILE_STATUS_NEW
                assert row["checksum"] == self._checksum(source_file)
                assert [row["daemon"] for row in task_rows] == [
                    provider.daemon_name for provider in list_providers()
                ]
                assert all(row["status"] == TASK_STATUS_PENDING for row in task_rows)
            finally:
                self._close_conn()

    def test_new_file_stays_new_until_all_seeded_tasks_are_terminal(self) -> None:
        """Keeper must not activate a file while any seeded task is unfinished.

        This protects the import pipeline from races where one daemon finishes
        before the other task rows seeded for the file have reached terminal states.
        """
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_file = tmp_path / "scan.tif"
            source_file.write_bytes(b"new scan data")

            self.database = ArchiveDatabase(tmp_path)
            conn = self.database.get_conn()

            try:
                conn.execute(
                    "INSERT INTO files (path, status, imported_at) VALUES (?, ?, ?)",
                    ("scan.tif", FILE_STATUS_NEW, self._now()),
                )
                file_id = conn.execute(
                    "SELECT id FROM files WHERE path = ?",
                    ("scan.tif",),
                ).fetchone()[0]
                conn.execute(
                    "INSERT INTO daemon_tasks (file_id, daemon, status, updated_at) VALUES (?, ?, ?, ?)",
                    (file_id, "preview-maker", TASK_STATUS_DONE, self._now()),
                )
                conn.execute(
                    "INSERT INTO daemon_tasks (file_id, daemon, status, updated_at) VALUES (?, ?, ?, ?)",
                    (file_id, "tile-cutter", TASK_STATUS_DONE, self._now()),
                )
                conn.execute(
                    "INSERT INTO daemon_tasks (file_id, daemon, status, updated_at) VALUES (?, ?, ?, ?)",
                    (file_id, "face-recognizer", TASK_STATUS_PENDING, self._now()),
                )
                conn.commit()

                self._close_conn()

                keeper = Keeper(Logger("test"))
                keeper.execute(path=tmp_path)

                conn = self._reopen_conn(tmp_path)
                row = conn.execute(
                    "SELECT status, checksum FROM files WHERE id = ?",
                    (file_id,),
                ).fetchone()

                assert row["status"] == FILE_STATUS_NEW
                assert row["checksum"] == self._checksum(source_file)
            finally:
                self._close_conn()