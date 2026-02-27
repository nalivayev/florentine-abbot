"""
Configuration management for Face Detector.
"""

from pathlib import Path
from typing import Any

from common.logger import Logger
from common.config_utils import get_config_dir, ensure_config_exists, load_config, get_template_path
from face_detector.constants import DEFAULT_DETECTOR


class Config:
    """
    Configuration manager for Face Detector.

    Falls back to sensible defaults when no config file is present so the tool
    is usable out-of-the-box.
    """

    _DEFAULT_DETECTION: dict[str, Any] = {
        "backend": "retinaface",
        "model": "ArcFace",
        "enforce_detection": False,
        "align": True,
    }

    _DEFAULT_INSIGHTFACE: dict[str, Any] = {
        "model_pack": "buffalo_l",
        "det_size": 640,
    }

    _DEFAULT_PROCESSING: dict[str, Any] = {
        "source_extensions": [".jpg", ".jpeg", ".tif", ".tiff", ".png", ".bmp"],
        "source_suffixes": ["PRV", "MSR", "RAW"],
    }

    _DEFAULT_CLUSTERING: dict[str, Any] = {
        "eps": 0.4,
        "min_samples": 2,
    }

    def __init__(self, logger: Logger, config_path: str | Path | None = None) -> None:
        self._logger = logger

        if config_path:
            self._config_path = Path(config_path)
        else:
            config_dir = get_config_dir()
            self._config_path = config_dir / "face-detector" / "config.json"

        template_path = get_template_path("face_detector", "config.template.json")
        default_config: dict[str, Any] = {"help": "Configuration for Face Detector"}

        if ensure_config_exists(self._logger, self._config_path, default_config, template_path):
            self._logger.info(f"Created new config at {self._config_path}")

        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        self._data = load_config(self._logger, self._config_path)
        if self._data:
            self._logger.info(f"Loaded configuration from {self._config_path}")
        else:
            self._logger.debug("Config not found or empty — using defaults")

    @property
    def detector(self) -> str:
        """Symbolic name of the detector plugin to use (e.g. ``'insightface'``)."""
        return str(self._data.get("detector", DEFAULT_DETECTOR))

    @property
    def insightface_model_pack(self) -> str:
        """InsightFace model pack name (default: ``'buffalo_l'``)."""
        return str(
            self._data.get("insightface", {}).get("model_pack", self._DEFAULT_INSIGHTFACE["model_pack"])
        )

    @property
    def insightface_det_size(self) -> int:
        """InsightFace detection input size in pixels (default: 640)."""
        return int(
            self._data.get("insightface", {}).get("det_size", self._DEFAULT_INSIGHTFACE["det_size"])
        )

    @property
    def detection_backend(self) -> str:
        """DeepFace detector backend (retinaface, mtcnn, opencv, mediapipe, …)."""
        return str(self._data.get("detection", {}).get("backend", self._DEFAULT_DETECTION["backend"]))

    @property
    def embedding_model(self) -> str:
        """Embedding model name recognised by DeepFace (ArcFace, VGG-Face, …)."""
        return str(self._data.get("detection", {}).get("model", self._DEFAULT_DETECTION["model"]))

    @property
    def enforce_detection(self) -> bool:
        """If False, return empty list instead of raising when no face is found."""
        return bool(
            self._data.get("detection", {}).get("enforce_detection", self._DEFAULT_DETECTION["enforce_detection"])
        )

    @property
    def align(self) -> bool:
        """Align detected faces before embedding extraction."""
        return bool(self._data.get("detection", {}).get("align", self._DEFAULT_DETECTION["align"]))

    @property
    def source_extensions(self) -> list[str]:
        """Lower-cased file extensions eligible for face detection."""
        raw = self._data.get("processing", {}).get(
            "source_extensions", self._DEFAULT_PROCESSING["source_extensions"]
        )
        return [e.lower() for e in raw]

    @property
    def source_suffixes(self) -> list[str]:
        """Filename suffixes (PRV, MSR, RAW, …) eligible for processing."""
        raw = self._data.get("processing", {}).get(
            "source_suffixes", self._DEFAULT_PROCESSING["source_suffixes"]
        )
        return [s.upper() for s in raw]

    @property
    def default_db_path(self) -> Path:
        """Default SQLite database path (None in config → next to config file)."""
        raw = self._data.get("database", {}).get("path")
        if raw:
            return Path(raw)
        return self._config_path.parent / "faces.db"

    @property
    def clustering_eps(self) -> float:
        """DBSCAN eps — cosine distance threshold for same-cluster assignment."""
        return float(
            self._data.get("clustering", {}).get("eps", self._DEFAULT_CLUSTERING["eps"])
        )

    @property
    def clustering_min_samples(self) -> int:
        """DBSCAN min_samples — minimum faces to form a core cluster."""
        return int(
            self._data.get("clustering", {}).get("min_samples", self._DEFAULT_CLUSTERING["min_samples"])
        )
