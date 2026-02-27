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

* Faces that belong to a cluster each have a ``domain_id`` set.
* Faces labelled as noise (label == -1) keep ``domain_id = None``.
* Anonymous ``Domain`` rows are created automatically (``name=None``).
* Already-assigned faces are **not** re-clustered (incremental-safe).

The ``eps`` parameter controls how similar two embeddings must be to be
considered the same person.  With L2-normalised ArcFace vectors cosine
distance ≈ 0.4 is a reasonable starting point for diverse real-world photos;
lower values mean stricter matching.
"""

import io

import numpy as np
from sklearn.cluster import DBSCAN  # type: ignore[import-untyped]

from common.logger import Logger
from face_detector.store import FaceStore


class FaceClusterer:
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

    def cluster(self, embeddings: np.ndarray) -> np.ndarray:
        """Assign DBSCAN cluster labels. Returns array of ints; -1 means noise."""
        if len(embeddings) == 0:
            return np.array([], dtype=int)

        model = DBSCAN(
            eps=self._eps,
            min_samples=self._min_samples,
            metric="cosine",
            n_jobs=-1,
        )
        return model.fit_predict(embeddings)

    def assign_domains(self, store: FaceStore) -> int:
        """
        Cluster every face in *store* and write domain assignments back.

        Only faces without a ``domain_id`` are clustered.  Faces that are
        already assigned keep their existing domain.

        Returns
        -------
        int
            Number of new ``Domain`` rows created.
        """
        unassigned = store.get_faces_without_cluster()
        if not unassigned:
            self._logger.info("No unassigned faces — skipping clustering")
            return 0

        self._logger.info(
            f"Clustering {len(unassigned)} unassigned face(s) (eps={self._eps:.3f}, min_samples={self._min_samples})"
        )

        ids = [f.id for f in unassigned]
        matrix = np.stack([np.load(io.BytesIO(f.embedding)) for f in unassigned])

        labels = self.cluster(matrix)

        new_clusters = 0
        for face_id, label in zip(ids, labels):
            if label == -1:
                continue
            store.set_cluster(face_id, int(label))
            new_clusters += 1

        store.commit()

        n_noise = int(np.sum(labels == -1))
        self._logger.info(
            f"Clustering complete: {new_clusters} face(s) assigned, {n_noise} noise"
        )
        return new_clusters
