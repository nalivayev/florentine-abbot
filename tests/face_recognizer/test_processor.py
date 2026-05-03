"""Regression tests for RecognizerProcessor file-level behavior."""

from pathlib import Path

import numpy
from PIL import Image

from common.logger import Logger
from face_recognizer.classes import DetectedFace
from face_recognizer.detector import FaceDetector, get_detector, detector, register_detector_class
from face_recognizer.processor import RecognizerProcessor


@detector("processor-test")
class ProcessorTestDetector(FaceDetector):
    """Fake detector backend used to test the package-level processor."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def detect(self, image_path: Path) -> list[DetectedFace]:
        return [
            DetectedFace(
                region=(0.25, 0.4, 0.3, 0.4),
                confidence=0.95,
                embedding=numpy.ones(512, dtype=numpy.float32),
            )
        ]


register_detector_class(ProcessorTestDetector)


class TestRecognizerProcessor:
    """Covers low-level single-file face detection."""

    def test_builtin_insightface_is_available_via_plugin_registry(self) -> None:
        detector_class = get_detector("insightface")

        assert issubclass(detector_class, FaceDetector)
        assert detector_class.__name__ == "InsightFaceDetector"

    def test_process_returns_faces_from_detector(self) -> None:
        processor = RecognizerProcessor(Logger("test_face_processor"), detector_name="processor-test")

        faces = processor.process(Path("photo.tif"))

        assert len(faces) == 1
        assert faces[0].region == (0.25, 0.4, 0.3, 0.4)
        assert faces[0].confidence == 0.95
        assert faces[0].embedding.shape == (512,)

    def test_process_uses_temp_detection_view_for_large_images(self, tmp_path: Path) -> None:
        source_path = tmp_path / "large_scan.tif"
        Image.new("L", (200, 100), color=128).save(source_path)

        class RecordingDetector(FaceDetector):
            def __init__(self, logger: Logger) -> None:
                self._logger = logger
                self.last_path: Path | None = None
                self.last_size: tuple[int, int] | None = None

            def detect(self, image_path: Path) -> list[DetectedFace]:
                self.last_path = image_path
                with Image.open(image_path) as img:
                    self.last_size = img.size
                return [
                    DetectedFace(
                        region=(0.3125, 0.75, 0.375, 0.5),
                        confidence=0.88,
                        embedding=numpy.ones(512, dtype=numpy.float32),
                    )
                ]

        detector = RecordingDetector(Logger("test_face_processor"))
        processor = RecognizerProcessor(
            Logger("test_face_processor"),
            detector=detector,
            detection_view_max_size=40,
        )

        faces = processor.process(source_path)

        assert detector.last_size == (40, 20)
        assert detector.last_path is not None
        assert detector.last_path != source_path
        assert not detector.last_path.exists()
        assert faces[0].region == (0.3125, 0.75, 0.375, 0.5)
        assert faces[0].confidence == 0.88
