"""
Configuration management for file organizer.
"""

from pathlib import Path
from typing import Any

from common.logger import Logger
from common.config_utils import get_config_dir, ensure_config_exists, load_config, load_optional_config, get_template_path
from common.constants import DEFAULT_TAGS, DEFAULT_SUFFIX_ROUTING


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
            "_comment": "Configuration for File Organizer"
        }

        if ensure_config_exists(self._logger, self._config_path, default_config, template_path):
            self._logger.info(f"Created new config at {self._config_path}")
            self._logger.info("Please edit the configuration file and restart")

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
            self._logger.warning("Using empty configuration")
    
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
    

    
    def get_metadata_tags(self) -> dict[str, str]:
        """
        Get metadata field to XMP tag mapping.

        Loads from tags.json if present, otherwise uses DEFAULT_TAGS.

        Returns:
            dict[str, str]: Mapping field names to XMP tag names.
        """
        config_dir = get_config_dir()
        tags_path = config_dir / "tags.json"
        return load_optional_config(self._logger, tags_path, DEFAULT_TAGS)
    
    def get_suffix_routing(self) -> dict[str, str]:
        """
        Get suffix routing rules.

        Loads from routes.json if present, otherwise uses DEFAULT_SUFFIX_ROUTING.

        Returns:
            dict[str, str]: Mapping file suffixes to subfolder names ('SOURCES', 'DERIVATIVES', '.', etc.).
        """
        config_dir = get_config_dir()
        routes_path = config_dir / "routes.json"
        return load_optional_config(self._logger, routes_path, DEFAULT_SUFFIX_ROUTING)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Args:
            key (str): Configuration key.
            default (Any): Default value if key not found.
        Returns:
            Any: Configuration value or default.
        """
        return self._data.get(key, default)
