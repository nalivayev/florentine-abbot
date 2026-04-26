"""Regression tests for ui.web SetupStore bootstrap DB operations."""

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from common.constants import ARCHIVE_DB_FILENAME, ARCHIVE_SYSTEM_DIR
from common.database import ArchiveDatabase
from ui.web.setup_store import SetupStore


class TestSetupStore:
    """Covers ui.web bootstrap/status DB operations behind SetupStore."""

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def test_exists_is_false_without_db_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            store = SetupStore(archive_path)

            assert store.exists() is False
            assert store.has_any_users() is False

    def test_ensure_ready_creates_db_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            store = SetupStore(archive_path)

            store.ensure_ready()

            assert store.exists() is True
            assert (archive_path / ARCHIVE_SYSTEM_DIR / ARCHIVE_DB_FILENAME).exists()

    def test_has_any_users_tracks_existing_db_state(self) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            store = SetupStore(archive_path)
            database = ArchiveDatabase(archive_path)

            store.ensure_ready()
            assert store.has_any_users() is False

            try:
                conn = database.get_conn()
                role_id = conn.execute(
                    "SELECT id FROM roles WHERE name = 'admin'"
                ).fetchone()[0]
                conn.execute(
                    "INSERT INTO users (username, password_hash, role_id, created_at) VALUES (?, ?, ?, ?)",
                    ("admin", "hashed", role_id, self._now()),
                )
                conn.commit()
            finally:
                database.close_conn()

            assert store.has_any_users() is True