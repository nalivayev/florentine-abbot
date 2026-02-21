"""
Configuration management for Preview Maker.
"""

from pathlib import Path
from typing import Any

from common.logger import Logger
from common.config_utils import get_config_dir, ensure_config_exists, load_config, get_template_path


# Default configuration values
_DEFAULT_SUFFIXES = {
    "master": "MSR",
    "raw": "RAW",
    "preview": "PRV",
}


class Config:
    """
    Configuration manager for Preview Maker.

    Handles loading and access to preview-maker config file.
    Falls back to defaults when no config file is present.
    """

    def __init__(self, logger: Logger, config_path: str | Path | None = None) -> None:
        """
        Initialize configuration.

        Args:
            logger: Logger instance for this config.
            config_path: Path to JSON config file. If None, uses
                preview-maker/config.json in the standard location.
        """
        self._logger = logger

        if config_path:
            self._config_path = Path(config_path)
        else:
            config_dir = get_config_dir()
            self._config_path = config_dir / "preview-maker" / "config.json"

        template_path = get_template_path("preview_maker", "config.template.json")
        default_config: dict[str, Any] = {
            "_comment": "Configuration for Preview Maker"
        }

        if ensure_config_exists(self._logger, self._config_path, default_config, template_path):
            self._logger.info(f"Created new config at {self._config_path}")
            self._logger.info("Please edit the configuration file and restart")

        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from file."""
        self._data = load_config(self._logger, self._config_path)
        if self._data:
            self._logger.info(f"Loaded configuration from {self._config_path}")
        else:
            self._logger.debug("Config not found or empty — using defaults")

    def _get_suffix(self, key: str) -> str:
        """Return a suffix value by key, case-normalized to uppercase."""
        suffixes = self._data.get("suffixes", {})
        value = suffixes.get(key, _DEFAULT_SUFFIXES[key])
        return str(value).upper()

    @property
    def master_suffix(self) -> str:
        """Preferred master suffix (processed/retouched scan). E.g. 'MSR'."""
        return self._get_suffix("master")

    @property
    def raw_suffix(self) -> str:
        """Raw scan suffix (unprocessed). E.g. 'RAW'."""
        return self._get_suffix("raw")

    @property
    def preview_suffix(self) -> str:
        """Preview derivative suffix. E.g. 'PRV'."""
        return self._get_suffix("preview")

    @property
    def source_suffixes(self) -> list[str]:
        """All suffixes that can be used as source for preview generation."""
        return [self.raw_suffix, self.master_suffix]

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a raw configuration value by key.

        Args:
            key: Configuration key.
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        return self._data.get(key, default)
