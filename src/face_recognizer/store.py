"""Persistence layer for face detection results in the shared archive database."""

from dataclasses import dataclass
from datetime import datetime, timezone
import io
from pathlib import Path
import sqlite3

import numpy

from common.database import ArchiveDatabase
from common.database import FILE_STATUS_ACTIVE, FILE_STATUS_MODIFIED, FILE_STATUS_NEW
from common.database import TASK_STATUS_DONE, TASK_STATUS_FAILED, TASK_STATUS_PENDING, TASK_STATUS_RUNNING, TASK_STATUS_SKIPPED
from face_recognizer.constants import DAEMON_NAME
from face_recognizer.schema import SCHEMA_SQL


@dataclass(slots=True)
class RecognizerTaskRecord:
    """Minimal task candidate state needed by face-recognizer orchestration."""

    file_id: int
    rel_path: str
    status: str


@dataclass(slots=True)
class ImageFile:
    """A source image file registered in the shared archive database."""

    id: int
    file_path: str
    status: str
    checksum: str | None
    imported_at: str


@dataclass(slots=True)
class Person:
    """An identified person. name is NULL until the user assigns a label."""

    id: int
    name: str | None
    notes: str | None
    created_at: str


@dataclass(slots=True)
class FaceClusterSummary:
    """Cluster-level review state derived from its member faces."""

    cluster_id: int
    face_count: int
    assigned_face_count: int
    distinct_person_count: int
    created_at: str


@dataclass(slots=True)
class Face:
    """A single face detected in an image file."""

    id: int
    file_id: int
    center_x: float
    center_y: float
    width: float
    height: float
    confidence: float | None
    embedding: bytes
    cluster: int | None
    person_id: int | None
    created_at: str
    file: ImageFile
    person: Person | None = None

    @property
    def region(self) -> tuple[float, float, float, float]:
        """Return the normalized center-based region tuple."""
        return (self.center_x, self.center_y, self.width, self.height)


