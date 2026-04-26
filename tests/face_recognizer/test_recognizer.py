"""Regression tests for Recognizer batch behavior."""

from pathlib import Path
from tempfile import TemporaryDirectory

import numpy
from PIL import Image

from common.logger import Logger
from face_recognizer.classes import DetectedFace, RecognizerSettings
from face_recognizer.detector import FaceDetector, detector, register_detector_class
from face_recognizer.recognizer import Recognizer
from face_recognizer.store import RecognizerStore


@detector("detector-test")
class RecognizerTestDetector(FaceDetector):
    """Fake detector backend used for detector batch regression tests."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def detect(self, image_path: Path) -> list[DetectedFace]:
        return [
            DetectedFace(
                bbox=(0, 0, 50, 50),
                confidence=0.9,
                embedding=numpy.ones(512, dtype=numpy.float32),
            )
        ]


register_detector_class(RecognizerTestDetector)


class TestRecognizer:
    """Covers one-shot face-detection orchestration over an archive tree."""

    def test_execute_processes_all_supported_images_by_default(self) -> None:
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            date_dir = tmp_path / "1950" / "1950.06.15" / "SOURCES"
            date_dir.mkdir(parents=True, exist_ok=True)

            msr_file = date_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff"
            raw_file = date_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.RAW.tiff"
            ignored = date_dir / "notes.txt"
            Image.new("RGB", (100, 100), color="white").save(msr_file)
            Image.new("RGB", (100, 100), color="white").save(raw_file)
            ignored.write_text("ignore me", encoding="utf-8")

            settings = RecognizerSettings.from_data(detector="detector-test")
            recognizer = Recognizer(Logger("test_recognizer"), settings=settings)

            count = recognizer.execute(path=tmp_path, overwrite=False, cluster=False)

            assert count == 2
            with RecognizerStore(tmp_path) as store:
                assert store.face_count() == 2
                for file_path in (msr_file, raw_file):
                    stored_faces = store.get_faces_by_file(file_path)
                    assert len(stored_faces) == 1
                    assert abs(stored_faces[0].center_x - 0.25) < 1e-9
                    assert abs(stored_faces[0].center_y - 0.25) < 1e-9
                    assert abs(stored_faces[0].width - 0.5) < 1e-9
                    assert abs(stored_faces[0].height - 0.5) < 1e-9

    def test_execute_ignores_legacy_source_priority_filters(self) -> None:
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            date_dir = tmp_path / "1950" / "1950.06.15" / "SOURCES"
            date_dir.mkdir(parents=True, exist_ok=True)

            msr_file = date_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff"
            raw_file = date_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.RAW.tiff"
            Image.new("RGB", (100, 100), color="white").save(msr_file)
            Image.new("RGB", (100, 100), color="white").save(raw_file)

            settings = RecognizerSettings.from_data(
                detector="detector-test",
                source_priority=["*.MSR.*"],
            )
            recognizer = Recognizer(Logger("test_recognizer_legacy_config"), settings=settings)

            count = recognizer.execute(path=tmp_path, overwrite=False, cluster=False)

            assert count == 2
            with RecognizerStore(tmp_path) as store:
                assert len(store.get_faces_by_file(msr_file)) == 1
                assert len(store.get_faces_by_file(raw_file)) == 1
