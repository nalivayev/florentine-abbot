"""Regression tests for Recognizer database-backed orchestration."""

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from common.database import ArchiveDatabase
from common.database import FILE_STATUS_MODIFIED, TASK_STATUS_DONE, TASK_STATUS_PENDING
from common.logger import Logger
from face_recognizer.classes import RecognizerSettings
from face_recognizer.detector import FaceDetector, detector, register_detector_class
from face_recognizer.recognizer import Recognizer
from face_recognizer.store import RecognizerStore


@detector("detector-db-test")
class RecognizerDbTestDetector(FaceDetector):
    """Fake detector backend used for daemon-mode regression tests."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def detect(self, image_path: Path) -> list[object]:
        return []


register_detector_class(RecognizerDbTestDetector)


class TestRecognizerDb:
    """Covers DB/task orchestration now owned by Recognizer."""

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _close_conn(database: ArchiveDatabase) -> None:
        database.close_conn()

    def test_modified_file_uses_overwrite_for_existing_face_records(self) -> None:
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            database = ArchiveDatabase(tmp_path)
            source_file = tmp_path / "1950" / "scan.tif"
            source_file.parent.mkdir(parents=True, exist_ok=True)
            source_file.write_bytes(b"scan data")

            conn = database.get_conn()

            try:
                conn.execute(
                    "INSERT INTO files (path, status, imported_at) VALUES (?, ?, ?)",
                    ("1950/scan.tif", FILE_STATUS_MODIFIED, self._now()),
                )
                file_id = conn.execute(
                    "SELECT id FROM files WHERE path = ?",
                    ("1950/scan.tif",),
                ).fetchone()[0]
                conn.execute(
                    "INSERT INTO tasks (file_id, daemon, status, updated_at) VALUES (?, ?, ?, ?)",
                    (file_id, "face-recognizer", TASK_STATUS_PENDING, self._now()),
                )
                conn.commit()

                self._close_conn(database)

                settings = RecognizerSettings.from_data(detector="detector-db-test")
                logger = Logger("test_recognizer_db")
                with patch.object(Recognizer, "_should_process", return_value=True), patch.object(
                    Recognizer,
                    "_process_single_file",
                    return_value=1,
                ) as mock_process:
                    recognizer = Recognizer(logger, settings=settings)
                    total = recognizer.poll(tmp_path, cluster=False)

                conn = database.get_conn()
                row = conn.execute(
                    "SELECT status FROM tasks WHERE file_id = ? AND daemon = ?",
                    (file_id, "face-recognizer"),
                ).fetchone()

                assert total == 1
                assert row["status"] == TASK_STATUS_DONE
                assert mock_process.call_count == 1
                assert mock_process.call_args.args[0] == source_file
                assert isinstance(mock_process.call_args.args[1], RecognizerStore)
                assert mock_process.call_args.kwargs["overwrite"] is True
            finally:
                self._close_conn(database)