"""Bootstrap/status DB boundary for ui.web setup and startup flows."""

from pathlib import Path

from common.constants import ARCHIVE_DB_FILENAME, ARCHIVE_SYSTEM_DIR
from common.database import ArchiveDatabase


class SetupStore:
    """Thin package-local wrapper around archive DB bootstrap checks."""

    def __init__(self, archive_path: str | Path) -> None:
        self._archive_path = Path(archive_path)
        self._db_path = self._archive_path / ARCHIVE_SYSTEM_DIR / ARCHIVE_DB_FILENAME
        self._database = ArchiveDatabase(self._archive_path)

    def exists(self) -> bool:
        """Return True when the archive DB file already exists on disk."""
        return self._db_path.exists()

    def ensure_ready(self) -> None:
        """Create or open the archive DB once so the shared schema exists."""
        self._database.get_conn()
        self._database.close_conn()

    def has_any_users(self) -> bool:
        """Return True when an existing archive DB already contains users."""
        if not self.exists():
            return False

        try:
            row = self._database.get_conn().execute(
                "SELECT COUNT(*) AS count FROM users"
            ).fetchone()
            assert row is not None
            return int(row["count"]) > 0
        finally:
            self._database.close_conn()