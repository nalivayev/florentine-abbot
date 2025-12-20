"""Configuration management for archive keeper."""

import logging
from pathlib import Path
from typing import Any

from common.config_utils import (
    get_config_path,
    ensure_config_exists,
    load_config,
    get_template_path
)

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for archive keeper."""
    
    def __init__(self, config_path: str | Path | None = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to JSON config file. If None, uses standard location.
        """
        # Get config path (custom or standard location)
        self.config_path = get_config_path('archive-keeper', config_path)
        
        # Ensure config exists, create from template if needed
        template_path = get_template_path('archive_keeper', 'config.template.json')
        default_config = {
            "_comment": "Configuration for Archive Keeper",
            "database": "archive.db",
            "chunk_size": 67108864,  # 64MB
            "log_progress_threshold": 104857600  # 100MB
        }
        
        if ensure_config_exists(self.config_path, default_config, template_path):
            logger.info(f"Created new config at {self.config_path}")
        
        # Load configuration
        self.data: dict[str, Any] = {}
        self._load()
    
    def _load(self) -> None:
        """Load configuration from file."""
        self.data = load_config(self.config_path)
        if self.data:
            logger.info(f"Loaded configuration from {self.config_path}")
        else:
            logger.warning("Using default configuration")
            self.data = {
                "database": "archive.db",
                "chunk_size": 67108864,
                "log_progress_threshold": 104857600
            }
    
    def reload(self) -> bool:
        """
        Reload configuration from file.
        
        Returns:
            True if reload was successful, False otherwise.
        """
        old_data = self.data.copy()
        self._load()
        
        if self.data != old_data:
            logger.info("Configuration reloaded successfully")
            return True
        else:
            logger.debug("Configuration unchanged")
            return False
    
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
    
    @property
    def database(self) -> str:
        """Get database path."""
        return self.get('database', 'archive.db')
    
    @property
    def chunk_size(self) -> int:
        """Get chunk size for file hashing."""
        return self.get('chunk_size', 67108864)
    
    @property
    def log_progress_threshold(self) -> int:
        """Get threshold for logging progress on large files."""
        return self.get('log_progress_threshold', 104857600)
