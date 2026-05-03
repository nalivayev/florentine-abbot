"""Tests for TaskStore."""

from pathlib import Path

from common.database import ArchiveDatabase
from common.task_store import TaskStore


def _init_db(archive_path: Path) -> None:
    db = ArchiveDatabase(archive_path)
    db.get_conn()
    db.close_conn()


def _query(archive_path: Path, sql: str, *params):
    db = ArchiveDatabase(archive_path)
    row = db.get_conn().execute(sql, params).fetchone()
    db.close_conn()
    return row


class TestTaskStore:

    def test_create_task_returns_positive_id(self, tmp_path: Path) -> None:
        _init_db(tmp_path)
        with TaskStore(tmp_path) as store:
            task_id = store.create_task(domain="import", action="scan", payload={"n": 1})
        assert isinstance(task_id, int)
        assert task_id > 0

    def test_created_task_has_pending_status(self, tmp_path: Path) -> None:
        _init_db(tmp_path)
        with TaskStore(tmp_path) as store:
            task_id = store.create_task(domain="import", action="scan", payload={})
        row = _query(tmp_path, "SELECT status FROM tasks WHERE id = ?", task_id)
        assert row["status"] == "pending"

    def test_start_task_sets_running_with_timestamp(self, tmp_path: Path) -> None:
        _init_db(tmp_path)
        with TaskStore(tmp_path) as store:
            task_id = store.create_task(domain="import", action="scan", payload={})
            store.start_task(task_id)
        row = _query(tmp_path, "SELECT status, started_at FROM tasks WHERE id = ?", task_id)
        assert row["status"] == "running"
        assert row["started_at"] is not None

    def test_finish_task_sets_done_with_timestamp(self, tmp_path: Path) -> None:
        _init_db(tmp_path)
        with TaskStore(tmp_path) as store:
            task_id = store.create_task(domain="import", action="scan", payload={})
            store.start_task(task_id)
            store.finish_task(task_id)
        row = _query(tmp_path, "SELECT status, finished_at FROM tasks WHERE id = ?", task_id)
        assert row["status"] == "done"
        assert row["finished_at"] is not None

    def test_fail_task_sets_failed(self, tmp_path: Path) -> None:
        _init_db(tmp_path)
        with TaskStore(tmp_path) as store:
            task_id = store.create_task(domain="import", action="scan", payload={})
            store.fail_task(task_id)
        row = _query(tmp_path, "SELECT status FROM tasks WHERE id = ?", task_id)
        assert row["status"] == "failed"

    def test_create_step_increments_task_steps_counter(self, tmp_path: Path) -> None:
        _init_db(tmp_path)
        with TaskStore(tmp_path) as store:
            task_id = store.create_task(domain="import", action="scan", payload={})
            store.create_step(task_id=task_id, kind="register_file", payload={"path": "a.tif"})
            store.create_step(task_id=task_id, kind="register_file", payload={"path": "b.tif"})
        row = _query(tmp_path, "SELECT steps FROM tasks WHERE id = ?", task_id)
        assert row["steps"] == 2

    def test_finish_step_increments_task_done(self, tmp_path: Path) -> None:
        _init_db(tmp_path)
        with TaskStore(tmp_path) as store:
            task_id = store.create_task(domain="import", action="scan", payload={})
            step_id = store.create_step(task_id=task_id, kind="register_file", payload={})
            store.finish_step(step_id)
        row = _query(tmp_path, "SELECT done, failed FROM tasks WHERE id = ?", task_id)
        assert row["done"] == 1
        assert row["failed"] == 0

    def test_fail_step_increments_task_failed_and_stores_error(self, tmp_path: Path) -> None:
        _init_db(tmp_path)
        with TaskStore(tmp_path) as store:
            task_id = store.create_task(domain="import", action="scan", payload={})
            step_id = store.create_step(task_id=task_id, kind="register_file", payload={})
            store.fail_step(step_id, "something went wrong")
        task_row = _query(tmp_path, "SELECT done, failed FROM tasks WHERE id = ?", task_id)
        step_row = _query(tmp_path, "SELECT status, error FROM task_steps WHERE id = ?", step_id)
        assert task_row["failed"] == 1
        assert task_row["done"] == 0
        assert step_row["status"] == "failed"
        assert step_row["error"] == "something went wrong"

    def test_multiple_steps_counters_are_independent(self, tmp_path: Path) -> None:
        _init_db(tmp_path)
        with TaskStore(tmp_path) as store:
            task_id = store.create_task(domain="import", action="scan", payload={})
            step_ok = store.create_step(task_id=task_id, kind="register_file", payload={})
            step_bad = store.create_step(task_id=task_id, kind="register_file", payload={})
            store.finish_step(step_ok)
            store.fail_step(step_bad, "err")
        row = _query(tmp_path, "SELECT steps, done, failed FROM tasks WHERE id = ?", task_id)
        assert row["steps"] == 2
        assert row["done"] == 1
        assert row["failed"] == 1
