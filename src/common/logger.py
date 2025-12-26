"""Unified logging system for Florentine Abbot.

Provides centralized logging configuration with support for:
- Automatic log directory management
- File rotation
- Console and file output
- Consistent timestamp format across all modules
"""

import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class Logger:
    """Centralized logging configuration and path management.
    
    This class provides a unified interface for setting up logging across all
    Florentine Abbot modules with consistent formatting, rotation, and path resolution.
    
    Features:
    - Automatic log directory creation
    - Environment variable support (FLORENTINE_LOG_DIR)
    - Log file rotation (10 MB per file, 5 backups)
    - Unified timestamp format: YYYY.MM.DD HH:MM:SS.mmm
    - Console and file output
    
    Example:
        >>> logger = Logger("scan_batcher", level=logging.INFO, console=True)
        >>> logger.info("Starting scan workflow")
    """
    
    # Unified format for the entire project
    # Format: YYYY.MM.DD HH:MM:SS.mmm - module.name - LEVEL - message
    LOG_FORMAT = "%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y.%m.%d %H:%M:%S"
    
    # Default rotation settings
    DEFAULT_ROTATION_SIZE = 10 * 1024 * 1024  # 10 MB
    DEFAULT_BACKUP_COUNT = 5
    
    def __init__(
        self, 
        module_name: str, 
        custom_dir: Optional[str] = None,
        level: int = logging.INFO,
        console: bool = True,
        rotation_size: Optional[int] = None,
        backup_count: Optional[int] = None
    ):
        """Initialize and configure logger for a specific module.
        
        Args:
            module_name: Name of the module (e.g., "scan_batcher", "file_organizer")
            custom_dir: Optional custom log directory path (overrides default)
            level: Logging level (logging.DEBUG, logging.INFO, etc.). Default: INFO.
            console: Whether to output logs to stdout. Default: True.
            rotation_size: Maximum log file size in bytes before rotation. Default: 10 MB.
            backup_count: Number of rotated backup files to keep. Default: 5.
        """
        self.module_name = module_name
        self.custom_dir = custom_dir
        self._log_file = self._resolve_log_file()
        
        # Setup logging immediately
        handlers = []
        
        # Console handler (stdout)
        if console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter(self.LOG_FORMAT, self.LOG_DATE_FORMAT))
            handlers.append(console_handler)
        
        # File handler with rotation
        if rotation_size is None:
            rotation_size = self.DEFAULT_ROTATION_SIZE
        if backup_count is None:
            backup_count = self.DEFAULT_BACKUP_COUNT
            
        file_handler = RotatingFileHandler(
            self._log_file,
            maxBytes=rotation_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(self.LOG_FORMAT, self.LOG_DATE_FORMAT))
        handlers.append(file_handler)
        
        # Configure root logger
        logging.basicConfig(
            level=level,
            handlers=handlers,
            force=True  # Override any existing configuration
        )
        
        # Store logger instance
        self._logger = logging.getLogger(self.module_name)
    
    def _get_log_directory(self) -> Path:
        """Get the log directory path with priority resolution.
        
        Priority (highest to lowest):
        1. custom_dir parameter (CLI --log-path argument)
        2. FLORENTINE_LOG_DIR environment variable (for systemd, Docker)
        3. User home directory: ~/.florentine-abbot/logs/ (default)
        
        Returns:
            Path: Absolute path to the log directory.
        """
        # Priority 1: CLI argument
        if self.custom_dir:
            log_dir = Path(self.custom_dir)
        # Priority 2: Environment variable (for systemd, Docker, custom deployments)
        elif env_log_dir := os.getenv("FLORENTINE_LOG_DIR"):
            log_dir = Path(env_log_dir)
        # Priority 3: Default (user home directory)
        else:
            log_dir = Path.home() / ".florentine-abbot" / "logs"
        
        # Ensure directory exists
        log_dir.mkdir(parents=True, exist_ok=True)
        
        return log_dir
    
    def _resolve_log_file(self) -> Path:
        """Resolve the full path to the log file.
        
        Returns:
            Path: Absolute path to the log file.
        """
        return self._get_log_directory() / f"{self.module_name}.log"
    
    # Delegate logging methods to internal logger
    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log a debug message."""
        self._logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs) -> None:
        """Log an info message."""
        self._logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log a warning message."""
        self._logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs) -> None:
        """Log an error message."""
        self._logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs) -> None:
        """Log a critical message."""
        self._logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs) -> None:
        """Log an exception with traceback."""
        self._logger.exception(msg, *args, **kwargs)
    
    @property
    def log_file(self) -> Path:
        """Get the path to the log file.
        
        Returns:
            Path: Absolute path to the log file.
        """
        return self._log_file
    
    @property
    def log_directory(self) -> Path:
        """Get the path to the log directory.
        
        Returns:
            Path: Absolute path to the log directory.
        """
        return self._get_log_directory()
