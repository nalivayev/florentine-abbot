"""Blind per-file face detection without config or database orchestration."""

import io
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from PIL import Image

from common.logger import Logger
from face_recognizer.classes import DetectedFace
from face_recognizer.constants import (
    DEFAULT_DETECTOR,
    DEFAULT_DETECTION_VIEW_MAX_SIZE,
    DEFAULT_FACE_THUMB_MAX_SIZE,
    DEFAULT_FACE_THUMB_PADDING,
)
from face_recognizer.detector import FaceDetector, get_detector


@dataclass(frozen=True)
class _PreparedDetectionInput:
    """Resolved image path and coordinate scaling for one detection pass."""

    image_path: Path


class RecognizerProcessor:
    """Package-level low-level processor for one image file."""

    def __init__(
        self,
        logger: Logger,
        *,
        detector_name: str = DEFAULT_DETECTOR,
        detector: FaceDetector | None = None,
        detection_view_max_size: int = DEFAULT_DETECTION_VIEW_MAX_SIZE,
        face_thumb_max_size: int = DEFAULT_FACE_THUMB_MAX_SIZE,
        face_thumb_padding: float = DEFAULT_FACE_THUMB_PADDING,
    ) -> None:
        self._logger = logger
        self._detection_view_max_size = detection_view_max_size
        self._face_thumb_max_size = face_thumb_max_size
        self._face_thumb_padding = face_thumb_padding
        if detector is not None:
            self._detector = detector
        else:
            detector_cls = get_detector(detector_name)
            self._detector = detector_cls(logger)

    def process(self, file_path: Path) -> list[DetectedFace]:
        """Detect faces in one file and return normalized regions."""
        with self._prepare_detection_input(file_path) as prepared:
            return self._detector.detect(prepared.image_path)

    def process_for_storage(self, file_path: Path) -> list[DetectedFace]:
        """Detect faces and generate persistent face thumbs from the same prepared view."""
        with self._prepare_detection_input(file_path) as prepared:
            faces = self._detector.detect(prepared.image_path)
            if not faces:
                return []

            thumbs = self._build_face_thumbnails(prepared.image_path, faces)
            for face, thumb_webp in zip(faces, thumbs):
                face.thumb_webp = thumb_webp
            return faces

    @contextmanager
    def _prepare_detection_input(self, file_path: Path) -> Iterator[_PreparedDetectionInput]:
        """Create a temporary detector-friendly view for oversized inputs."""
        if self._detection_view_max_size <= 0:
            yield _PreparedDetectionInput(file_path)
            return

        Image.MAX_IMAGE_PIXELS = None

        try:
            with Image.open(file_path) as img:
                orig_w, orig_h = img.size
        except Exception as exc:
            self._logger.warning(
                f"Cannot inspect {file_path} before detection, using source file directly: {exc}"
            )
            yield _PreparedDetectionInput(file_path)
            return

        if max(orig_w, orig_h) <= self._detection_view_max_size:
            yield _PreparedDetectionInput(file_path)
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

            self._logger.debug(
                f"Prepared detection view for {file_path.name}: "
                f"{orig_w}x{orig_h} -> {view_w}x{view_h} in system temp"
            )

            yield _PreparedDetectionInput(view_path)

    def _build_face_thumbnails(
        self,
        image_path: Path,
        faces: list[DetectedFace],
    ) -> list[bytes]:
        """Cut face thumbnails from the already prepared detector view."""
        Image.MAX_IMAGE_PIXELS = None
        with Image.open(image_path) as image:
            image.load()
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGB")

            image_size = image.size
            thumbnails: list[bytes] = []
            for face in faces:
                crop_box = self._crop_box_from_region(face.region, image_size)
                crop = image.crop(crop_box)
                if crop.mode == "RGBA":
                    crop = crop.convert("RGB")
                if max(crop.size) > self._face_thumb_max_size:
                    crop.thumbnail(
                        (self._face_thumb_max_size, self._face_thumb_max_size),
                        Image.Resampling.LANCZOS,
                    )
                thumbnails.append(self._encode_webp(crop))

            return thumbnails

    def _crop_box_from_region(
        self,
        region: tuple[float, float, float, float],
        image_size: tuple[int, int],
    ) -> tuple[int, int, int, int]:
        image_width, image_height = image_size
        center_x, center_y, width, height = region

        padded_width = min(1.0, width * (1.0 + self._face_thumb_padding * 2.0))
        padded_height = min(1.0, height * (1.0 + self._face_thumb_padding * 2.0))

        left = max(0.0, min(1.0, center_x - padded_width / 2.0))
        top = max(0.0, min(1.0, center_y - padded_height / 2.0))
        right = max(0.0, min(1.0, center_x + padded_width / 2.0))
        bottom = max(0.0, min(1.0, center_y + padded_height / 2.0))

        pixel_left = int(round(left * image_width))
        pixel_top = int(round(top * image_height))
        pixel_right = int(round(right * image_width))
        pixel_bottom = int(round(bottom * image_height))

        if pixel_right <= pixel_left:
            pixel_right = min(image_width, pixel_left + 1)
        if pixel_bottom <= pixel_top:
            pixel_bottom = min(image_height, pixel_top + 1)

        return (pixel_left, pixel_top, pixel_right, pixel_bottom)

    @staticmethod
    def _encode_webp(image: Image.Image) -> bytes:
        buf = io.BytesIO()
        image.save(buf, format="WEBP", quality=90)
        return buf.getvalue()
