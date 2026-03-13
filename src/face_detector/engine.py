"""
Batch face detection engine.

Orchestrates scanning a directory tree, running the detector on eligible
files, persisting results and optionally re-clustering all stored faces.

Usage (callable interface, consistent with other workflow classes)::

    engine = FaceDetectorEngine(logger)
    total = engine(
        path=Path("/archive/photos"),
        db_path=Path("faces.db"),
        overwrite=False,
        cluster=True,
    )
"""

from pathlib import Path

from common.logger import Logger
from face_detector.config import Config
from face_detector.clusterer import FaceClusterer
from face_detector.detector import FaceDetector
from face_detector.detectors import get_detector
from face_detector.store import FaceStore


class FaceDetectorEngine:
    """
    Callable batch engine.

    Parameters set at construction time; per-run parameters passed to
    ``__call__``.  Follows the same pattern as :class:`PreviewMaker`.
    """

    def __init__(
        self,
        logger: Logger,
        config_path: str | Path | None = None,
        detector: str | None = None,
    ) -> None:
        self._logger = logger
        self._config = Config(logger, config_path)
        detector_name = detector or self._config.detector
        detector_cls = get_detector(detector_name)
        self._detector: FaceDetector = detector_cls(logger)

    def __call__(
        self,
        *,
        path: Path,
        db_path: Path | None = None,
        overwrite: bool = False,
        cluster: bool = True,
    ) -> int:
        """
        Scan *path* recursively, detect faces, persist results and optionally
        cluster embeddings into identity domains.

        Parameters
        ----------
        path:
            Root directory to scan for image files.
        db_path:
            Path to the SQLite database file.  Defaults to the value in the
            config (``~/.config/florentine-abbot/face-detector/faces.db``).
        overwrite:
            If True, re-process files that already have face records.
        cluster:
            If True, run DBSCAN clustering after detection.

        Returns
        -------
        int
            Total number of faces detected and stored in this run.
        """
        resolved_db = db_path or self._config.default_db_path
        self._logger.info(f"Using database: {resolved_db}")

        with FaceStore(resolved_db) as store:
            total_faces = self._scan_path(path, store, overwrite=overwrite)

            if cluster and total_faces > 0:
                clusterer = FaceClusterer(
                    self._logger,
                    eps=self._config.clustering_eps,
                    min_samples=self._config.clustering_min_samples,
                )
                clusterer.assign_domains(store)
            elif cluster:
                self._logger.info("No new faces detected — skipping clustering")

        return total_faces

    def process_single_file(
        self,
        file_path: Path,
        store: FaceStore,
        *,
        overwrite: bool = False,
    ) -> int:
        """
        Detect and store faces for a single *file_path*.

        Parameters
        ----------
        file_path:
            Path to the image file.
        store:
            Open :class:`FaceStore` instance.
        overwrite:
            If True, delete existing records before re-processing.

        Returns
        -------
        int
            Number of faces stored.
        """
        if not overwrite and store.file_already_processed(file_path):
            self._logger.debug(f"Skipping already-processed file: {file_path}")
            return 0

        if overwrite and store.file_already_processed(file_path):
            deleted = store.delete_faces_by_file(file_path)
            self._logger.debug(f"Overwrite: removed {deleted} existing record(s) for {file_path.name}")

        faces = self._detector.detect(file_path)
        if not faces:
            return 0

        img_file = store.get_or_create_file(file_path)
        for face in faces:
            store.add_face(
                file=img_file,
                bbox=face.bbox,
                embedding=face.embedding,
                confidence=face.confidence,
            )

        store.commit()
        self._logger.debug(f"Stored {len(faces)} face(s) from {file_path.name}")
        return len(faces)

    def _is_eligible(self, file_path: Path) -> bool:
        """Return True if *file_path* passes the engine-level filters."""
        if file_path.is_symlink():
            self._logger.debug(f"Skipping {file_path}: is symlink")
            return False

        if file_path.suffix.lower() not in self._config.source_extensions:
            self._logger.debug(
                f"Skipping {file_path}: extension {file_path.suffix!r} not in source_extensions"
            )
            return False

        import fnmatch
        patterns = self._config.source_priority
        if patterns and not any(fnmatch.fnmatch(file_path.name, p) for p in patterns):
            self._logger.debug(
                f"Skipping {file_path}: does not match any source_priority pattern"
            )
            return False

        return True

    def _scan_path(
        self,
        path: Path,
        store: FaceStore,
        *,
        overwrite: bool,
    ) -> int:
        """Walk *path* recursively and process all eligible image files."""
        if not path.exists():
            self._logger.error(f"Path does not exist: {path}")
            return 0

        total = 0
        for file_path in sorted(path.rglob("*")):
            if not file_path.is_file():
                continue
            if not self._is_eligible(file_path):
                continue

            count = self.process_single_file(file_path, store, overwrite=overwrite)
            total += count

        self._logger.info(f"Scan complete: {total} face(s) detected under {path}")
        return total
