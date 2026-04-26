"""Regression tests for ui.web faces routes."""

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy
import pytest

from common.database import ArchiveDatabase
from face_recognizer.store import RecognizerStore
from ui.web.routes.collections.files.faces import list_faces
from ui.web.routes.faces import get_face
from ui.web.store import WebStore


class TestFacesRoutes:
    def test_list_faces_filters_by_file_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            database = ArchiveDatabase(archive_path)
            monkeypatch.setattr("ui.web.routes.collections.files.faces.get_archive_path", lambda: archive_path)

            try:
                conn = database.get_conn()
                collection_id = conn.execute(
                    "INSERT INTO collections (type, name, created_at) VALUES (?, ?, ?)",
                    ("scan", "Family album", "2024-01-01T00:00:00+00:00"),
                ).lastrowid
                assert collection_id is not None
                conn.commit()
                database.close_conn()

                with RecognizerStore(archive_path) as store:
                    image_file = store.get_or_create_file("2024/scan.tif")
                    person = store.create_person(name="Alice Example")
                    face = store.add_face(
                        file=image_file,
                        bbox=(20, 10, 40, 30),
                        image_size=(200, 100),
                        embedding=numpy.ones(512, dtype=numpy.float32),
                        confidence=0.9,
                    )
                    store.set_cluster(face.id, 7)
                    store.assign_person(face.id, person.id)

                conn = database.get_conn()
                conn.execute(
                    "UPDATE files SET collection_id = ? WHERE id = ?",
                    (int(collection_id), image_file.id),
                )
                conn.commit()

                with WebStore(archive_path) as store:
                    payload = asyncio.run(
                        list_faces(
                            collection_id=int(collection_id),
                            file_id=image_file.id,
                            _user={"id": 1, "role": "admin"},
                            store=store,
                        )
                    )

                assert len(payload) == 1
                assert payload[0]["id"] == face.id
                assert abs(payload[0]["region"]["center_x"] - 0.2) < 1e-9
                assert abs(payload[0]["region"]["center_y"] - 0.25) < 1e-9
                assert abs(payload[0]["region"]["width"] - 0.2) < 1e-9
                assert abs(payload[0]["region"]["height"] - 0.3) < 1e-9
                assert payload[0]["cluster"] == 7
                assert payload[0]["person"] is not None
                assert payload[0]["person"]["name"] == "Alice Example"
            finally:
                database.close_conn()

    def test_list_faces_rejects_file_from_other_collection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            database = ArchiveDatabase(archive_path)
            monkeypatch.setattr("ui.web.routes.collections.files.faces.get_archive_path", lambda: archive_path)

            try:
                conn = database.get_conn()
                collection_id = conn.execute(
                    "INSERT INTO collections (type, name, created_at) VALUES (?, ?, ?)",
                    ("scan", "Family album", "2024-01-01T00:00:00+00:00"),
                ).lastrowid
                other_collection_id = conn.execute(
                    "INSERT INTO collections (type, name, created_at) VALUES (?, ?, ?)",
                    ("scan", "Other album", "2024-01-01T00:00:00+00:00"),
                ).lastrowid
                assert collection_id is not None
                assert other_collection_id is not None
                file_id = conn.execute(
                    "INSERT INTO files (collection_id, path, status, imported_at) VALUES (?, ?, ?, ?)",
                    (int(collection_id), "2024/scan.tif", "active", "2024-01-01T00:00:00+00:00"),
                ).lastrowid
                assert file_id is not None
                conn.commit()

                with WebStore(archive_path) as store:
                    with pytest.raises(Exception) as exc_info:
                        asyncio.run(
                            list_faces(
                                collection_id=int(other_collection_id),
                                file_id=int(file_id),
                                _user={"id": 1, "role": "admin"},
                                store=store,
                            )
                        )

                assert getattr(exc_info.value, "status_code", None) == 404
            finally:
                database.close_conn()

    def test_get_face_returns_one_face(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            database = ArchiveDatabase(archive_path)
            monkeypatch.setattr("ui.web.routes.faces.get_archive_path", lambda: archive_path)

            try:
                with RecognizerStore(archive_path) as store:
                    image_file = store.get_or_create_file("2024/scan.tif")
                    face = store.add_face(
                        file=image_file,
                        bbox=(0, 0, 50, 50),
                        image_size=(100, 100),
                        embedding=numpy.zeros(512, dtype=numpy.float32),
                    )

                payload = asyncio.run(
                    get_face(
                        face.id,
                        _user={"id": 1, "role": "admin"},
                    )
                )

                assert payload["id"] == face.id
                assert payload["file_id"] == image_file.id
                assert abs(payload["region"]["center_x"] - 0.25) < 1e-9
                assert abs(payload["region"]["center_y"] - 0.25) < 1e-9
                assert abs(payload["region"]["width"] - 0.5) < 1e-9
                assert abs(payload["region"]["height"] - 0.5) < 1e-9
            finally:
                database.close_conn()