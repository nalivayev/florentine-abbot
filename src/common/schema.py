"""SQLite schema fragments owned by common."""

SCHEMA_SQL = """
    CREATE TABLE IF NOT EXISTS collections (
        id          INTEGER PRIMARY KEY,
        type        TEXT    NOT NULL,
        name        TEXT    NOT NULL,
        created_at  TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS files (
        id            INTEGER PRIMARY KEY,
        collection_id INTEGER REFERENCES collections(id),
        path          TEXT    UNIQUE NOT NULL,
        status        TEXT    NOT NULL DEFAULT 'new',
        checksum      TEXT,
        imported_at   TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id          INTEGER PRIMARY KEY,
        file_id     INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
        daemon      TEXT    NOT NULL,
        status      TEXT    NOT NULL DEFAULT 'pending',
        error       TEXT,
        updated_at  TEXT    NOT NULL,
        UNIQUE(file_id, daemon)
    );

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

    CREATE TABLE IF NOT EXISTS file_metadata (
        file_id        INTEGER PRIMARY KEY REFERENCES files(id) ON DELETE CASCADE,
        photo_year     INTEGER,
        photo_month    INTEGER,
        photo_day      INTEGER,
        photo_time     TEXT,
        date_accuracy  TEXT,
        description    TEXT,
        source         TEXT,
        credit         TEXT
    );

    CREATE TABLE IF NOT EXISTS file_creators (
        file_id    INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
        position   INTEGER NOT NULL,
        name       TEXT    NOT NULL,
        PRIMARY KEY (file_id, position)
    );

    CREATE TABLE IF NOT EXISTS file_history (
        id           INTEGER PRIMARY KEY,
        file_id      INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
        action       TEXT    NOT NULL,
        recorded_at  TEXT    NOT NULL,
        software     TEXT,
        changed      TEXT,
        instance_id  TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_file_history_file_recorded_at
        ON file_history(file_id, recorded_at);

    CREATE TABLE IF NOT EXISTS file_meta_xmp_dc (
        file_id     INTEGER PRIMARY KEY REFERENCES files(id) ON DELETE CASCADE,
        title       TEXT,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS file_meta_ifd0 (
        file_id  INTEGER PRIMARY KEY REFERENCES files(id) ON DELETE CASCADE,
        make     TEXT,
        model    TEXT,
        software TEXT
    );

    CREATE TABLE IF NOT EXISTS file_meta_exif (
        file_id INTEGER PRIMARY KEY REFERENCES files(id) ON DELETE CASCADE,
        year    INTEGER,
        month   INTEGER,
        day     INTEGER,
        time    TEXT,
        tz      TEXT
    );

    CREATE TABLE IF NOT EXISTS file_meta_gps (
        file_id  INTEGER PRIMARY KEY REFERENCES files(id) ON DELETE CASCADE,
        lat      REAL NOT NULL,
        lon      REAL NOT NULL,
        altitude REAL
    );

    CREATE INDEX IF NOT EXISTS idx_file_meta_gps_latlon ON file_meta_gps(lat, lon);
    CREATE INDEX IF NOT EXISTS idx_file_meta_exif_year  ON file_meta_exif(year);

    INSERT OR IGNORE INTO roles (name, description)
        VALUES ('admin', 'Administrator');
    INSERT OR IGNORE INTO roles (name, description)
        VALUES ('user', 'Regular user');
"""