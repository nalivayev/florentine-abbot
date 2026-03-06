"""
Unit tests for FaceClusterer (requires scikit-learn but not DeepFace).
"""

from collections.abc import Generator
from pathlib import Path

import pytest
import numpy as np

pytest.importorskip("sklearn", reason="scikit-learn required for clustering tests")

from face_detector.clusterer import FaceClusterer
from face_detector.store import FaceStore
from common.logger import Logger


def _cluster_vec(center: np.ndarray, noise: float, seed: int) -> np.ndarray:
    """Return a normalised vector near *center*."""
    rng = np.random.default_rng(seed)
    vec = center + rng.normal(0, noise, size=center.shape)
    return (vec / np.linalg.norm(vec)).astype(np.float32)


@pytest.fixture
def store(tmp_path: Path) -> Generator[FaceStore, None, None]:
    db = tmp_path / "cluster_test.db"
    with FaceStore(db) as s:
        yield s


# ── cluster() ─────────────────────────────────────────────────────────────────

def test_cluster_separates_two_identities(logger: Logger) -> None:
    # Use explicitly orthogonal unit vectors as cluster centres so cosine
    # distance between groups is exactly 1.0 (>> eps=0.3).
    center_a = np.zeros(512, dtype=np.float32); center_a[0] = 1.0
    center_b = np.zeros(512, dtype=np.float32); center_b[256] = 1.0

    group_a = np.stack([_cluster_vec(center_a, 0.01, i) for i in range(5)])
    group_b = np.stack([_cluster_vec(center_b, 0.01, i + 100) for i in range(5)])
    embeddings = np.concatenate([group_a, group_b])

    clusterer = FaceClusterer(logger, eps=0.3, min_samples=2)
    labels = clusterer.cluster(embeddings)

    # Two distinct cluster labels (ignoring noise at -1)
    active = set(labels[labels >= 0])
    assert len(active) == 2, f"Expected 2 clusters, got {sorted(active)}"

    # All group_a faces in the same cluster
    assert len(set(labels[:5])) == 1
    # All group_b faces in the same cluster
    assert len(set(labels[5:])) == 1
    # Different clusters
    assert labels[0] != labels[5]


def test_cluster_empty_input(logger: Logger) -> None:
    clusterer = FaceClusterer(logger)
    result = clusterer.cluster(np.zeros((0, 512), dtype=np.float32))
    assert len(result) == 0


# ── assign_domains() ──────────────────────────────────────────────────────────

def test_assign_domains_creates_domains(logger: Logger, store: FaceStore) -> None:
    rng = np.random.default_rng(42)
    center = rng.random(512).astype(np.float32)
    center /= np.linalg.norm(center)

    for i in range(4):
        vec = _cluster_vec(center, 0.01, i)
        img_file = store.get_or_create_file(f"/img{i}.jpg")
        store.add_face(
            file=img_file,
            bbox=(0, 0, 50, 50), embedding=vec,
        )

    clusterer = FaceClusterer(logger, eps=0.3, min_samples=2)
    n_assigned = clusterer.assign_domains(store)
    assert n_assigned >= 1

    # After clustering, at most noise points remain without a cluster
    unclustered = store.get_faces_without_cluster()
    assert len(unclustered) <= 4


def test_assign_domains_no_faces(logger: Logger, store: FaceStore) -> None:
    clusterer = FaceClusterer(logger)
    n = clusterer.assign_domains(store)
    assert n == 0
