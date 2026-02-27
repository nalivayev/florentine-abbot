"""
Persistence layer for face detection results.

Schema:
    files   — registry of processed image files (shared with other tools via file_hash)
    faces   — one row per detected face: bbox, embedding, cluster assignment
    persons — identified people; linked to faces by the user after clustering
"""

import io
import datetime
from pathlib import Path
from typing import Optional

import numpy as np
from sqlalchemy import ForeignKey, String, LargeBinary, Float, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)


class _Base(DeclarativeBase):
    pass


class ImageFile(_Base):
    """A source image file known to the system."""

    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_path: Mapped[str] = mapped_column(String, unique=True, index=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    faces: Mapped[list["Face"]] = relationship("Face", back_populates="file")

    def __repr__(self) -> str:
        return f"<ImageFile id={self.id} path={Path(self.file_path).name!r}>"


class Person(_Base):
    """An identified person. name is NULL until the user assigns a label."""

    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now
    )

    faces: Mapped[list["Face"]] = relationship("Face", back_populates="person")

    def __repr__(self) -> str:
        return f"<Person id={self.id} name={self.name!r}>"


class Face(_Base):
    """A single face detected in an image file."""

    __tablename__ = "faces"

    id: Mapped[int] = mapped_column(primary_key=True)

    file_id: Mapped[int] = mapped_column(ForeignKey("files.id"), index=True)
    file: Mapped["ImageFile"] = relationship("ImageFile", back_populates="faces")

    bbox_x: Mapped[int]
    bbox_y: Mapped[int]
    bbox_w: Mapped[int]
    bbox_h: Mapped[int]

    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    embedding: Mapped[bytes] = mapped_column(LargeBinary)

    cluster: Mapped[Optional[int]] = mapped_column(nullable=True, index=True)

    person_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("persons.id"), nullable=True, index=True
    )
    person: Mapped[Optional["Person"]] = relationship("Person", back_populates="faces")

    created_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now
    )

    def __repr__(self) -> str:
        return (
            f"<Face id={self.id} file_id={self.file_id} "
            f"cluster={self.cluster} person_id={self.person_id}>"
        )


class FaceStore:
    """
    Persistence layer wrapping the SQLAlchemy session.

    Usage::

        with FaceStore("faces.db") as store:
            f = store.get_or_create_file("/archive/photo.tif")
            store.add_face(file=f, bbox=(x, y, w, h), embedding=vec)
    """

    def __init__(self, db_path: str | Path = "faces.db") -> None:
        self._db_path = Path(db_path)
        self._engine = create_engine(
            f"sqlite:///{self._db_path}",
            connect_args={"check_same_thread": False},
        )
        self._Session = sessionmaker(bind=self._engine)
        self._session: Session | None = None

    def open(self) -> "FaceStore":
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        _Base.metadata.create_all(self._engine)
        self._session = self._Session()
        return self

    def close(self) -> None:
        if self._session:
            self._session.commit()
            self._session.close()
            self._session = None

    def __enter__(self) -> "FaceStore":
        return self.open()

    def __exit__(self, *_) -> None:
        self.close()

    @property
    def _s(self) -> Session:
        if self._session is None:
            raise RuntimeError("FaceStore is not open")
        return self._session

    def commit(self) -> None:
        self._s.commit()

    @staticmethod
    def _embedding_to_bytes(vec: np.ndarray) -> bytes:
        buf = io.BytesIO()
        np.save(buf, vec.astype(np.float32))
        return buf.getvalue()

    @staticmethod
    def _bytes_to_embedding(data: bytes) -> np.ndarray:
        return np.load(io.BytesIO(data))

    # files

    def get_or_create_file(self, file_path: str | Path) -> ImageFile:
        """Return an existing ImageFile record or create one."""
        path = str(file_path)
        existing = self._s.query(ImageFile).filter(ImageFile.file_path == path).first()
        if existing:
            return existing
        record = ImageFile(file_path=path)
        self._s.add(record)
        self._s.flush()
        return record

    def _get_file(self, file_path: str | Path) -> ImageFile | None:
        return (
            self._s.query(ImageFile)
            .filter(ImageFile.file_path == str(file_path))
            .first()
        )

    def file_already_processed(self, file_path: str | Path) -> bool:
        """Return True if the file has at least one face record."""
        image_file = self._get_file(file_path)
        if image_file is None:
            return False
        return self._s.query(Face.id).filter(Face.file_id == image_file.id).first() is not None

    # faces

    def add_face(
        self,
        *,
        file: ImageFile,
        bbox: tuple[int, int, int, int],
        embedding: np.ndarray,
        confidence: float | None = None,
    ) -> Face:
        face = Face(
            file_id=file.id,
            bbox_x=bbox[0],
            bbox_y=bbox[1],
            bbox_w=bbox[2],
            bbox_h=bbox[3],
            confidence=confidence,
            embedding=self._embedding_to_bytes(embedding),
        )
        self._s.add(face)
        self._s.flush()
        return face

    def get_face(self, face_id: int) -> Face | None:
        return self._s.get(Face, face_id)

    def get_faces_by_file(self, file_path: str | Path) -> list[Face]:
        image_file = self._get_file(file_path)
        if image_file is None:
            return []
        return self._s.query(Face).filter(Face.file_id == image_file.id).all()

    def delete_faces_by_file(self, file_path: str | Path) -> int:
        """Delete all faces for a file. Returns count deleted."""
        image_file = self._get_file(file_path)
        if image_file is None:
            return 0
        return (
            self._s.query(Face)
            .filter(Face.file_id == image_file.id)
            .delete(synchronize_session=False)
        )

    def get_all_embeddings(self) -> list[tuple[int, np.ndarray]]:
        """Return [(face_id, embedding), ...] for all faces."""
        rows = self._s.query(Face.id, Face.embedding).all()
        return [(fid, self._bytes_to_embedding(raw)) for fid, raw in rows]

    def get_faces_without_cluster(self) -> list[Face]:
        return self._s.query(Face).filter(Face.cluster.is_(None)).all()

    def set_cluster(self, face_id: int, cluster: int | None) -> None:
        face = self._s.get(Face, face_id)
        if face:
            face.cluster = cluster

    def face_count(self) -> int:
        return self._s.query(Face).count()

    # persons

    def create_person(self, name: str | None = None, notes: str | None = None) -> Person:
        person = Person(name=name, notes=notes)
        self._s.add(person)
        self._s.flush()
        return person

    def get_person(self, person_id: int) -> Person | None:
        return self._s.get(Person, person_id)

    def get_all_persons(self) -> list[Person]:
        return self._s.query(Person).all()

    def get_or_create_person(self, name: str) -> Person:
        existing = self._s.query(Person).filter(Person.name == name).first()
        return existing if existing else self.create_person(name=name)

    def assign_person(self, face_id: int, person_id: int | None) -> None:
        face = self._s.get(Face, face_id)
        if face:
            face.person_id = person_id
