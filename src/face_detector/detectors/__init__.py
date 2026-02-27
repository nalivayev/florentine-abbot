"""Face detector plugin registry.

Built-in detectors live in sub-packages of this package and are loaded
automatically.  Third-party detectors register themselves via the
``face_detector.detectors`` entry-points group in their own
``pyproject.toml``::

    [project.entry-points."face_detector.detectors"]
    deepface = "face_detector_deepface.detector:DeepFaceDetector"
"""

import importlib
import pkgutil
import sys
from pathlib import Path
from typing import Callable
from importlib.metadata import entry_points

from face_detector.detector import FaceDetector

_detectors: dict[str, type[FaceDetector]] = {}


def register_detector(name: str) -> Callable[[type[FaceDetector]], type[FaceDetector]]:
    """Decorator for registering detector classes under a symbolic name.

    Args:
        name: Symbolic name used on the CLI and in config (e.g. ``'insightface'``).

    Returns:
        Class decorator that registers the class and returns it unchanged.
    """
    def decorator(cls: type[FaceDetector]) -> type[FaceDetector]:
        _detectors[name] = cls
        return cls
    return decorator


def get_detector(name: str) -> type[FaceDetector]:
    """Return the registered detector class for *name*.

    Args:
        name: Symbolic name (e.g. ``'insightface'``).

    Returns:
        Registered detector class.

    Raises:
        ValueError: If no detector with that name is registered.
    """
    if name not in _detectors:
        available = ", ".join(sorted(_detectors)) or "(none)"
        raise ValueError(f"Unknown detector: {name!r}. Available: {available}")
    return _detectors[name]


def load_detectors() -> None:
    """Load all built-in and external detector plugins.

    1. Imports ``detector.py`` from each sub-package of this package.
    2. Loads external plugins registered via the ``face_detector.detectors``
       entry-points group.
    """
    package_dir = Path(__file__).parent
    for _, subpkg, is_pkg in pkgutil.iter_modules([str(package_dir)]):
        if not is_pkg:
            continue
        subpkg_path = package_dir / subpkg
        if (subpkg_path / "detector.py").exists():
            importlib.import_module(f".{subpkg}.detector", package=__name__)

    try:
        plugin_group = "face_detector.detectors"
        if sys.version_info >= (3, 10):
            plugins = entry_points(group=plugin_group)
        else:
            eps = entry_points()
            plugins = eps.get(plugin_group, [])  # type: ignore[union-attr]

        for ep in plugins:
            detector_class = ep.load()
            _detectors[ep.name] = detector_class
    except Exception:
        pass


load_detectors()
