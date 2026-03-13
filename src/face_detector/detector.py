"""Abstract base class for face detector plugins.

External packages register themselves via the ``face_detector.detectors``
entry-points group.  Built-in detectors live under
:mod:`face_detector.detectors`.

Example entry-point in a third-party ``pyproject.toml``::

    [project.entry-points."face_detector.detectors"]
    deepface = "face_detector_deepface.detector:DeepFaceDetector"

After ``pip install face-detector-deepface`` the detector is automatically
available::

    face-detector batch --detector deepface --path /archive/photos
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from common.logger import Logger


@dataclass
class DetectedFace:
    """A single face detected in an image."""

    #: Bounding box (x, y, w, h) in pixels, top-left origin
    bbox: tuple[int, int, int, int]

    #: Detection confidence in [0.0, 1.0]; None if backend does not report it
    confidence: float | None

    #: L2-normalised embedding vector (float32)
    embedding: np.ndarray = field(repr=False)


class FaceDetector(ABC):
    """Abstract base class for all face detector plugins.

    Each detector is responsible for its own configuration — it reads
    ``get_config_dir() / "face-detector" / "detectors" / <name> / "config.json"``
    directly in ``__init__``.

    The engine handles file filtering (extensions, priority patterns).
    The detector receives a :class:`pathlib.Path` to an eligible file
    and returns the detected faces.
    """

    def __init__(self, logger: Logger) -> None:
        ...

    @abstractmethod
    def detect(self, image_path: Path) -> list[DetectedFace]:
        """Detect faces in *image_path* and return their embeddings.

        Returns a (possibly empty) list of :class:`DetectedFace`.
        """
