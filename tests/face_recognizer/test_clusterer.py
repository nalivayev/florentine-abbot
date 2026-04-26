"""
Unit tests for RecognizerClusterer (requires scikit-learn but not DeepFace).
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import numpy

pytest.importorskip("sklearn", reason="scikit-learn required for clustering tests")

from common.logger import Logger
from face_recognizer.clusterer import RecognizerClusterer
from face_recognizer.store import RecognizerStore


class TestRecognizerClusterer:
    """Regression coverage for RecognizerClusterer without pytest fixtures."""

    def setup_method(self) -> None:
        self.logger = Logger("test_clusterer")

    @staticmethod
    def _cluster_vec(center: numpy.ndarray, noise: float, seed: int) -> numpy.ndarray:
        """Return a normalised vector near *center*."""
        rng = numpy.random.default_rng(seed)
        vec = center + rng.normal(0, noise, size=center.shape)
        return (vec / numpy.linalg.norm(vec)).astype(numpy.float32)

    @staticmethod
    def _make_center(index: int) -> numpy.ndarray:
        """Return a unit vector aligned to one axis for deterministic clustering."""
        center = numpy.zeros(512, dtype=numpy.float32)
        center[index] = 1.0
        return center

    def test_cluster_separates_two_identities(self) -> None:
        # Use explicitly orthogonal unit vectors as cluster centres so cosine
        # distance between groups is exactly 1.0 (>> eps=0.3).
        center_a = self._make_center(0)
        center_b = self._make_center(256)

        group_a = numpy.stack([self._cluster_vec(center_a, 0.01, i) for i in range(5)])
        group_b = numpy.stack([self._cluster_vec(center_b, 0.01, i + 100) for i in range(5)])
        embeddings = numpy.concatenate([group_a, group_b])

        clusterer = RecognizerClusterer(self.logger, eps=0.3, min_samples=2)
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

    def test_cluster_empty_input(self) -> None:
        clusterer = RecognizerClusterer(self.logger)
        result = clusterer.cluster(numpy.zeros((0, 512), dtype=numpy.float32))
        assert len(result) == 0

    def test_assign_domains_creates_domains(self) -> None:
        rng = numpy.random.default_rng(42)
        center = rng.random(512).astype(numpy.float32)
        center /= numpy.linalg.norm(center)

        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            with RecognizerStore(archive_path) as store:
                for i in range(4):
                    vec = self._cluster_vec(center, 0.01, i)
                    img_file = store.get_or_create_file(f"/img{i}.jpg")
                    store.add_face(
                        file=img_file,
                        bbox=(0, 0, 50, 50), image_size=(100, 100), embedding=vec,
                    )

                clusterer = RecognizerClusterer(self.logger, eps=0.3, min_samples=2)
                n_assigned = clusterer.assign_domains(store)
                assert n_assigned >= 1

                # After clustering, at most noise points remain without a cluster
                unclustered = store.get_faces_without_cluster()
                assert len(unclustered) <= 4

    def test_assign_domains_no_faces(self) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            with RecognizerStore(archive_path) as store:
                clusterer = RecognizerClusterer(self.logger)
                n = clusterer.assign_domains(store)
                assert n == 0

    def test_assign_domains_offsets_clusters_across_runs(self) -> None:
        center_a = self._make_center(0)
        center_b = self._make_center(256)

        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            with RecognizerStore(archive_path) as store:
                first_ids: list[int] = []
                for i in range(3):
                    vec = self._cluster_vec(center_a, 0.01, i)
                    img_file = store.get_or_create_file(f"/first{i}.jpg")
                    face = store.add_face(
                        file=img_file,
                        bbox=(0, 0, 50, 50),
                        image_size=(100, 100),
                        embedding=vec,
                    )
                    first_ids.append(face.id)

                clusterer = RecognizerClusterer(self.logger, eps=0.3, min_samples=2)
                clusterer.assign_domains(store)

                first_clusters = {
                    store.get_face(face_id).cluster  # type: ignore[union-attr]
                    for face_id in first_ids
                }
                assert None not in first_clusters

                second_ids: list[int] = []
                for i in range(3):
                    vec = self._cluster_vec(center_b, 0.01, i + 100)
                    img_file = store.get_or_create_file(f"/second{i}.jpg")
                    face = store.add_face(
                        file=img_file,
                        bbox=(0, 0, 50, 50),
                        image_size=(100, 100),
                        embedding=vec,
                    )
                    second_ids.append(face.id)

                clusterer.assign_domains(store)

                second_clusters = {
                    store.get_face(face_id).cluster  # type: ignore[union-attr]
                    for face_id in second_ids
                }
                assert None not in second_clusters
                assert first_clusters.isdisjoint(second_clusters)

    def test_assign_domains_reuses_existing_cluster_for_same_identity(self) -> None:
        center = self._make_center(0)

        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            with RecognizerStore(archive_path) as store:
                first_ids: list[int] = []
                for i in range(3):
                    vec = self._cluster_vec(center, 0.01, i)
                    img_file = store.get_or_create_file(f"/first{i}.jpg")
                    face = store.add_face(
                        file=img_file,
                        bbox=(0, 0, 50, 50),
                        image_size=(100, 100),
                        embedding=vec,
                    )
                    first_ids.append(face.id)

                clusterer = RecognizerClusterer(self.logger, eps=0.3, min_samples=2)
                clusterer.assign_domains(store)

                first_clusters = {
                    store.get_face(face_id).cluster  # type: ignore[union-attr]
                    for face_id in first_ids
                }
                assert len(first_clusters) == 1
                first_cluster = next(iter(first_clusters))
                assert first_cluster is not None

                second_ids: list[int] = []
                for i in range(3):
                    vec = self._cluster_vec(center, 0.01, i + 100)
                    img_file = store.get_or_create_file(f"/second{i}.jpg")
                    face = store.add_face(
                        file=img_file,
                        bbox=(0, 0, 50, 50),
                        image_size=(100, 100),
                        embedding=vec,
                    )
                    second_ids.append(face.id)

                clusterer.assign_domains(store)

                second_clusters = {
                    store.get_face(face_id).cluster  # type: ignore[union-attr]
                    for face_id in second_ids
                }
                assert second_clusters == {first_cluster}
