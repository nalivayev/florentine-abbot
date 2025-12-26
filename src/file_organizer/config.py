"""Configuration management for file organizer."""

from pathlib import Path
from typing import Any

from common.logger import Logger
from common.config_utils import (
    get_config_path,
    ensure_config_exists,
    load_config,
    get_template_path
)


class Config:
    """Configuration manager for file organizer."""
    
    def __init__(self, logger: Logger, config_path: str | Path | None = None):
        """
        Initialize configuration.
        
        Args:
            logger: Logger instance for this config.
            config_path: Path to JSON config file. If None, uses standard location.
        """
        self.logger = logger
        # Get config path (custom or standard location)
        self.config_path = get_config_path('file-organizer', config_path)
        
        # Ensure config exists, create from template if needed
        template_path = get_template_path('file_organizer', 'config.template.json')
        default_config = {
            "_comment": "Configuration for File Organizer",
            "creator": None,
            "credit": None,
            "rights": None,
            "usage_terms": None,
            "source": None
        }
        
        if ensure_config_exists(self.logger, self.config_path, default_config, template_path):
            self.logger.info(f"Created new config at {self.config_path}")
            self.logger.info("Please edit the configuration file and restart")
        
        # Load configuration
        self.data: dict[str, Any] = {}
        self._load()
    
    def _load(self) -> None:
        """Load configuration from file."""
        self.data = load_config(self.logger, self.config_path)
        if self.data:
            self.logger.info(f"Loaded configuration from {self.config_path}")
        else:
            self.logger.warning("Using empty configuration")
    
    def reload(self) -> bool:
        """
        Reload configuration from file.
        
        Returns:
            True if reload was successful, False otherwise.
        """
        old_data = self.data.copy()
        self._load()
        
        if self.data != old_data:
            self.logger.info("Configuration reloaded successfully")
            return True
        else:
            self.logger.debug("Configuration unchanged")
            return False
    
    def get_metadata(self) -> dict[str, str | None]:
        """
        Get metadata configuration for XMP fields.
        
        Returns:
            Dictionary with XMP field values.
        """
        return {
            "creator": self.data.get("creator"),
            "credit": self.data.get("credit"),
            "rights": self.data.get("rights"),
            "usage_terms": self.data.get("usage_terms"),
            "source": self.data.get("source"),
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key.
            default: Default value if key not found.
            
        Returns:
            Configuration value or default.
        """
        return self.data.get(key, default)
