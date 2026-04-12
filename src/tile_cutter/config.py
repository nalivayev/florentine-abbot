"""
Configuration management for Tile Cutter.
"""

from pathlib import Path
from typing import Any

from common.logger import Logger
from common.config_utils import get_config_dir, ensure_config_exists, load_config, get_template_path
from tile_cutter.constants import DEFAULT_FORMAT_OPTIONS, DEFAULT_SIZE, DEFAULT_TILE_SIZE


class Config:
    """Configuration manager for Tile Cutter.

    Handles loading and access to tile-cutter config file.
    Falls back to defaults when no config file is present.

    Source patterns are glob patterns matched against filenames to identify
    master images eligible for tile generation.  They are listed in
    **priority order** — when multiple sources exist for the same shot,
    the file matching the earliest pattern wins.
    """

    _DEFAULT_SOURCE_PRIORITY: list[str] = [
        "*.MSR.*",
        "*.RAW.*",
    ]

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
            self._config_path = config_dir / "tile-cutter" / "config.json"

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

    @property
    def source_priority(self) -> list[str]:
        """Ordered list of glob patterns identifying source files.

        The first pattern has the highest priority.  When multiple files
        in a folder match different patterns, the one matching an earlier
        pattern is preferred as the tile source.
        """
        return self._data.get("priority", self._DEFAULT_SOURCE_PRIORITY)

    @property
    def preview_size(self) -> int:
        """Target short side in pixels for the intermediate image used for tiling."""
        image = self._data.get("image", {})
        return int(image.get("size", DEFAULT_SIZE))

    @property
    def tile_size(self) -> int:
        """Tile side in pixels."""
        image = self._data.get("image", {})
        return int(image.get("tile_size", DEFAULT_TILE_SIZE))

    @property
    def save_options(self) -> dict[str, Any]:
        """PIL save keyword arguments for JPEG tile output.

        Merges built-in defaults with user overrides from image.jpeg section.
        """
        defaults = dict(DEFAULT_FORMAT_OPTIONS)
        image = self._data.get("image", {})
        overrides = image.get("jpeg", {})
        defaults.update(overrides)
        return defaults
