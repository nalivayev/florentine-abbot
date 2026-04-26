"""Blind per-file face detection without config or database orchestration."""

import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from PIL import Image

from common.logger import Logger
from face_recognizer.classes import DetectedFace
from face_recognizer.constants import DEFAULT_DETECTOR, DEFAULT_DETECTION_VIEW_MAX_SIZE
from face_recognizer.detector import FaceDetector, get_detector


@dataclass(frozen=True)
class _PreparedDetectionInput:
    """Resolved image path and coordinate scaling for one detection pass."""

    image_path: Path
    scale_x: float
    scale_y: float


class RecognizerProcessor:
    """Package-level low-level processor for one image file."""

    def __init__(
        self,
        logger: Logger,
        *,
        detector_name: str = DEFAULT_DETECTOR,
        detector: FaceDetector | None = None,
        detection_view_max_size: int = DEFAULT_DETECTION_VIEW_MAX_SIZE,
    ) -> None:
        self._logger = logger
        self._detection_view_max_size = detection_view_max_size
        if detector is not None:
            self._detector = detector
        else:
            detector_cls = get_detector(detector_name)
            self._detector = detector_cls(logger)

    def process(self, file_path: Path) -> list[DetectedFace]:
        """Detect faces in one file and return detections in source coordinates."""
        with self._prepare_detection_input(file_path) as prepared:
            faces = self._detector.detect(prepared.image_path)

        if prepared.scale_x == 1.0 and prepared.scale_y == 1.0:
            return faces

        return [self._scale_face(face, prepared.scale_x, prepared.scale_y) for face in faces]

    @contextmanager
    def _prepare_detection_input(self, file_path: Path) -> Iterator[_PreparedDetectionInput]:
        """Create a temporary detector-friendly view for oversized inputs."""
        if self._detection_view_max_size <= 0:
            yield _PreparedDetectionInput(file_path, 1.0, 1.0)
            return

        Image.MAX_IMAGE_PIXELS = None

        try:
            with Image.open(file_path) as img:
                orig_w, orig_h = img.size
        except Exception as exc:
            self._logger.warning(
                f"Cannot inspect {file_path} before detection, using source file directly: {exc}"
            )
            yield _PreparedDetectionInput(file_path, 1.0, 1.0)
            return

        if max(orig_w, orig_h) <= self._detection_view_max_size:
            yield _PreparedDetectionInput(file_path, 1.0, 1.0)
            return

        with tempfile.TemporaryDirectory(prefix="face-recognizer-") as temp_dir:
            view_path = Path(temp_dir) / f"{file_path.stem}.detect.jpg"

            with Image.open(file_path) as img:
                draft_size = (
                    self._detection_view_max_size,
                    self._detection_view_max_size,
                )
                try:
                    img.draft("RGB", draft_size)
                except Exception:
                    pass

                img.thumbnail(draft_size, Image.Resampling.LANCZOS)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(view_path, format="JPEG", quality=90)

                view_w, view_h = img.size

            scale_x = orig_w / view_w
            scale_y = orig_h / view_h
            self._logger.debug(
                f"Prepared detection view for {file_path.name}: "
                f"{orig_w}x{orig_h} -> {view_w}x{view_h} in system temp"
            )

            yield _PreparedDetectionInput(view_path, scale_x, scale_y)

    @staticmethod
    def _scale_face(face: DetectedFace, scale_x: float, scale_y: float) -> DetectedFace:
        """Map one detection from detector-view coordinates back to source pixels."""
        x, y, width, height = face.bbox
        return DetectedFace(
            bbox=(
                int(round(x * scale_x)),
                int(round(y * scale_y)),
                int(round(width * scale_x)),
                int(round(height * scale_y)),
            ),
            confidence=face.confidence,
            embedding=face.embedding,
        )
