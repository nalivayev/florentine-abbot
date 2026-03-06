"""
Unit tests for face_detector.store (no DeepFace dependency required).
"""

from collections.abc import Generator
from pathlib import Path

import pytest
import numpy as np

from face_detector.store import FaceStore


# ── Embedding serialisation ────────────────────────────────────────────────────

def test_embedding_round_trip() -> None:
    original = np.random.randn(512).astype(np.float32)
    recovered = FaceStore._bytes_to_embedding(
        FaceStore._embedding_to_bytes(original)
    )
    np.testing.assert_array_almost_equal(original, recovered)


# ── FaceStore ─────────────────────────────────────────────────────────────────

@pytest.fixture
def store(tmp_path: Path) -> Generator[FaceStore, None, None]:
    db = tmp_path / "test_faces.db"
    with FaceStore(db) as s:
        yield s


def _make_embedding(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    vec = rng.random(512).astype(np.float32)
    return vec / np.linalg.norm(vec)


def test_add_and_retrieve_face(store: FaceStore) -> None:
    vec = _make_embedding()
    img_file = store.get_or_create_file("/archive/2020/img.PRV.jpg")
    face = store.add_face(
        file=img_file,
        bbox=(10, 20, 100, 120),
        embedding=vec,
        confidence=0.97,
    )
    assert face.id is not None
    assert face.confidence == pytest.approx(0.97)

    fetched = store.get_face(face.id)
    assert fetched is not None
    assert fetched.file.file_path == "/archive/2020/img.PRV.jpg"
    np.testing.assert_array_almost_equal(
        FaceStore._bytes_to_embedding(fetched.embedding), vec
    )


def test_file_already_processed(store: FaceStore) -> None:
    assert not store.file_already_processed("/archive/img.jpg")

    img_file = store.get_or_create_file("/archive/img.jpg")
    store.add_face(
        file=img_file,
        bbox=(0, 0, 50, 50),
        embedding=_make_embedding(),
    )
    assert store.file_already_processed("/archive/img.jpg")


def test_get_faces_by_file(store: FaceStore) -> None:
    img_file = store.get_or_create_file("/archive/group.jpg")
    for i in range(3):
        store.add_face(
            file=img_file,
            bbox=(i * 10, 0, 50, 50),
            embedding=_make_embedding(i),
        )
    other_file = store.get_or_create_file("/archive/other.jpg")
    store.add_face(
        file=other_file,
        bbox=(0, 0, 50, 50),
        embedding=_make_embedding(99),
    )

    faces = store.get_faces_by_file("/archive/group.jpg")
    assert len(faces) == 3


def test_person_lifecycle(store: FaceStore) -> None:
    person = store.create_person(name="Alice", notes="Test person")
    assert person.id is not None
    assert person.name == "Alice"

    same = store.get_or_create_person("Alice")
    assert same.id == person.id

    new_person = store.get_or_create_person("Bob")
    assert new_person.id != person.id
    assert new_person.name == "Bob"


def test_assign_person(store: FaceStore) -> None:
    person = store.create_person()
    img_file = store.get_or_create_file("/img.jpg")
    face = store.add_face(
        file=img_file,
        bbox=(0, 0, 50, 50),
        embedding=_make_embedding(),
    )
    assert face.person_id is None

    store.assign_person(face.id, person.id)
    fetched = store.get_face(face.id)
    assert fetched is not None
    assert fetched.person_id == person.id


def test_get_faces_without_cluster(store: FaceStore) -> None:
    img_a = store.get_or_create_file("/a.jpg")
    face_a = store.add_face(
        file=img_a, bbox=(0, 0, 50, 50), embedding=_make_embedding(1)
    )
    img_b = store.get_or_create_file("/b.jpg")
    face_b = store.add_face(
        file=img_b, bbox=(0, 0, 50, 50), embedding=_make_embedding(2)
    )
    store.set_cluster(face_a.id, 0)

    unclustered = store.get_faces_without_cluster()
    ids = [f.id for f in unclustered]
    assert face_b.id in ids
    assert face_a.id not in ids


def test_get_all_embeddings(store: FaceStore) -> None:
    for i in range(5):
        img_file = store.get_or_create_file(f"/img{i}.jpg")
        store.add_face(
            file=img_file, bbox=(0, 0, 50, 50), embedding=_make_embedding(i)
        )
    pairs = store.get_all_embeddings()
    assert len(pairs) == 5
    for fid, vec in pairs:
        assert isinstance(fid, int)
        assert vec.shape == (512,)
