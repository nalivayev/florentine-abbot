"""High-level batch and database-backed orchestration for Face Recognizer."""

import datetime
from pathlib import Path
import shutil

from common.constants import ARCHIVE_SYSTEM_DIR
from common.database import FILE_STATUS_MODIFIED
from common.logger import Logger
from face_recognizer.classes import RecognizerSettings
from face_recognizer.clusterer import RecognizerClusterer
from face_recognizer.constants import FACES_DIR
from face_recognizer.processor import RecognizerProcessor
from face_recognizer.store import RecognizerStore


class Recognizer:
    """Face detection orchestration layer for batch and daemon modes."""

    def __init__(
        self,
        logger: Logger,
        settings: RecognizerSettings | None = None,
        processor: RecognizerProcessor | None = None,
    ) -> None:
        self._logger = logger
        self._settings = settings or RecognizerSettings.from_data()
        self._processor = processor or RecognizerProcessor(
            logger,
            detector_name=self._settings.detector,
        )

    def execute(
        self,
        *,
        path: Path,
        overwrite: bool = False,
        cluster: bool = True,
    ) -> int:
        """Run one batch face-detection pass under *path*."""
        if not path.exists():
            raise ValueError(f"Path does not exist: {path}")

        with RecognizerStore(path) as store:
            total_faces = self._scan_path(path, store, overwrite=overwrite)

            self._cluster_if_needed(store, total_faces=total_faces, cluster=cluster)

        return total_faces

    def poll(self, archive_path: Path, *, cluster: bool = True) -> int:
        """Process DB-backed face-detection tasks for files pending in the archive."""
        if not archive_path.exists():
            raise ValueError(f"Archive path does not exist: {archive_path}")

        with RecognizerStore(archive_path) as store:
            rows = store.list_pending_files()

            if not rows:
                return 0

            self._logger.info(f"Found {len(rows)} file(s) to process")

            total_faces = 0
            for row in rows:
                total_faces += self._process_pending_file(
                    store,
                    file_id=row.file_id,
                    rel_path=row.rel_path,
                    file_status=row.status,
                    archive_path=archive_path,
                )

            self._cluster_if_needed(store, total_faces=total_faces, cluster=cluster)
            return total_faces

    def _process_single_file(
        self,
        file_path: Path,
        store: RecognizerStore,
        *,
        archive_path: Path,
        overwrite: bool = False,
    ) -> int:
        """Detect and store faces for a single *file_path*."""
        if not overwrite and store.file_already_processed(file_path):
            self._logger.debug(f"Skipping already-processed file: {file_path}")
            return 0

        if overwrite and store.file_already_processed(file_path):
            deleted = store.delete_faces_by_file(file_path)
            self._delete_face_thumb_dir(file_path, archive_path=archive_path)
            self._logger.debug(f"Overwrite: removed {deleted} existing record(s) for {file_path.name}")

        faces = self._processor.process_for_storage(file_path)
        if not faces:
            return 0

        img_file = store.get_or_create_file(file_path)
        for face in faces:
            if face.thumb_webp is None:
                raise ValueError(
                    f"Processor returned face without thumbnail bytes: {file_path}"
                )
            stored_face = store.add_face(
                file=img_file,
                region=face.region,
                embedding=face.embedding,
                confidence=face.confidence,
            )
            self._write_face_thumb(
                file_path,
                archive_path=archive_path,
                face_id=stored_face.id,
                thumb_webp=face.thumb_webp,
            )
        self._logger.debug(f"Stored {len(faces)} face(s) from {file_path.name}")
        return len(faces)

    def _should_process(self, file_path: Path) -> bool:
        """Return True if *file_path* passes the detector-level filters."""
        if file_path.is_symlink():
            self._logger.debug(f"Skipping {file_path}: is symlink")
            return False

        if file_path.suffix.lower() not in self._settings.source_extensions:
            self._logger.debug(
                f"Skipping {file_path}: extension {file_path.suffix!r} not in source_extensions"
            )
            return False

        return True

    def _scan_path(
        self,
        path: Path,
        store: RecognizerStore,
        *,
        overwrite: bool,
    ) -> int:
        """Walk *path* recursively and process all eligible image files."""
        total = 0
        for file_path in sorted(path.rglob("*")):
            if not file_path.is_file():
                continue
            if not self._should_process(file_path):
                continue

            count = self._process_single_file(
                file_path,
                store,
                archive_path=path,
                overwrite=overwrite,
            )
            total += count

        self._logger.info(f"Scan complete: {total} face(s) detected under {path}")
        return total

    def _process_pending_file(
        self,
        store: RecognizerStore,
        *,
        file_id: int,
        rel_path: str,
        file_status: str,
        archive_path: Path,
    ) -> int:
        """Process one DB-backed face-detection task candidate."""

        def now() -> str:
            return datetime.datetime.now(datetime.timezone.utc).isoformat()

        store.start_task(file_id, now())

        file_path = archive_path / rel_path
        if not file_path.exists():
            self._logger.warning(f"File not found, skipping: {file_path}")
            store.mark_failed(file_id, "File not found", now())
            return 0

        try:
            if not self._should_process(file_path):
                store.mark_skipped(file_id, now())
                return 0

            count = self._process_single_file(
                file_path,
                store,
                archive_path=archive_path,
                overwrite=file_status == FILE_STATUS_MODIFIED,
            )
            store.mark_done(file_id, now())
            return count
        except Exception as exc:
            self._logger.error(f"Error processing {file_path.name}: {exc}")
            store.mark_failed(file_id, str(exc), now())
            return 0

    def _cluster_if_needed(self, store: RecognizerStore, *, total_faces: int, cluster: bool) -> None:
        """Run clustering if requested and this cycle stored new faces."""
        if not cluster:
            return
        if total_faces == 0:
            self._logger.info("No new faces detected — skipping clustering")
            return

        clusterer = RecognizerClusterer(
            self._logger,
            eps=self._settings.clustering_eps,
            min_samples=self._settings.clustering_min_samples,
        )
        clusterer.assign_domains(store)

    def _build_face_thumb_dir(self, file_path: Path, *, archive_path: Path) -> Path:
        try:
            relative_path = file_path.relative_to(archive_path)
        except ValueError as exc:
            raise ValueError(
                f"Source path {file_path} is not inside archive root {archive_path}"
            ) from exc

        return archive_path / ARCHIVE_SYSTEM_DIR / FACES_DIR / relative_path.parent / file_path.stem

    def _write_face_thumb(
        self,
        file_path: Path,
        *,
        archive_path: Path,
        face_id: int,
        thumb_webp: bytes,
    ) -> None:
        output_dir = self._build_face_thumb_dir(file_path, archive_path=archive_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"face-{face_id}.webp"
        output_path.write_bytes(thumb_webp)

    def _delete_face_thumb_dir(self, file_path: Path, *, archive_path: Path) -> None:
        output_dir = self._build_face_thumb_dir(file_path, archive_path=archive_path)
        if output_dir.exists():
            shutil.rmtree(output_dir)
