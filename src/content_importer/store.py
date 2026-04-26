"""Database boundary for content importer archive registration."""

from pathlib import Path
import sqlite3
from typing import Any

from common.constants import ARCHIVE_DB_FILENAME, ARCHIVE_SYSTEM_DIR
from common.database import ArchiveDatabase, FILE_STATUS_NEW, TASK_STATUS_PENDING
from common.provider import list_providers


class ImporterStore:
    """Thin package-local wrapper around optional DB registration for imports."""

    def __init__(self, archive_path: str | Path) -> None:
        self._archive_path = Path(archive_path)
        self._database = ArchiveDatabase(self._archive_path)
        self._conn: sqlite3.Connection | None = None

    def _open(self) -> bool:
        """Attach to the archive DB if it already exists on disk."""
        if self._conn is not None:
            return True
        db_path = self._archive_path / ARCHIVE_SYSTEM_DIR / ARCHIVE_DB_FILENAME
        if not db_path.exists():
            return False
        self._conn = self._database.get_conn()
        return True

    def _close(self) -> None:
        """Commit pending writes and detach from the shared connection."""
        if self._conn is None:
            return
        self._conn.commit()
        self._conn = None
        self._database.close_conn()

    @property
    def _c(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("ImporterStore is not open")
        return self._conn

    def _commit(self) -> None:
        self._c.commit()

    def _seed_tasks_for_file(self, *, file_id: int, updated_at: str) -> None:
        for provider in list_providers():
            self._c.execute(
                "INSERT OR IGNORE INTO tasks (file_id, daemon, status, updated_at) VALUES (?, ?, ?, ?)",
                (file_id, provider.daemon_name, TASK_STATUS_PENDING, updated_at),
            )

    def _register_imported_file(
        self,
        *,
        collection_id: int | None,
        dest_path: Path,
        imported_at: str,
    ) -> int:
        """Register one successfully imported file in the shared archive DB."""
        rel_path = str(dest_path.relative_to(self._archive_path))
        self._c.execute(
            "INSERT OR IGNORE INTO files (collection_id, path, status, imported_at) VALUES (?, ?, ?, ?)",
            (collection_id, rel_path, FILE_STATUS_NEW, imported_at),
        )
        row = self._c.execute(
            "SELECT id FROM files WHERE path = ?",
            (rel_path,),
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Failed to register imported file: {rel_path}")
        return int(row["id"])

    def _write_file_metadata(self, *, file_id: int, metadata: dict[str, Any]) -> None:
        self._c.execute(
            """
            INSERT OR REPLACE INTO file_metadata (
                file_id, photo_year, photo_month, photo_day, photo_time,
                date_accuracy, description, source, credit
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                file_id,
                metadata.get("photo_year"),
                metadata.get("photo_month"),
                metadata.get("photo_day"),
                metadata.get("photo_time"),
                metadata.get("date_accuracy"),
                metadata.get("description"),
                metadata.get("source"),
                metadata.get("credit"),
            ),
        )

    def _replace_file_creators(self, *, file_id: int, creators: list[str]) -> None:
        self._c.execute("DELETE FROM file_creators WHERE file_id = ?", (file_id,))
        for position, name in enumerate(creators, start=1):
            self._c.execute(
                "INSERT INTO file_creators (file_id, position, name) VALUES (?, ?, ?)",
                (file_id, position, name),
            )

    def _append_file_history(self, *, file_id: int, entries: list[dict[str, Any]]) -> None:
        for entry in entries:
            self._c.execute(
                """
                INSERT INTO file_history (file_id, action, recorded_at, software, changed, instance_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    file_id,
                    entry.get("action"),
                    entry.get("recorded_at"),
                    entry.get("software"),
                    entry.get("changed"),
                    entry.get("instance_id"),
                ),
            )

    def register_imported_files(
        self,
        *,
        collection_id: int | None,
        files: list[dict[str, Any]],
    ) -> None:
        """Register imported files when the archive DB already exists."""
        if not self._open():
            return

        try:
            for file_data in files:
                file_id = self._register_imported_file(
                    collection_id=collection_id,
                    dest_path=file_data["dest_path"],
                    imported_at=file_data["imported_at"],
                )
                self._seed_tasks_for_file(
                    file_id=file_id,
                    updated_at=file_data["imported_at"],
                )
                self._write_file_metadata(
                    file_id=file_id,
                    metadata=file_data.get("metadata", {}),
                )
                self._replace_file_creators(
                    file_id=file_id,
                    creators=file_data.get("creators", []),
                )
                self._append_file_history(
                    file_id=file_id,
                    entries=file_data.get("history", []),
                )
            self._commit()
        finally:
            self._close()
