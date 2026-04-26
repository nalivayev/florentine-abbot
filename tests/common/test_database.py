"""Regression tests for explicit common.database ArchiveDatabase instances."""

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from common.constants import ARCHIVE_DB_FILENAME, ARCHIVE_SYSTEM_DIR
from common.database import ArchiveDatabase


class TestArchiveDatabase:
    """Covers the explicit ArchiveDatabase runtime wrapper."""

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def test_archive_database_manages_its_connection(self) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            database = ArchiveDatabase(archive_path)

            conn = database.get_conn()

            db_path = archive_path / ARCHIVE_SYSTEM_DIR / ARCHIVE_DB_FILENAME
            assert db_path.exists()
            assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0

            role_id = conn.execute(
                "SELECT id FROM roles WHERE name = 'admin'"
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO users (username, password_hash, role_id, created_at) VALUES (?, ?, ?, ?)",
                ("admin", "hashed", role_id, self._now()),
            )
            conn.commit()

            assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1

            database.close_conn()
            reopened = database.get_conn()
            assert reopened.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
            database.close_conn()

    def test_second_archive_database_instance_reopens_existing_db(self) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            writer = ArchiveDatabase(archive_path)
            reader = ArchiveDatabase(archive_path)

            conn = writer.get_conn()
            role_id = conn.execute(
                "SELECT id FROM roles WHERE name = 'admin'"
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO users (username, password_hash, role_id, created_at) VALUES (?, ?, ?, ?)",
                ("admin", "hashed", role_id, self._now()),
            )
            conn.commit()

            writer.close_conn()

            assert reader.get_conn().execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1

            reader.close_conn()
            assert reader.get_conn().execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
            reader.close_conn()