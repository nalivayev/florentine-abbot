"""Database boundary for ui.web authentication and user management."""

from pathlib import Path
import sqlite3
from typing import Any

from common.database import ArchiveDatabase


class WebStore:
    """Thin package-local wrapper around shared auth and user tables."""

    _USER_SUMMARY_SELECT = """
        SELECT u.id, u.username, r.name AS role, u.is_active, u.created_at, u.last_login_at
        FROM users u
        JOIN roles r ON r.id = u.role_id
    """

    def __init__(self, archive_path: str | Path) -> None:
        self._database = ArchiveDatabase(Path(archive_path))
        self._conn: sqlite3.Connection | None = None

    def __enter__(self) -> "WebStore":
        return self._open()

    def __exit__(self, *_) -> None:
        self._close()

    def _open(self) -> "WebStore":
        if self._conn is not None:
            return self
        self._conn = self._database.get_conn()
        return self

    def _close(self) -> None:
        """Release the owned DB connection after a request-scoped use."""
        if self._conn is None:
            return
        self._conn.commit()
        self._conn = None
        self._database.close_conn()

    @property
    def _c(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("WebStore is not open")
        return self._conn

    def _commit(self) -> None:
        self._c.commit()

    def get_user_for_login(self, username: str) -> dict[str, Any] | None:
        """Return the login row for *username*, if present."""
        row = self._c.execute(
            "SELECT id, username, password_hash, is_active FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return None if row is None else dict(row)

    def get_user_by_token_hash(self, token_hash: str) -> dict[str, Any] | None:
        """Return the current-user row for a session token hash, if present."""
        row = self._c.execute(
            """
            SELECT u.id, u.username, u.is_active, u.role_id,
                   r.name AS role, s.expires_at, s.token_hash
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            JOIN roles r ON r.id = u.role_id
            WHERE s.token_hash = ?
            """,
            (token_hash,),
        ).fetchone()
        return None if row is None else dict(row)

    def create_session(
        self,
        *,
        user_id: int,
        token_hash: str,
        created_at: str,
        expires_at: str,
    ) -> None:
        """Create a new auth session row."""
        self._c.execute(
            "INSERT INTO sessions (user_id, token_hash, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (user_id, token_hash, created_at, expires_at),
        )
        self._commit()

    def delete_session(self, user_id: int, token_hash: str) -> None:
        """Delete one auth session row."""
        self._c.execute(
            "DELETE FROM sessions WHERE user_id = ? AND token_hash = ?",
            (user_id, token_hash),
        )
        self._commit()

    def update_last_login(self, user_id: int, last_login_at: str) -> None:
        """Persist the latest successful login timestamp."""
        self._c.execute(
            "UPDATE users SET last_login_at = ? WHERE id = ?",
            (last_login_at, user_id),
        )
        self._commit()

    def get_role_id(self, role_name: str) -> int | None:
        """Return the role id for *role_name*, if present."""
        row = self._c.execute(
            "SELECT id FROM roles WHERE name = ?",
            (role_name,),
        ).fetchone()
        return None if row is None else int(row["id"])

    def username_exists(self, username: str) -> bool:
        """Return True when *username* is already taken."""
        row = self._c.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return row is not None

    def create_user(
        self,
        *,
        username: str,
        password_hash: str,
        role_id: int,
        created_at: str,
        created_by: int | None = None,
    ) -> int:
        """Insert one user row and return its id."""
        cursor = self._c.execute(
            "INSERT INTO users (username, password_hash, role_id, is_active, created_by, created_at) VALUES (?, ?, ?, 1, ?, ?)",
            (username, password_hash, role_id, created_by, created_at),
        )
        assert cursor.lastrowid is not None
        self._commit()
        return int(cursor.lastrowid)

    def get_user_summary(self, username: str) -> dict[str, Any] | None:
        """Return the list-view user row for *username*, if present."""
        row = self._c.execute(
            self._USER_SUMMARY_SELECT + " WHERE u.username = ?",
            (username,),
        ).fetchone()
        return None if row is None else dict(row)

    def list_users(self) -> list[dict[str, Any]]:
        """Return all user rows for the admin users list."""
        rows = self._c.execute(
            self._USER_SUMMARY_SELECT + " ORDER BY u.id"
        ).fetchall()
        return [dict(row) for row in rows]

    def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        """Return the minimal user row for *user_id*, if present."""
        row = self._c.execute(
            "SELECT id FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return None if row is None else dict(row)

    def delete_user_sessions(self, user_id: int) -> None:
        """Delete all sessions owned by *user_id*."""
        self._c.execute(
            "DELETE FROM sessions WHERE user_id = ?",
            (user_id,),
        )
        self._commit()

    def delete_user(self, user_id: int) -> None:
        """Delete one user row."""
        self._c.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,),
        )
        self._commit()

    def list_collections(self) -> list[dict[str, Any]]:
        """Return all collection rows."""
        rows = self._c.execute(
            "SELECT id, type, name, created_at FROM collections ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]

    def list_files(self, collection_id: int | None = None) -> list[dict[str, Any]]:
        """Return file rows, optionally filtered by collection."""
        query = "SELECT id, collection_id, path, status, checksum, imported_at FROM files"
        params: tuple[object, ...] = ()
        if collection_id is not None:
            query += " WHERE collection_id = ?"
            params = (collection_id,)
        query += " ORDER BY path"
        rows = self._c.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def list_file_paths(self, collection_id: int | None = None) -> list[dict[str, Any]]:
        """Return minimal id/path rows, optionally filtered by collection."""
        query = "SELECT id, collection_id, path FROM files"
        params: tuple[object, ...] = ()
        if collection_id is not None:
            query += " WHERE collection_id = ?"
            params = (collection_id,)
        query += " ORDER BY path"
        rows = self._c.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_file_detail(self, file_id: int, collection_id: int | None = None) -> dict[str, Any] | None:
        """Return one file with its semantic metadata and GPS projection."""
        query = """
            SELECT
                f.id,
                f.collection_id,
                f.path,
                f.status,
                f.checksum,
                f.imported_at,
                fm.photo_year,
                fm.photo_month,
                fm.photo_day,
                fm.photo_time,
                fm.date_accuracy,
                fm.description,
                fm.source,
                fm.credit,
                fg.lat AS gps_lat,
                fg.lon AS gps_lon,
                fg.altitude AS gps_altitude
            FROM files f
            LEFT JOIN file_metadata fm ON fm.file_id = f.id
            LEFT JOIN file_meta_gps fg ON fg.file_id = f.id
            WHERE f.id = ?
        """
        params: tuple[object, ...] = (file_id,)
        if collection_id is not None:
            query += " AND f.collection_id = ?"
            params += (collection_id,)

        row = self._c.execute(query, params).fetchone()
        return None if row is None else dict(row)

    def list_file_creators(self, file_id: int) -> list[str]:
        """Return ordered creator names for one file."""
        rows = self._c.execute(
            "SELECT name FROM file_creators WHERE file_id = ? ORDER BY position",
            (file_id,),
        ).fetchall()
        return [str(row["name"]) for row in rows]

    def list_file_history(self, file_id: int) -> list[dict[str, Any]]:
        """Return ordered semantic history entries for one file."""
        rows = self._c.execute(
            """
            SELECT action, recorded_at, software, changed, instance_id
            FROM file_history
            WHERE file_id = ?
            ORDER BY recorded_at, id
            """,
            (file_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def create_collection(self, collection_type: str, name: str, created_at: str) -> dict[str, Any]:
        """Insert one collection row and return it."""
        cursor = self._c.execute(
            "INSERT INTO collections (type, name, created_at) VALUES (?, ?, ?)",
            (collection_type, name, created_at),
        )
        assert cursor.lastrowid is not None
        self._commit()
        row = self._c.execute(
            "SELECT id, type, name, created_at FROM collections WHERE id = ?",
            (int(cursor.lastrowid),),
        ).fetchone()
        assert row is not None
        return dict(row)
