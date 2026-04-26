"""SQLite schema fragments owned by face_recognizer."""

SCHEMA_SQL = """
    CREATE TABLE IF NOT EXISTS persons (
        id          INTEGER PRIMARY KEY,
        name        TEXT UNIQUE,
        notes       TEXT,
        created_at  TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS faces (
        id          INTEGER PRIMARY KEY,
        file_id     INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
        center_x    REAL    NOT NULL,
        center_y    REAL    NOT NULL,
        width       REAL    NOT NULL,
        height      REAL    NOT NULL,
        confidence  REAL,
        embedding   BLOB NOT NULL,
        cluster     INTEGER,
        person_id   INTEGER REFERENCES persons(id) ON DELETE SET NULL,
        created_at  TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_persons_name    ON persons(name);
    CREATE INDEX IF NOT EXISTS idx_faces_file_id   ON faces(file_id);
    CREATE INDEX IF NOT EXISTS idx_faces_cluster   ON faces(cluster);
    CREATE INDEX IF NOT EXISTS idx_faces_person_id ON faces(person_id);
"""