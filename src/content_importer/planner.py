"""Planner for the import/scan task: wraps file registration with task tracking."""

from pathlib import Path
from typing import Any

from common.constants import ARCHIVE_DB_FILENAME, ARCHIVE_SYSTEM_DIR
from common.task_store import TaskStore
from content_importer.store import ImporterStore


def _db_exists(archive_path: Path) -> bool:
    return (archive_path / ARCHIVE_SYSTEM_DIR / ARCHIVE_DB_FILENAME).exists()


class ImportScanPlanner:
    """Creates an import/scan task with one step per file, then runs registration inline."""

    def run(
        self,
        archive_path: Path,
        *,
        collection_id: int | None,
        files: list[dict[str, Any]],
    ) -> int | None:
        """Register imported files wrapped in a task. Returns task_id or None if no archive DB."""
        if not files or not _db_exists(archive_path):
            return None

        with TaskStore(archive_path) as store:
            task_id = store.create_task(
                domain="import",
                action="scan",
                payload={"collection_id": collection_id, "file_count": len(files)},
            )
            step_ids = [
                store.create_step(
                    task_id=task_id,
                    kind="register_file",
                    payload={"path": str(file_data["dest_path"])},
                )
                for file_data in files
            ]
            store.start_task(task_id)

            try:
                ImporterStore(archive_path).register_imported_files(
                    collection_id=collection_id,
                    files=files,
                )
            except Exception:
                for step_id in step_ids:
                    store.fail_step(step_id, "batch failed")
                store.fail_task(task_id)
                raise
            else:
                for step_id in step_ids:
                    store.finish_step(step_id)
                store.finish_task(task_id)

        return task_id
