"""Unified logging configuration for all modules."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# Unified format for the entire project
# Format: YYYY.MM.DD HH:MM:SS.mmm - module.name - LEVEL - message
LOG_FORMAT = "%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y.%m.%d %H:%M:%S"


def setup_logging(
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    console: bool = True,
    rotation_size: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> None:
    """
    Configure unified logging for all modules.
    
    This function sets up consistent logging across the entire project with support for:
    - Console output (stdout)
    - File output with automatic rotation
    - Unified timestamp format (YYYY.MM.DD HH:MM:SS.mmm)
    - Module names and log levels
    
    Args:
        log_file: Path to log file. If None, no file logging is configured.
        level: Logging level (logging.DEBUG, logging.INFO, etc.). Default: INFO.
        console: Whether to output logs to stdout. Default: True.
        rotation_size: Maximum log file size in bytes before rotation. Default: 10 MB.
        backup_count: Number of rotated backup files to keep. Default: 5.
    
    Example:
        >>> from pathlib import Path
        >>> setup_logging(
        ...     log_file=Path("app.log"),
        ...     level=logging.INFO,
        ...     console=True
        ... )
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Application started")
    """
    handlers = []
    
    # Console handler (stdout)
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        )
        handlers.append(console_handler)
    
    # File handler with rotation
    if log_file:
        # Ensure parent directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=rotation_size,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setFormatter(
            logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        )
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
