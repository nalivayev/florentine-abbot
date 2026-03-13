"""
Configuration management for file organizer.
"""

from pathlib import Path
from typing import Any

from common.logger import Logger
from common.config_utils import get_config_dir, ensure_config_exists, load_config, get_template_path


class Config:
    """
    Configuration manager for file organizer.
    Handles loading, reloading, and access to organizer config files.
    """

    def __init__(self, logger: Logger, config_path: str | Path | None = None) -> None:
        """
        Initialize configuration.

        Args:
            logger (Logger): Logger instance for this config.
            config_path (str|Path|None): Path to JSON config file. If None, uses file-organizer/config.json in standard location.
        """
        self._logger: Logger = logger

        # Get config path (custom or standard file-organizer/config.json)
        if config_path:
            self._config_path: Path = Path(config_path)
        else:
            config_dir = get_config_dir()
            self._config_path = config_dir / 'file-organizer' / 'config.json'

        # Ensure config exists, create from template if needed
        template_path = get_template_path('file_organizer', 'config.template.json')
        default_config = {
            "help": "Configuration for File Organizer"
        }

        if ensure_config_exists(self._logger, self._config_path, default_config, template_path):
            self._logger.info(f"Created new config at {self._config_path}")

        # Load configuration
        self._data: dict[str, Any] = {}
        self._load()
    

    def _load(self) -> None:
        """
        Load configuration from file.
        """
        self._data = load_config(self._logger, self._config_path)
        if self._data:
            self._logger.info(f"Loaded configuration from {self._config_path}")
        else:
            self._logger.debug("Config not found or empty — using defaults")
    

    def reload(self) -> bool:
        """
        Reload configuration from file.

        Returns:
            bool: True if reload was successful, False otherwise.
        """
        old_data = self._data.copy()
        self._load()

        if self._data != old_data:
            self._logger.info("Configuration reloaded successfully")
            return True
        else:
            self._logger.debug("Configuration unchanged")
            return False
    

    @property
    def metadata(self) -> dict:
        """The ``metadata`` section (tag mapping + per-language texts)."""
        return self._data.get("metadata", {})
