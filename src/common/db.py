"""
Shared SQLite database for Florentine Abbot.

The database lives in the archive root: {archive}/florentine.db
Call init_db(archive_path) once at startup before using get_conn().
"""

import sqlite3
from pathlib import Path
from typing import Optional

_conn: Optional[sqlite3.Connection] = None


def init_db(archive_path: str | Path) -> None:
    """Open (or create) florentine.db in archive_path and create tables."""
    global _conn
    db_path = Path(archive_path) / "florentine.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _conn = sqlite3.connect(str(db_path), check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    _conn.execute("PRAGMA journal_mode=WAL")
    _conn.execute("PRAGMA foreign_keys=ON")
    _create_tables(_conn)


def get_conn() -> sqlite3.Connection:
    """Return the active connection. Raises if init_db() was not called."""
    if _conn is None:
        raise RuntimeError("Database is not initialized. Call init_db() first.")
    return _conn


def is_initialized() -> bool:
    """Return True if the database has at least one user."""
    if _conn is None:
        return False
    row = _conn.execute("SELECT COUNT(*) FROM users").fetchone()
    return row[0] > 0


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS roles (
            id          INTEGER PRIMARY KEY,
            name        TEXT    UNIQUE NOT NULL,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY,
            username      TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            role_id       INTEGER NOT NULL REFERENCES roles(id),
            is_active     INTEGER NOT NULL DEFAULT 1,
            created_by    INTEGER REFERENCES users(id),
            created_at    TEXT    NOT NULL,
            last_login_at TEXT
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            token_hash  TEXT    UNIQUE NOT NULL,
            created_at  TEXT    NOT NULL,
            expires_at  TEXT    NOT NULL
        );

        INSERT OR IGNORE INTO roles (name, description)
            VALUES ('admin', 'Administrator');
        INSERT OR IGNORE INTO roles (name, description)
            VALUES ('user', 'Regular user');
    """)
    conn.commit()
