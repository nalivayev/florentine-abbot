"""Configuration loader and adaptor for Face Recognizer."""

from pathlib import Path
from typing import Any

from common.logger import Logger
from common.config_utils import get_config_dir, ensure_config_exists, load_config, get_template_path
from face_recognizer.classes import RecognizerSettings
from face_recognizer.constants import DAEMON_NAME


class Config:
    """Configuration loader for Face Recognizer."""

    def __init__(self, logger: Logger, config_path: str | Path | None = None) -> None:
        self._logger = logger

        if config_path:
            self._config_path = Path(config_path)
        else:
            config_dir = get_config_dir()
            self._config_path = config_dir / DAEMON_NAME / "config.json"

        template_path = get_template_path("face_recognizer", "config.template.json")
        default_config: dict[str, Any] = {"help": "Configuration for Face Recognizer"}

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

    def to_settings(
        self,
        *,
        detector: str | None = None,
        source_extensions: list[str] | None = None,
        source_priority: list[str] | None = None,
        clustering_eps: float | None = None,
        clustering_min_samples: int | None = None,
    ) -> RecognizerSettings:
        """Convert loaded file-backed config data to normalized settings."""
        return RecognizerSettings.from_data(
            local_data=self._data,
            detector=detector,
            source_extensions=source_extensions,
            source_priority=source_priority,
            clustering_eps=clustering_eps,
            clustering_min_samples=clustering_min_samples,
        )