class RecognizerStore:
    """
    Persistence layer wrapping the shared sqlite archive database.

    Usage::

        with RecognizerStore("/archive") as store:
            f = store.get_or_create_file("/archive/photo.tif")
            store.add_face(file=f, region=(cx, cy, w, h), embedding=vec)
    """

    _FACE_SELECT = """
        SELECT
            faces.id AS face_id,
            faces.file_id AS face_file_id,
            faces.center_x AS face_center_x,
            faces.center_y AS face_center_y,
            faces.width AS face_width,
            faces.height AS face_height,
            faces.confidence AS face_confidence,
            faces.embedding AS face_embedding,
            faces.cluster AS face_cluster,
            faces.person_id AS face_person_id,
            faces.created_at AS face_created_at,
            files.id AS image_file_id,
            files.path AS image_file_path,
            files.status AS image_file_status,
            files.checksum AS image_file_checksum,
            files.imported_at AS image_file_imported_at,
            persons.id AS person_row_id,
            persons.name AS person_name,
            persons.notes AS person_notes,
            persons.created_at AS person_created_at
        FROM faces
        JOIN files ON files.id = faces.file_id
        LEFT JOIN persons ON persons.id = faces.person_id
    """

    def __init__(
        self,
        archive_path: str | Path,
    ) -> None:
        self._archive_path = Path(archive_path)
        self._database = ArchiveDatabase(self._archive_path)
        self._conn: sqlite3.Connection | None = None

    def _open(self) -> "RecognizerStore":
        if self._conn is not None:
            return self
        self._conn = self._database.get_conn()
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()
        return self

    def _close(self) -> None:
        if self._conn is None:
            return
        self._conn.commit()
        self._conn = None
        self._database.close_conn()

    def __enter__(self) -> "RecognizerStore":
        return self._open()

    def __exit__(self, *_) -> None:
        self._close()

    @property
    def _c(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("RecognizerStore is not open")
        return self._conn

    def _commit(self) -> None:
        self._c.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _embedding_to_bytes(vec: numpy.ndarray) -> bytes:
        buf = io.BytesIO()
        numpy.save(buf, vec.astype(numpy.float32))
        return buf.getvalue()

    @staticmethod
    def _bytes_to_embedding(data: bytes) -> numpy.ndarray:
        return numpy.load(io.BytesIO(data))

    @staticmethod
    def _validate_region(region: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
        center_x, center_y, width, height = [float(value) for value in region]
        if not (0.0 <= center_x <= 1.0):
            raise ValueError(f"Invalid face center_x: {center_x}")
        if not (0.0 <= center_y <= 1.0):
            raise ValueError(f"Invalid face center_y: {center_y}")
        if not (0.0 <= width <= 1.0):
            raise ValueError(f"Invalid face width: {width}")
        if not (0.0 <= height <= 1.0):
            raise ValueError(f"Invalid face height: {height}")
        return (center_x, center_y, width, height)

    def _normalize_file_path(self, file_path: str | Path) -> str:
        path = Path(file_path)
        if path.is_absolute():
            try:
                return str(path.relative_to(self._archive_path))
            except ValueError:
                return str(path)
        return str(path)

    @staticmethod
    def _file_from_row(row: sqlite3.Row) -> ImageFile:
        return ImageFile(
            id=int(row["id"]),
            file_path=str(row["path"]),
            status=str(row["status"]),
            checksum=row["checksum"],
            imported_at=str(row["imported_at"]),
        )

    @staticmethod
    def _person_from_row(row: sqlite3.Row) -> Person:
        return Person(
            id=int(row["id"]),
            name=row["name"],
            notes=row["notes"],
            created_at=str(row["created_at"]),
        )

    @staticmethod
    def _cluster_summary_from_row(row: sqlite3.Row) -> FaceClusterSummary:
        return FaceClusterSummary(
            cluster_id=int(row["cluster_id"]),
            face_count=int(row["face_count"]),
            assigned_face_count=int(row["assigned_face_count"]),
            distinct_person_count=int(row["distinct_person_count"]),
            created_at=str(row["created_at"]),
        )

    @classmethod
    def _face_from_row(cls, row: sqlite3.Row) -> Face:
        person: Person | None = None
        if row["person_row_id"] is not None:
            person = Person(
                id=int(row["person_row_id"]),
                name=row["person_name"],
                notes=row["person_notes"],
                created_at=str(row["person_created_at"]),
            )

        image_file = ImageFile(
            id=int(row["image_file_id"]),
            file_path=str(row["image_file_path"]),
            status=str(row["image_file_status"]),
            checksum=row["image_file_checksum"],
            imported_at=str(row["image_file_imported_at"]),
        )

        return Face(
            id=int(row["face_id"]),
            file_id=int(row["face_file_id"]),
            center_x=float(row["face_center_x"]),
            center_y=float(row["face_center_y"]),
            width=float(row["face_width"]),
            height=float(row["face_height"]),
            confidence=(
                float(row["face_confidence"])
                if row["face_confidence"] is not None
                else None
            ),
            embedding=bytes(row["face_embedding"]),
            cluster=(
                int(row["face_cluster"])
                if row["face_cluster"] is not None
                else None
            ),
            person_id=(
                int(row["face_person_id"])
                if row["face_person_id"] is not None
                else None
            ),
            created_at=str(row["face_created_at"]),
            file=image_file,
            person=person,
        )

    # files

    def list_pending_files(self) -> list[RecognizerTaskRecord]:
        """Return this daemon's pending tasks for new/modified files."""
        rows = self._c.execute(
            """
            SELECT f.id, f.path, f.status
            FROM daemon_tasks t
            JOIN files f ON f.id = t.file_id
            WHERE t.daemon = ?
              AND t.status = ?
              AND f.status IN (?, ?)
            """,
            (DAEMON_NAME, TASK_STATUS_PENDING, FILE_STATUS_NEW, FILE_STATUS_MODIFIED),
        ).fetchall()
        return [
            RecognizerTaskRecord(
                file_id=int(row["id"]),
                rel_path=str(row["path"]),
                status=str(row["status"]),
            )
            for row in rows
        ]

    def start_task(self, file_id: int, updated_at: str) -> None:
        """Create or reset the face-recognizer task to running."""
        self._c.execute(
            "INSERT OR IGNORE INTO daemon_tasks (file_id, daemon, status, updated_at) VALUES (?, ?, ?, ?)",
            (file_id, DAEMON_NAME, TASK_STATUS_RUNNING, updated_at),
        )
        self._c.execute(
            "UPDATE daemon_tasks SET status = ?, error = NULL, updated_at = ? WHERE file_id = ? AND daemon = ?",
            (TASK_STATUS_RUNNING, updated_at, file_id, DAEMON_NAME),
        )
        self._commit()

    def mark_done(self, file_id: int, updated_at: str) -> None:
        """Mark a face-recognizer task as done."""
        self._c.execute(
            "UPDATE daemon_tasks SET status = ?, error = NULL, updated_at = ? WHERE file_id = ? AND daemon = ?",
            (TASK_STATUS_DONE, updated_at, file_id, DAEMON_NAME),
        )
        self._commit()

    def mark_skipped(self, file_id: int, updated_at: str) -> None:
        """Mark a face-recognizer task as skipped."""
        self._c.execute(
            "UPDATE daemon_tasks SET status = ?, error = NULL, updated_at = ? WHERE file_id = ? AND daemon = ?",
            (TASK_STATUS_SKIPPED, updated_at, file_id, DAEMON_NAME),
        )
        self._commit()

    def mark_failed(self, file_id: int, error: str, updated_at: str) -> None:
        """Mark a face-recognizer task as failed with an error message."""
        self._c.execute(
            "UPDATE daemon_tasks SET status = ?, error = ?, updated_at = ? WHERE file_id = ? AND daemon = ?",
            (TASK_STATUS_FAILED, error, updated_at, file_id, DAEMON_NAME),
        )
        self._commit()

    def get_or_create_file(self, file_path: str | Path) -> ImageFile:
        """Return an existing ImageFile record or create one."""
        normalized_path = self._normalize_file_path(file_path)
        existing = self._get_file(file_path)
        if existing:
            return existing

        imported_at = self._now()
        cursor = self._c.execute(
            "INSERT INTO files (path, status, imported_at) VALUES (?, ?, ?)",
            (normalized_path, FILE_STATUS_ACTIVE, imported_at),
        )
        assert cursor.lastrowid is not None
        self._commit()
        return ImageFile(
            id=int(cursor.lastrowid),
            file_path=normalized_path,
            status=FILE_STATUS_ACTIVE,
            checksum=None,
            imported_at=imported_at,
        )

    def _get_file(self, file_path: str | Path) -> ImageFile | None:
        normalized_path = self._normalize_file_path(file_path)
        row = self._c.execute(
            "SELECT id, path, status, checksum, imported_at FROM files WHERE path = ?",
            (normalized_path,),
        ).fetchone()
        return None if row is None else self._file_from_row(row)

    def file_already_processed(self, file_path: str | Path) -> bool:
        """Return True if the file has at least one face record."""
        image_file = self._get_file(file_path)
        if image_file is None:
            return False
        row = self._c.execute(
            "SELECT 1 FROM faces WHERE file_id = ? LIMIT 1",
            (image_file.id,),
        ).fetchone()
        return row is not None

    # faces

    def add_face(
        self,
        *,
        file: ImageFile,
        region: tuple[float, float, float, float],
        embedding: numpy.ndarray,
        confidence: float | None = None,
    ) -> Face:
        raw_embedding = self._embedding_to_bytes(embedding)
        center_x, center_y, width, height = self._validate_region(region)
        created_at = self._now()
        cursor = self._c.execute(
            """
            INSERT INTO faces (
                file_id,
                center_x,
                center_y,
                width,
                height,
                confidence,
                embedding,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                file.id,
                center_x,
                center_y,
                width,
                height,
                confidence,
                raw_embedding,
                created_at,
            ),
        )
        assert cursor.lastrowid is not None
        self._commit()
        return Face(
            id=int(cursor.lastrowid),
            file_id=file.id,
            center_x=center_x,
            center_y=center_y,
            width=width,
            height=height,
            confidence=confidence,
            embedding=raw_embedding,
            cluster=None,
            person_id=None,
            created_at=created_at,
            file=file,
            person=None,
        )

    def get_face(self, face_id: int) -> Face | None:
        row = self._c.execute(
            self._FACE_SELECT + " WHERE faces.id = ?",
            (face_id,),
        ).fetchone()
        return None if row is None else self._face_from_row(row)

    def get_faces_by_file(self, file_path: str | Path) -> list[Face]:
        normalized_path = self._normalize_file_path(file_path)
        rows = self._c.execute(
            self._FACE_SELECT + " WHERE files.path = ? ORDER BY faces.id",
            (normalized_path,),
        ).fetchall()
        return [self._face_from_row(row) for row in rows]

    def get_faces_by_file_id(self, file_id: int) -> list[Face]:
        rows = self._c.execute(
            self._FACE_SELECT + " WHERE faces.file_id = ? ORDER BY faces.id",
            (file_id,),
        ).fetchall()
        return [self._face_from_row(row) for row in rows]

    def delete_faces_by_file(self, file_path: str | Path) -> int:
        """Delete all faces for a file. Returns count deleted."""
        image_file = self._get_file(file_path)
        if image_file is None:
            return 0
        cursor = self._c.execute(
            "DELETE FROM faces WHERE file_id = ?",
            (image_file.id,),
        )
        self._commit()
        return int(cursor.rowcount)

    def get_all_embeddings(self) -> list[tuple[int, numpy.ndarray]]:
        """Return [(face_id, embedding), ...] for all faces."""
        rows = self._c.execute("SELECT id, embedding FROM faces ORDER BY id").fetchall()
        return [
            (int(row["id"]), self._bytes_to_embedding(row["embedding"]))
            for row in rows
        ]

    def get_faces_without_cluster(self) -> list[Face]:
        rows = self._c.execute(
            self._FACE_SELECT + " WHERE faces.cluster IS NULL ORDER BY faces.id"
        ).fetchall()
        return [self._face_from_row(row) for row in rows]

    def get_faces_with_cluster(self) -> list[Face]:
        rows = self._c.execute(
            self._FACE_SELECT + " WHERE faces.cluster IS NOT NULL ORDER BY faces.cluster, faces.id"
        ).fetchall()
        return [self._face_from_row(row) for row in rows]

    def list_unconfirmed_clusters(self) -> list[FaceClusterSummary]:
        """Return clusters that are not fully resolved to one assigned person."""
        rows = self._c.execute(
            """
            SELECT
                faces.cluster AS cluster_id,
                COUNT(*) AS face_count,
                COUNT(faces.person_id) AS assigned_face_count,
                COUNT(DISTINCT faces.person_id) AS distinct_person_count,
                MIN(faces.created_at) AS created_at
            FROM faces
            WHERE faces.cluster IS NOT NULL
            GROUP BY faces.cluster
            HAVING NOT (
                COUNT(*) = COUNT(faces.person_id)
                AND COUNT(DISTINCT faces.person_id) = 1
            )
            ORDER BY MIN(faces.created_at), faces.cluster
            """
        ).fetchall()
        return [self._cluster_summary_from_row(row) for row in rows]

    def get_faces_by_cluster(self, cluster: int) -> list[Face]:
        rows = self._c.execute(
            self._FACE_SELECT + " WHERE faces.cluster = ? ORDER BY faces.id",
            (cluster,),
        ).fetchall()
        return [self._face_from_row(row) for row in rows]

    def set_cluster(self, face_id: int, cluster: int | None) -> None:
        self._c.execute(
            "UPDATE faces SET cluster = ? WHERE id = ?",
            (cluster, face_id),
        )
        self._commit()

    def get_max_cluster(self) -> int | None:
        """Return the highest assigned cluster id, if any."""
        row = self._c.execute("SELECT MAX(cluster) AS max_cluster FROM faces").fetchone()
        if row is None or row["max_cluster"] is None:
            return None
        return int(row["max_cluster"])

    def face_count(self) -> int:
        row = self._c.execute("SELECT COUNT(*) AS count FROM faces").fetchone()
        assert row is not None
        return int(row["count"])

    # persons

    def create_person(self, name: str | None = None, notes: str | None = None) -> Person:
        created_at = self._now()
        cursor = self._c.execute(
            "INSERT INTO persons (name, notes, created_at) VALUES (?, ?, ?)",
            (name, notes, created_at),
        )
        assert cursor.lastrowid is not None
        self._commit()
        return Person(
            id=int(cursor.lastrowid),
            name=name,
            notes=notes,
            created_at=created_at,
        )

    def get_person(self, person_id: int) -> Person | None:
        row = self._c.execute(
            "SELECT id, name, notes, created_at FROM persons WHERE id = ?",
            (person_id,),
        ).fetchone()
        return None if row is None else self._person_from_row(row)

    def get_all_persons(self) -> list[Person]:
        rows = self._c.execute(
            "SELECT id, name, notes, created_at FROM persons ORDER BY id"
        ).fetchall()
        return [self._person_from_row(row) for row in rows]

    def get_or_create_person(self, name: str) -> Person:
        row = self._c.execute(
            "SELECT id, name, notes, created_at FROM persons WHERE name = ?",
            (name,),
        ).fetchone()
        if row is not None:
            return self._person_from_row(row)
        return self.create_person(name=name)

    def assign_cluster_to_person(self, cluster: int, person_id: int | None) -> int:
        if person_id is not None and self.get_person(person_id) is None:
            raise ValueError(f"Person does not exist: {person_id}")

        cursor = self._c.execute(
            "UPDATE faces SET person_id = ? WHERE cluster = ?",
            (person_id, cluster),
        )
        if cursor.rowcount <= 0:
            raise ValueError(f"Cluster does not exist: {cluster}")
        self._commit()
        return int(cursor.rowcount)

    def create_person_from_cluster(
        self,
        cluster: int,
        *,
        name: str | None = None,
        notes: str | None = None,
    ) -> Person:
        if not self.get_faces_by_cluster(cluster):
            raise ValueError(f"Cluster does not exist: {cluster}")

        person = self.create_person(name=name, notes=notes)
        self.assign_cluster_to_person(cluster, person.id)
        return person

    def assign_person(self, face_id: int, person_id: int | None) -> None:
        self._c.execute(
            "UPDATE faces SET person_id = ? WHERE id = ?",
            (person_id, face_id),
        )
        self._commit()

    def exclude_face_from_cluster(self, face_id: int) -> None:
        cursor = self._c.execute(
            "UPDATE faces SET cluster = NULL, person_id = NULL WHERE id = ?",
            (face_id,),
        )
        if cursor.rowcount <= 0:
            raise ValueError(f"Face does not exist: {face_id}")
        self._commit()
