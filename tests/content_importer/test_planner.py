"""Tests for ImportScanPlanner."""

from pathlib import Path
from unittest.mock import patch

import pytest

from common.database import ArchiveDatabase
from content_importer.planner import ImportScanPlanner


def _init_db(archive_path: Path) -> None:
    db = ArchiveDatabase(archive_path)
    db.get_conn()
    db.close_conn()


def _file_data(archive_path: Path, name: str = "scan.tif") -> dict:
    return {
        "dest_path": archive_path / name,
        "imported_at": "2024-01-01T00:00:00+00:00",
        "metadata": {"photo_year": 2024, "date_accuracy": "exact"},
        "creators": [],
        "history": [],
    }


class TestImportScanPlanner:

    def test_returns_none_when_archive_db_absent(self, tmp_path: Path) -> None:
        result = ImportScanPlanner().run(
            tmp_path,
            collection_id=None,
            files=[_file_data(tmp_path)],
        )
        assert result is None

    def test_returns_none_for_empty_file_list(self, tmp_path: Path) -> None:
        _init_db(tmp_path)
        result = ImportScanPlanner().run(tmp_path, collection_id=None, files=[])
        assert result is None

    def test_success_returns_task_id_and_task_is_done(self, tmp_path: Path) -> None:
        _init_db(tmp_path)

        task_id = ImportScanPlanner().run(
            tmp_path,
            collection_id=None,
            files=[_file_data(tmp_path, "a.tif"), _file_data(tmp_path, "b.tif")],
        )

        assert task_id is not None

        db = ArchiveDatabase(tmp_path)
        conn = db.get_conn()
        task_row = conn.execute(
            "SELECT domain, action, status, steps, done, failed FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
        step_rows = conn.execute(
            "SELECT status FROM task_steps WHERE task_id = ?", (task_id,)
        ).fetchall()
        db.close_conn()

        assert task_row["domain"] == "import"
        assert task_row["action"] == "scan"
        assert task_row["status"] == "done"
        assert task_row["steps"] == 2
        assert task_row["done"] == 2
        assert task_row["failed"] == 0
        assert all(r["status"] == "done" for r in step_rows)

    def test_failure_marks_task_and_steps_failed_and_reraises(self, tmp_path: Path) -> None:
        _init_db(tmp_path)

        with patch("content_importer.planner.ImporterStore") as mock_cls:
            mock_cls.return_value.register_imported_files.side_effect = RuntimeError("DB error")

            with pytest.raises(RuntimeError, match="DB error"):
                ImportScanPlanner().run(
                    tmp_path,
                    collection_id=None,
                    files=[_file_data(tmp_path)],
                )

        db = ArchiveDatabase(tmp_path)
        conn = db.get_conn()
        task_row = conn.execute("SELECT status, failed FROM tasks").fetchone()
        step_rows = conn.execute("SELECT status FROM task_steps").fetchall()
        db.close_conn()

        assert task_row["status"] == "failed"
        assert len(step_rows) == 1
        assert step_rows[0]["status"] == "failed"

    def test_no_db_created_when_archive_absent(self, tmp_path: Path) -> None:
        from common.constants import ARCHIVE_DB_FILENAME, ARCHIVE_SYSTEM_DIR

        ImportScanPlanner().run(tmp_path, collection_id=None, files=[_file_data(tmp_path)])

        assert not (tmp_path / ARCHIVE_SYSTEM_DIR / ARCHIVE_DB_FILENAME).exists()
