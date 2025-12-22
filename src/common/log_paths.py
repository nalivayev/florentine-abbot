"""Centralized log path management for all modules."""

import os
from pathlib import Path
from typing import Optional


def get_log_directory(custom_dir: Optional[str] = None) -> Path:
    """
    Get the standard log directory for Florentine Abbot.
    
    Priority (highest to lowest):
    1. custom_dir parameter (CLI --log-dir argument)
    2. FLORENTINE_LOG_DIR environment variable (for systemd, Docker)
    3. User home directory: ~/.florentine-abbot/logs/ (default)
    
    The directory is created automatically if it doesn't exist.
    
    Args:
        custom_dir: Optional custom log directory path (from CLI argument).
    
    Returns:
        Path: Absolute path to the log directory.
    
    Example:
        Linux/Mac: /home/user/.florentine-abbot/logs/
        Windows: C:\\Users\\user\\.florentine-abbot\\logs\\
        Docker/systemd: /var/log/florentine-abbot/ (if FLORENTINE_LOG_DIR is set)
        Custom: /custom/path (if --log-dir is specified)
    """
    # Priority 1: CLI argument
    if custom_dir:
        log_dir = Path(custom_dir)
    # Priority 2: Environment variable (for systemd, Docker, custom deployments)
    elif env_log_dir := os.getenv("FLORENTINE_LOG_DIR"):
        log_dir = Path(env_log_dir)
    # Priority 3: Default (user home directory)
    else:
        log_dir = Path.home() / ".florentine-abbot" / "logs"
    
    # Ensure directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    
    return log_dir


def get_log_file(module_name: str, custom_dir: Optional[str] = None) -> Path:
    """
    Get the standard log file path for a specific module.
    
    Args:
        module_name: Name of the module (e.g., "scan_batcher", "file_organizer", "archive_keeper")
        custom_dir: Optional custom log directory path (from CLI argument).
    
    Returns:
        Path: Absolute path to the log file.
    
    Example:
        >>> get_log_file("scan_batcher")
        Path('/home/user/.florentine-abbot/logs/scan_batcher.log')
        >>> get_log_file("scan_batcher", "/tmp/logs")
        Path('/tmp/logs/scan_batcher.log')
    """
    return get_log_directory(custom_dir) / f"{module_name}.log"
