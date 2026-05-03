"""Tests for tasks API route."""

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from fastapi import HTTPException

from common.database import ArchiveDatabase
from ui.web.routes.tasks import get_task, list_tasks


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _insert_task(conn, domain: str = "import", action: str = "scan") -> int:
    row_id = conn.execute(
        "INSERT INTO tasks (domain, action, status, payload, created_at) VALUES (?, ?, ?, ?, ?)",
        (domain, action, "done", '{"n": 1}', _now()),
    ).lastrowid
    conn.commit()
    return row_id  # type: ignore[return-value]


class TestListTasks:

    def test_returns_pagination_envelope(self) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            db = ArchiveDatabase(archive_path)
            conn = db.get_conn()
            _insert_task(conn)
            _insert_task(conn)
            db.close_conn()

            result = list_tasks(page=1, per_page=25, archive_path=archive_path, _user={"role": "admin"})

        assert result["total"] == 2
        assert result["page"] == 1
        assert result["pages"] == 1
        assert len(result["items"]) == 2

    def test_empty_archive_returns_zero(self) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            db = ArchiveDatabase(archive_path)
            db.get_conn()
            db.close_conn()

            result = list_tasks(page=1, per_page=25, archive_path=archive_path, _user={"role": "admin"})

        assert result["total"] == 0
        assert result["pages"] == 1
        assert result["items"] == []

    def test_pages_calculated_correctly(self) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            db = ArchiveDatabase(archive_path)
            conn = db.get_conn()
            for _ in range(5):
                _insert_task(conn)
            db.close_conn()

            result = list_tasks(page=1, per_page=2, archive_path=archive_path, _user={"role": "admin"})

        assert result["total"] == 5
        assert result["pages"] == 3
        assert len(result["items"]) == 2

    def test_pages_do_not_overlap(self) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            db = ArchiveDatabase(archive_path)
            conn = db.get_conn()
            for _ in range(4):
                _insert_task(conn)
            db.close_conn()

            p1 = list_tasks(page=1, per_page=2, archive_path=archive_path, _user={"role": "admin"})
            p2 = list_tasks(page=2, per_page=2, archive_path=archive_path, _user={"role": "admin"})

        ids_p1 = {r["id"] for r in p1["items"]}
        ids_p2 = {r["id"] for r in p2["items"]}
        assert ids_p1.isdisjoint(ids_p2)

    def test_ordered_newest_first(self) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            db = ArchiveDatabase(archive_path)
            conn = db.get_conn()
            id1 = _insert_task(conn)
            id2 = _insert_task(conn)
            id3 = _insert_task(conn)
            db.close_conn()

            result = list_tasks(page=1, per_page=25, archive_path=archive_path, _user={"role": "admin"})

        assert [r["id"] for r in result["items"]] == [id3, id2, id1]

    def test_payload_is_deserialized(self) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            db = ArchiveDatabase(archive_path)
            conn = db.get_conn()
            _insert_task(conn)
            db.close_conn()

            result = list_tasks(page=1, per_page=25, archive_path=archive_path, _user={"role": "admin"})

        assert result["items"][0]["payload"] == {"n": 1}


class TestGetTask:

    def test_returns_correct_task(self) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            db = ArchiveDatabase(archive_path)
            conn = db.get_conn()
            task_id = _insert_task(conn, domain="import", action="scan")
            db.close_conn()

            result = get_task(task_id=task_id, archive_path=archive_path, _user={"role": "admin"})

        assert result["id"] == task_id
        assert result["domain"] == "import"
        assert result["action"] == "scan"
        assert result["payload"] == {"n": 1}

    def test_raises_404_for_missing_task(self) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            db = ArchiveDatabase(archive_path)
            db.get_conn()
            db.close_conn()

            with pytest.raises(HTTPException) as exc_info:
                get_task(task_id=999, archive_path=archive_path, _user={"role": "admin"})

        assert exc_info.value.status_code == 404
