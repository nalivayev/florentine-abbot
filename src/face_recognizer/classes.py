"""Shared Face Recognizer data classes and settings."""

from dataclasses import dataclass, field
from typing import Any, cast

import numpy

from face_recognizer.constants import DEFAULT_DETECTOR

_DEFAULT_SOURCE_EXTENSIONS = [".jpg", ".jpeg", ".tif", ".tiff", ".png", ".bmp"]
_DEFAULT_SOURCE_PRIORITY: list[str] = []
_DEFAULT_CLUSTERING_EPS = 0.4
_DEFAULT_CLUSTERING_MIN_SAMPLES = 2


@dataclass
class DetectedFace:
    """A single face detected in an image."""

    bbox: tuple[int, int, int, int]
    confidence: float | None
    embedding: numpy.ndarray = field(repr=False)


@dataclass(slots=True)
class RecognizerSettings:
    """Normalized Face Recognizer settings for batch and daemon orchestration."""

    detector: str
    source_extensions: list[str]
    source_priority: list[str]
    clustering_eps: float
    clustering_min_samples: int

    @classmethod
    def from_data(
        cls,
        *,
        local_data: dict[str, Any] | None = None,
        detector: str | None = None,
        source_extensions: list[str] | None = None,
        source_priority: list[str] | None = None,
        clustering_eps: float | None = None,
        clustering_min_samples: int | None = None,
    ) -> "RecognizerSettings":
        """Build settings from already-loaded config data and explicit overrides."""
        local = local_data or {}

        processing_value = local.get("processing")
        processing: dict[str, Any] = (
            cast(dict[str, Any], processing_value)
            if isinstance(processing_value, dict)
            else {}
        )
        clustering_value = local.get("clustering")
        clustering: dict[str, Any] = (
            cast(dict[str, Any], clustering_value)
            if isinstance(clustering_value, dict)
            else {}
        )

        resolved_detector = detector or str(
            local.get("detector", DEFAULT_DETECTOR)
        )

        raw_extensions = (
            source_extensions
            if source_extensions is not None
            else processing.get("source_extensions", _DEFAULT_SOURCE_EXTENSIONS)
        )
        if not isinstance(raw_extensions, list):
            resolved_extensions = list(_DEFAULT_SOURCE_EXTENSIONS)
        else:
            resolved_extensions = [
                str(ext).lower() for ext in cast(list[Any], raw_extensions)
            ]

        raw_priority = (
            source_priority
            if source_priority is not None
            else processing.get("source_priority", _DEFAULT_SOURCE_PRIORITY)
        )
        if not isinstance(raw_priority, list):
            resolved_priority = list(_DEFAULT_SOURCE_PRIORITY)
        else:
            resolved_priority = [
                str(pattern) for pattern in cast(list[Any], raw_priority)
            ]

        resolved_eps = float(
            clustering_eps
            if clustering_eps is not None
            else clustering.get("eps", _DEFAULT_CLUSTERING_EPS)
        )
        resolved_min_samples = int(
            clustering_min_samples
            if clustering_min_samples is not None
            else clustering.get("min_samples", _DEFAULT_CLUSTERING_MIN_SAMPLES)
        )

        return cls(
            detector=resolved_detector,
            source_extensions=resolved_extensions,
            source_priority=resolved_priority,
            clustering_eps=resolved_eps,
            clustering_min_samples=resolved_min_samples,
        )
