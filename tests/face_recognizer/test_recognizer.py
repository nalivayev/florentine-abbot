"""Regression tests for Recognizer batch behavior."""

import io
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
                region=(0.25, 0.25, 0.5, 0.5),
                confidence=0.9,
                embedding=numpy.ones(512, dtype=numpy.float32),
            )
        ]


register_detector_class(RecognizerTestDetector)


class TestRecognizer:
    """Covers one-shot face-detection orchestration over an archive tree."""

    @staticmethod
    def _make_thumb_bytes(color: str = "white") -> bytes:
        buf = io.BytesIO()
        Image.new("RGB", (40, 40), color=color).save(buf, format="WEBP", quality=90)
        return buf.getvalue()

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

    def test_execute_writes_face_thumbs_under_system_faces(self) -> None:
        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_dir = tmp_path / "1950" / "1950.06.15" / "SOURCES"
            source_dir.mkdir(parents=True, exist_ok=True)

            source_file = source_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.RAW.tiff"
            Image.new("RGB", (100, 100), color="white").save(source_file)

            settings = RecognizerSettings.from_data(detector="detector-test")
            recognizer = Recognizer(Logger("test_recognizer_thumbs"), settings=settings)

            count = recognizer.execute(path=tmp_path, overwrite=False, cluster=False)

            assert count == 1
            with RecognizerStore(tmp_path) as store:
                faces = store.get_faces_by_file(source_file)
                assert len(faces) == 1
                thumb_path = (
                    tmp_path
                    / ".system"
                    / "faces"
                    / "1950"
                    / "1950.06.15"
                    / "SOURCES"
                    / source_file.stem
                    / f"face-{faces[0].id}.webp"
                )

            assert thumb_path.is_file()
            with Image.open(thumb_path) as thumb:
                assert thumb.format == "WEBP"
                assert thumb.size[0] > 0
                assert thumb.size[1] > 0

    def test_overwrite_cleans_stale_face_thumb_files(self) -> None:
        class StubProcessor:
            def __init__(self, batches: list[list[DetectedFace]]) -> None:
                self._batches = list(batches)

            def process_for_storage(self, file_path: Path) -> list[DetectedFace]:
                return self._batches.pop(0)

        with TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source_dir = tmp_path / "1950" / "1950.06.15" / "SOURCES"
            source_dir.mkdir(parents=True, exist_ok=True)

            source_file = source_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.RAW.tiff"
            Image.new("RGB", (100, 100), color="white").save(source_file)

            first_batch = [
                DetectedFace(
                    region=(0.25, 0.25, 0.5, 0.5),
                    confidence=0.9,
                    embedding=numpy.ones(512, dtype=numpy.float32),
                    thumb_webp=self._make_thumb_bytes("white"),
                ),
                DetectedFace(
                    region=(0.75, 0.25, 0.2, 0.2),
                    confidence=0.8,
                    embedding=numpy.ones(512, dtype=numpy.float32),
                    thumb_webp=self._make_thumb_bytes("gray"),
                ),
            ]
            second_batch = [
                DetectedFace(
                    region=(0.5, 0.5, 0.3, 0.3),
                    confidence=0.7,
                    embedding=numpy.ones(512, dtype=numpy.float32),
                    thumb_webp=self._make_thumb_bytes("black"),
                )
            ]

            recognizer = Recognizer(
                Logger("test_recognizer_overwrite_thumbs"),
                settings=RecognizerSettings.from_data(detector="detector-test"),
                processor=StubProcessor([first_batch, second_batch]),
            )

            first_count = recognizer.execute(path=tmp_path, overwrite=False, cluster=False)
            second_count = recognizer.execute(path=tmp_path, overwrite=True, cluster=False)

            assert first_count == 2
            assert second_count == 1

            thumb_dir = (
                tmp_path
                / ".system"
                / "faces"
                / "1950"
                / "1950.06.15"
                / "SOURCES"
                / source_file.stem
            )
            thumb_files = sorted(thumb_dir.glob("face-*.webp"))
            assert len(thumb_files) == 1
