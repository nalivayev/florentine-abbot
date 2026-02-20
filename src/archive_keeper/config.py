"""
Configuration management for archive keeper.
"""

from pathlib import Path
from typing import Any

from common.logger import Logger
from common.config_utils import get_config_path, ensure_config_exists, load_config, get_template_path


class Config:
    """
    Configuration manager for archive keeper.
    """
    
    def __init__(self, logger: Logger, config_path: str | Path | None = None):
        """
        Initialize configuration.
        
        Args:
            logger: Logger instance for this config.
            config_path: Path to JSON config file. If None, uses standard location.
        """
        self._logger = logger
        # Get config path (custom or standard location)
        self._config_path = get_config_path('archive-keeper', config_path)
        
        # Ensure config exists, create from template if needed
        template_path = get_template_path('archive_keeper', 'config.template.json')
        default_config = {
            "_comment": "Configuration for Archive Keeper",
            "database": "archive.db",
            "chunk_size": 67108864,  # 64MB
            "log_progress_threshold": 104857600  # 100MB
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
            self._logger.warning("Using default configuration")
            self._data = {
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
        old_data = self._data.copy()
        self._load()
        
        if self._data != old_data:
            self._logger.info("Configuration reloaded successfully")
            return True
        else:
            self._logger.debug("Configuration unchanged")
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
        return self._data.get(key, default)

    @property
    def config_path(self) -> Path:
        """
        Path to the loaded configuration file.
        """
        return self._config_path

    @property
    def database(self) -> str:
        """
        Get database path.
        """
        return self.get('database', 'archive.db')
    
    @property
    def chunk_size(self) -> int:
        """
        Get chunk size for file hashing.
        """
        return self.get('chunk_size', 67108864)
    
    @property
    def log_progress_threshold(self) -> int:
        """
        Get threshold for logging progress on large files.
        """
        return self.get('log_progress_threshold', 104857600)
