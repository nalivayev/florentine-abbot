"""
Unit tests for face_detector.store (no DeepFace dependency required).
"""

import pytest
import numpy as np
from pathlib import Path

from face_detector.store import (
    FaceStore,
    embedding_to_bytes,
    bytes_to_embedding,
)


# ── Embedding serialisation ────────────────────────────────────────────────────

def test_embedding_round_trip():
    original = np.random.randn(512).astype(np.float32)
    recovered = bytes_to_embedding(embedding_to_bytes(original))
    np.testing.assert_array_almost_equal(original, recovered)


# ── FaceStore ─────────────────────────────────────────────────────────────────

@pytest.fixture
def store(tmp_path):
    db = tmp_path / "test_faces.db"
    with FaceStore(db) as s:
        yield s


def _make_embedding(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    vec = rng.random(512).astype(np.float32)
    return vec / np.linalg.norm(vec)


def test_add_and_retrieve_face(store):
    vec = _make_embedding()
    record = store.add_face(
        file_path="/archive/2020/img.PRV.jpg",
        face_index=0,
        bbox=(10, 20, 100, 120),
        embedding=vec,
        confidence=0.97,
    )
    assert record.id is not None
    assert record.face_index == 0
    assert record.confidence == pytest.approx(0.97)

    fetched = store.get_face(record.id)
    assert fetched is not None
    assert fetched.file_path == "/archive/2020/img.PRV.jpg"
    np.testing.assert_array_almost_equal(
        bytes_to_embedding(fetched.embedding), vec
    )


def test_file_already_processed(store):
    assert not store.file_already_processed("/archive/img.jpg")

    store.add_face(
        file_path="/archive/img.jpg",
        face_index=0,
        bbox=(0, 0, 50, 50),
        embedding=_make_embedding(),
    )
    assert store.file_already_processed("/archive/img.jpg")


def test_get_faces_by_file(store):
    for i in range(3):
        store.add_face(
            file_path="/archive/group.jpg",
            face_index=i,
            bbox=(i * 10, 0, 50, 50),
            embedding=_make_embedding(i),
        )
    store.add_face(
        file_path="/archive/other.jpg",
        face_index=0,
        bbox=(0, 0, 50, 50),
        embedding=_make_embedding(99),
    )

    faces = store.get_faces_by_file("/archive/group.jpg")
    assert len(faces) == 3


def test_domain_lifecycle(store):
    domain = store.create_domain(name="Alice", notes="Test person")
    assert domain.id is not None
    assert domain.name == "Alice"

    same = store.get_or_create_domain("Alice")
    assert same.id == domain.id

    new_domain = store.get_or_create_domain("Bob")
    assert new_domain.id != domain.id
    assert new_domain.name == "Bob"


def test_update_domain_assignment(store):
    domain = store.create_domain()
    face = store.add_face(
        file_path="/img.jpg",
        face_index=0,
        bbox=(0, 0, 50, 50),
        embedding=_make_embedding(),
    )
    assert face.domain_id is None

    store.update_domain(face.id, domain.id)
    fetched = store.get_face(face.id)
    assert fetched.domain_id == domain.id


def test_get_faces_without_domain(store):
    face_a = store.add_face(
        file_path="/a.jpg", face_index=0, bbox=(0, 0, 50, 50), embedding=_make_embedding(1)
    )
    face_b = store.add_face(
        file_path="/b.jpg", face_index=0, bbox=(0, 0, 50, 50), embedding=_make_embedding(2)
    )
    domain = store.create_domain()
    store.update_domain(face_a.id, domain.id)

    unassigned = store.get_faces_without_domain()
    ids = [f.id for f in unassigned]
    assert face_b.id in ids
    assert face_a.id not in ids


def test_get_all_embeddings(store):
    for i in range(5):
        store.add_face(
            file_path=f"/img{i}.jpg", face_index=0,
            bbox=(0, 0, 50, 50), embedding=_make_embedding(i)
        )
    pairs = store.get_all_embeddings()
    assert len(pairs) == 5
    for fid, vec in pairs:
        assert isinstance(fid, int)
        assert vec.shape == (512,)
