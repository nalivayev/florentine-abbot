"""
Configuration management for Tile Cutter.
"""

from pathlib import Path
from typing import Any

from common.logger import Logger
from common.config_utils import get_config_dir, ensure_config_exists, load_config, get_template_path
from tile_cutter.classes import CutterSettings
from tile_cutter.constants import DAEMON_NAME


class Config:
    """Configuration manager for Tile Cutter.

    Handles loading and access to tile-cutter config file.
    Falls back to defaults when no config file is present.

    Source patterns are glob patterns matched against filenames to identify
    master images eligible for tile generation.  They are listed in
    **priority order** — when multiple sources exist for the same shot,
    the file matching the earliest pattern wins.
    """

    def __init__(self, logger: Logger, config_path: str | Path | None = None) -> None:
        """Initialize configuration.

        Args:
            logger: Logger instance for this config.
            config_path: Path to JSON config file. If None, uses
                tile-cutter/config.json in the standard location.
        """
        self._logger = logger

        if config_path:
            self._config_path = Path(config_path)
        else:
            config_dir = get_config_dir()
            self._config_path = config_dir / DAEMON_NAME / "config.json"

        template_path = get_template_path("tile_cutter", "config.template.json")
        default_config: dict[str, Any] = {
            "help": "Configuration for Tile Cutter"
        }

        if ensure_config_exists(self._logger, self._config_path, default_config, template_path):
            self._logger.info(f"Created new config at {self._config_path}")

        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from file."""
        self._data = load_config(self._logger, self._config_path)
        if self._data:
            self._logger.info(f"Loaded configuration from {self._config_path}")
        else:
            self._logger.debug("Config not found or empty — using defaults")

    def to_settings(self, *, project_data: dict[str, Any] | None = None) -> CutterSettings:
        """Convert loaded file-backed config data to normalized settings."""
        return CutterSettings.from_data(
            local_data=self._data,
            project_data=project_data,
        )
