"""
Cluster face embeddings into identity domains using DBSCAN.

DBSCAN is chosen over K-Means because:

* It does **not** require knowing the number of people in advance.
* It handles noise (faces where confidence is too low to cluster) naturally
  by labelling them ``-1``.
* Cosine distance on L2-normalised ArcFace embeddings gives excellent
  separation between identities.

Typical workflow::

    clusterer = FaceClusterer(eps=0.4, min_samples=2)
    n_new = clusterer.assign_domains(store)

After ``assign_domains``:

* Faces that belong to a cluster each have a ``cluster`` value set.
* Faces labelled as noise (label == -1) keep ``cluster = None``.
* Already-assigned faces are **not** re-clustered.
* New cluster labels are offset to avoid collisions with earlier runs.

The ``eps`` parameter controls how similar two embeddings must be to be
considered the same person.  With L2-normalised ArcFace vectors cosine
distance ≈ 0.4 is a reasonable starting point for diverse real-world photos;
lower values mean stricter matching.
"""

import io

import numpy
from sklearn.cluster import DBSCAN  # type: ignore[import-untyped]

from common.logger import Logger
from face_recognizer.store import RecognizerStore


class RecognizerClusterer:
    """
    Cluster all unassigned face embeddings and write domain assignments back.

    Parameters
    ----------
    eps:
        DBSCAN neighbourhood radius (cosine distance).  Decrease for stricter
        same-identity matching.
    min_samples:
        Minimum neighbours to form a core point.  Set to 1 to avoid noise
        points, at the cost of more singleton clusters.
    """

    def __init__(
        self,
        logger: Logger,
        *,
        eps: float = 0.4,
        min_samples: int = 2,
    ) -> None:
        self._logger = logger
        self._eps = eps
        self._min_samples = min_samples

    @staticmethod
    def _load_embedding(raw_embedding: bytes) -> numpy.ndarray:
        embedding = numpy.load(io.BytesIO(raw_embedding))
        norm = float(numpy.linalg.norm(embedding))
        if norm == 0:
            return embedding.astype(numpy.float32)
        return (embedding / norm).astype(numpy.float32)

    def _existing_cluster_centroids(
        self,
        store: RecognizerStore,
    ) -> tuple[dict[int, numpy.ndarray], dict[int, numpy.ndarray], dict[int, int]]:
        cluster_sums: dict[int, numpy.ndarray] = {}
        cluster_counts: dict[int, int] = {}

        for face in store.get_faces_with_cluster():
            assert face.cluster is not None
            embedding = self._load_embedding(face.embedding)
            if face.cluster in cluster_sums:
                cluster_sums[face.cluster] += embedding
                cluster_counts[face.cluster] += 1
            else:
                cluster_sums[face.cluster] = embedding.copy()
                cluster_counts[face.cluster] = 1

        centroids = {
            cluster_id: cluster_sum / numpy.linalg.norm(cluster_sum)
            for cluster_id, cluster_sum in cluster_sums.items()
        }
        return centroids, cluster_sums, cluster_counts

    def _match_existing_cluster(
        self,
        embedding: numpy.ndarray,
        centroids: dict[int, numpy.ndarray],
    ) -> int | None:
        best_cluster: int | None = None
        best_distance: float | None = None

        for cluster_id, centroid in centroids.items():
            distance = 1.0 - float(numpy.dot(embedding, centroid))
            if distance > self._eps:
                continue
            if best_distance is None or distance < best_distance:
                best_cluster = cluster_id
                best_distance = distance

        return best_cluster

    def cluster(self, embeddings: numpy.ndarray) -> numpy.ndarray:
        """Assign DBSCAN cluster labels. Returns array of ints; -1 means noise."""
        if len(embeddings) == 0:
            return numpy.array([], dtype=int)

        model = DBSCAN(
            eps=self._eps,
            min_samples=self._min_samples,
            metric="cosine",
            n_jobs=-1,
        )
        return model.fit_predict(embeddings)

    def assign_domains(self, store: RecognizerStore) -> int:
        """
        Cluster every face in *store* and write domain assignments back.

        Only faces without a ``domain_id`` are clustered.  Faces that are
        already assigned keep their existing domain.

        Returns
        -------
        int
            Number of faces assigned to clusters in this run.
        """
        unassigned = store.get_faces_without_cluster()
        if not unassigned:
            self._logger.info("No unassigned faces — skipping clustering")
            return 0

        self._logger.info(
            f"Clustering {len(unassigned)} unassigned face(s) (eps={self._eps:.3f}, min_samples={self._min_samples})"
        )

        centroids, cluster_sums, cluster_counts = self._existing_cluster_centroids(store)

        ids: list[int] = []
        pending_embeddings: list[numpy.ndarray] = []
        assigned_faces = 0

        for face in unassigned:
            embedding = self._load_embedding(face.embedding)
            cluster_id = self._match_existing_cluster(embedding, centroids)
            if cluster_id is None:
                ids.append(face.id)
                pending_embeddings.append(embedding)
                continue

            store.set_cluster(face.id, cluster_id)
            cluster_sums[cluster_id] += embedding
            cluster_counts[cluster_id] += 1
            centroids[cluster_id] = cluster_sums[cluster_id] / numpy.linalg.norm(cluster_sums[cluster_id])
            assigned_faces += 1

        if not pending_embeddings:
            self._logger.info(
                f"Clustering complete: {assigned_faces} face(s) assigned to existing clusters, 0 noise"
            )
            return assigned_faces

        matrix = numpy.stack(pending_embeddings)

        labels = self.cluster(matrix)
        max_cluster = store.get_max_cluster()
        cluster_offset = 0 if max_cluster is None else max_cluster + 1

        for face_id, label in zip(ids, labels):
            if label == -1:
                continue
            store.set_cluster(face_id, cluster_offset + int(label))
            assigned_faces += 1

        n_noise = int(numpy.sum(labels == -1))
        self._logger.info(
            f"Clustering complete: {assigned_faces} face(s) assigned, {n_noise} noise"
        )
        return assigned_faces
