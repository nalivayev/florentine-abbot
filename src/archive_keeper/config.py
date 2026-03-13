"""
Configuration management for archive keeper.
"""

from pathlib import Path
from typing import Any

from common.logger import Logger
from common.config_utils import get_config_dir, ensure_config_exists, load_config, get_template_path


class Config:
    """
    Configuration manager for archive keeper.
    """

    _DEFAULT_DATABASE: str = "archive.db"
    _DEFAULT_CHUNK_SIZE: int = 67108864        # 64 MB
    _DEFAULT_LOG_THRESHOLD: int = 104857600   # 100 MB

    def __init__(self, logger: Logger, config_path: str | Path | None = None):
        """
        Initialize configuration.

        Args:
            logger: Logger instance for this config.
            config_path: Path to JSON config file. If None, uses standard location.
        """
        self._logger = logger
        if config_path:
            self._config_path = Path(config_path)
        else:
            self._config_path = get_config_dir() / "archive-keeper" / "config.json"

        # Ensure config exists, create from template if needed
        template_path = get_template_path('archive_keeper', 'config.template.json')
        default_config: dict[str, Any] = {
            "help": "Configuration for Archive Keeper",
            "database": self._DEFAULT_DATABASE,
            "chunk_size": self._DEFAULT_CHUNK_SIZE,
            "log_progress_threshold": self._DEFAULT_LOG_THRESHOLD,
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
    
    @property
    def config_path(self) -> Path:
        """
        Path to the loaded configuration file.
        """
        return self._config_path

    @property
    def database(self) -> str:
        """Path to the archive database file."""
        return self._data.get('database', self._DEFAULT_DATABASE)

    @property
    def chunk_size(self) -> int:
        """Chunk size in bytes for file hashing (default: 64 MB)."""
        return self._data.get('chunk_size', self._DEFAULT_CHUNK_SIZE)

    @property
    def log_progress_threshold(self) -> int:
        """File size threshold in bytes above which progress is logged (default: 100 MB)."""
        return self._data.get('log_progress_threshold', self._DEFAULT_LOG_THRESHOLD)
