"""Regression tests for ui.web faces routes."""

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy
import pytest

from common.database import ArchiveDatabase
from face_recognizer.store import RecognizerStore
from ui.web.routes.files.faces import list_faces
from ui.web.routes.faces import (
    AssignClusterPersonRequest,
    CreatePersonFromClusterRequest,
    assign_review_cluster_person,
    create_review_cluster_person,
    exclude_review_face,
    get_face,
    list_review_clusters,
    list_review_persons,
)
from ui.web.store import WebStore


class TestFacesRoutes:
    def test_list_faces_filters_by_file_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            database = ArchiveDatabase(archive_path)
            monkeypatch.setattr("ui.web.routes.faces_common.get_archive_path", lambda: archive_path)

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
                        region=(0.2, 0.25, 0.2, 0.3),
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
                assert payload[0]["thumb_url"] == f"/system/faces/2024/scan/face-{face.id}.webp"
            finally:
                database.close_conn()

    def test_list_faces_returns_404_for_missing_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            database = ArchiveDatabase(archive_path)
            monkeypatch.setattr("ui.web.routes.faces_common.get_archive_path", lambda: archive_path)

            try:
                database.get_conn()

                with WebStore(archive_path) as store:
                    with pytest.raises(Exception) as exc_info:
                        asyncio.run(
                            list_faces(
                                file_id=999,
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
            monkeypatch.setattr("ui.web.routes.faces_common.get_archive_path", lambda: archive_path)

            try:
                with RecognizerStore(archive_path) as store:
                    image_file = store.get_or_create_file("2024/scan.tif")
                    face = store.add_face(
                        file=image_file,
                        region=(0.25, 0.25, 0.5, 0.5),
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
                assert payload["thumb_url"] == f"/system/faces/2024/scan/face-{face.id}.webp"
            finally:
                database.close_conn()

    def test_list_review_clusters_returns_unconfirmed_only(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            database = ArchiveDatabase(archive_path)
            monkeypatch.setattr("ui.web.routes.faces_common.get_archive_path", lambda: archive_path)

            try:
                with RecognizerStore(archive_path) as store:
                    first_file = store.get_or_create_file("2024/first.tif")
                    face_a = store.add_face(
                        file=first_file,
                        region=(0.25, 0.25, 0.4, 0.4),
                        embedding=numpy.ones(512, dtype=numpy.float32),
                    )
                    face_b = store.add_face(
                        file=first_file,
                        region=(0.65, 0.25, 0.25, 0.25),
                        embedding=numpy.ones(512, dtype=numpy.float32),
                    )
                    store.set_cluster(face_a.id, 10)
                    store.set_cluster(face_b.id, 10)

                    second_file = store.get_or_create_file("2024/second.tif")
                    face_c = store.add_face(
                        file=second_file,
                        region=(0.25, 0.25, 0.4, 0.4),
                        embedding=numpy.ones(512, dtype=numpy.float32),
                    )
                    face_d = store.add_face(
                        file=second_file,
                        region=(0.65, 0.25, 0.25, 0.25),
                        embedding=numpy.ones(512, dtype=numpy.float32),
                    )
                    store.set_cluster(face_c.id, 11)
                    store.set_cluster(face_d.id, 11)
                    person = store.create_person(name="Resolved")
                    store.assign_cluster_to_person(11, person.id)

                payload = asyncio.run(
                    list_review_clusters(_user={"id": 1, "role": "admin"})
                )

                assert [cluster["id"] for cluster in payload] == [10]
                assert payload[0]["face_count"] == 2
                assert payload[0]["assigned_face_count"] == 0
                assert [face["id"] for face in payload[0]["faces"]] == [face_a.id, face_b.id]
            finally:
                database.close_conn()

    def test_list_review_persons_returns_known_people(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            database = ArchiveDatabase(archive_path)
            monkeypatch.setattr("ui.web.routes.faces_common.get_archive_path", lambda: archive_path)

            try:
                with RecognizerStore(archive_path) as store:
                    store.create_person(name="Alice", notes="first")
                    store.create_person(name="Bob")

                payload = asyncio.run(
                    list_review_persons(_user={"id": 1, "role": "admin"})
                )

                assert [person["name"] for person in payload] == ["Alice", "Bob"]
                assert payload[0]["notes"] == "first"
            finally:
                database.close_conn()

    def test_assign_review_cluster_person_updates_cluster_faces(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            database = ArchiveDatabase(archive_path)
            monkeypatch.setattr("ui.web.routes.faces_common.get_archive_path", lambda: archive_path)

            try:
                with RecognizerStore(archive_path) as store:
                    image_file = store.get_or_create_file("2024/assign.tif")
                    person = store.create_person(name="Alice")
                    face_a = store.add_face(
                        file=image_file,
                        region=(0.25, 0.25, 0.4, 0.4),
                        embedding=numpy.ones(512, dtype=numpy.float32),
                    )
                    face_b = store.add_face(
                        file=image_file,
                        region=(0.65, 0.25, 0.25, 0.25),
                        embedding=numpy.ones(512, dtype=numpy.float32),
                    )
                    store.set_cluster(face_a.id, 20)
                    store.set_cluster(face_b.id, 20)

                result = asyncio.run(
                    assign_review_cluster_person(
                        20,
                        AssignClusterPersonRequest(person_id=person.id),
                        _user={"id": 1, "role": "admin"},
                    )
                )

                assert result["updated_faces"] == 2
                with RecognizerStore(archive_path) as store:
                    assert store.get_face(face_a.id).person_id == person.id  # type: ignore[union-attr]
                    assert store.get_face(face_b.id).person_id == person.id  # type: ignore[union-attr]
            finally:
                database.close_conn()

    def test_create_review_cluster_person_creates_new_person(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            database = ArchiveDatabase(archive_path)
            monkeypatch.setattr("ui.web.routes.faces_common.get_archive_path", lambda: archive_path)

            try:
                with RecognizerStore(archive_path) as store:
                    image_file = store.get_or_create_file("2024/create.tif")
                    face_a = store.add_face(
                        file=image_file,
                        region=(0.25, 0.25, 0.4, 0.4),
                        embedding=numpy.ones(512, dtype=numpy.float32),
                    )
                    face_b = store.add_face(
                        file=image_file,
                        region=(0.65, 0.25, 0.25, 0.25),
                        embedding=numpy.ones(512, dtype=numpy.float32),
                    )
                    store.set_cluster(face_a.id, 30)
                    store.set_cluster(face_b.id, 30)

                result = asyncio.run(
                    create_review_cluster_person(
                        30,
                        CreatePersonFromClusterRequest(name="New person", notes="review"),
                        _user={"id": 1, "role": "admin"},
                    )
                )

                assert result["person"]["name"] == "New person"
                with RecognizerStore(archive_path) as store:
                    persons = store.get_all_persons()
                    assert len(persons) == 1
                    assert store.get_face(face_a.id).person_id == persons[0].id  # type: ignore[union-attr]
                    assert store.get_face(face_b.id).person_id == persons[0].id  # type: ignore[union-attr]
            finally:
                database.close_conn()

    def test_exclude_review_face_clears_cluster_and_person(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            database = ArchiveDatabase(archive_path)
            monkeypatch.setattr("ui.web.routes.faces_common.get_archive_path", lambda: archive_path)

            try:
                with RecognizerStore(archive_path) as store:
                    image_file = store.get_or_create_file("2024/exclude.tif")
                    person = store.create_person(name="Cluster person")
                    face_a = store.add_face(
                        file=image_file,
                        region=(0.25, 0.25, 0.4, 0.4),
                        embedding=numpy.ones(512, dtype=numpy.float32),
                    )
                    face_b = store.add_face(
                        file=image_file,
                        region=(0.65, 0.25, 0.25, 0.25),
                        embedding=numpy.ones(512, dtype=numpy.float32),
                    )
                    store.set_cluster(face_a.id, 40)
                    store.set_cluster(face_b.id, 40)
                    store.assign_cluster_to_person(40, person.id)

                result = asyncio.run(
                    exclude_review_face(
                        face_a.id,
                        _user={"id": 1, "role": "admin"},
                    )
                )

                assert result["excluded_face_id"] == face_a.id
                with RecognizerStore(archive_path) as store:
                    excluded = store.get_face(face_a.id)
                    kept = store.get_face(face_b.id)
                    assert excluded is not None
                    assert kept is not None
                    assert excluded.cluster is None
                    assert excluded.person_id is None
                    assert kept.cluster == 40
                    assert kept.person_id == person.id
            finally:
                database.close_conn()