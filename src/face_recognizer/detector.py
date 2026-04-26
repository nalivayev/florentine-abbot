"""Face detector plugin contract and registry.

Built-in and third-party detectors are discovered through the shared
``face_recognizer.detectors`` entry-points group::

    [project.entry-points."face_recognizer.detectors"]
    insightface = "face_recognizer.detectors.insightface.detector:InsightFaceDetector"
    custom = "face_recognizer_custom.detector:CustomFaceDetector"
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from importlib.metadata import distributions, entry_points
from pathlib import Path
import sys
from typing import ClassVar

from common.logger import Logger
from face_recognizer.classes import DetectedFace

_PLUGIN_GROUP = "face_recognizer.detectors"
_SOURCE_DISTRIBUTION_PATH = Path(__file__).resolve().parents[1]
_detectors: dict[str, type["FaceDetector"]] = {}
_loaded = False


class FaceDetector(ABC):
    """Abstract base class for detector plugins."""

    detector_name: ClassVar[str]

    def __init__(self, logger: Logger) -> None:
        ...

    @abstractmethod
    def detect(self, image_path: Path) -> list[DetectedFace]:
        """Detect faces in *image_path* and return their embeddings."""


def detector(name: str) -> Callable[[type[FaceDetector]], type[FaceDetector]]:
    """Declare the symbolic name handled by a detector class."""

    def decorator(cls: type[FaceDetector]) -> type[FaceDetector]:
        cls.detector_name = name
        return cls

    return decorator


def register_detector_class(detector_class: type[FaceDetector]) -> None:
    """Register one detector class using the name declared on the class."""
    detector_name = _get_detector_name(detector_class)
    _detectors[detector_name] = detector_class


def _get_detector_name(detector_class: type[FaceDetector]) -> str:
    detector_name = getattr(detector_class, "detector_name", None)
    if not isinstance(detector_name, str) or not detector_name:
        raise TypeError(
            f"{detector_class.__name__} must define a non-empty detector_name"
        )
    return detector_name


def _load_entry_point_detectors() -> None:
    seen: set[tuple[str, str]] = set()

    try:
        if sys.version_info >= (3, 10):
            plugins = list(entry_points(group=_PLUGIN_GROUP))
        else:
            eps = entry_points()
            plugins = list(eps.get(_PLUGIN_GROUP, []))  # type: ignore[union-attr]
    except Exception:
        plugins = []

    try:
        for dist in distributions(path=[str(_SOURCE_DISTRIBUTION_PATH)]):
            for ep in dist.entry_points:
                if ep.group == _PLUGIN_GROUP:
                    plugins.append(ep)
    except Exception:
        pass

    for ep in plugins:
        signature = (ep.name, ep.value)
        if signature in seen:
            continue
        seen.add(signature)
        try:
            register_detector_class(ep.load())
        except Exception:
            continue


def get_detector(name: str) -> type[FaceDetector]:
    """Return the registered detector class for *name*."""
    if name not in _detectors:
        available = ", ".join(sorted(_detectors)) or "(none)"
        raise ValueError(f"Unknown detector: {name!r}. Available: {available}")
    return _detectors[name]


def load_detectors(*, force_reload: bool = False) -> None:
    """Load detector plugins discovered via the shared entry-points contract."""
    global _loaded

    if _loaded and not force_reload:
        return

    _detectors.clear()
    _load_entry_point_detectors()
    _loaded = True


load_detectors()
