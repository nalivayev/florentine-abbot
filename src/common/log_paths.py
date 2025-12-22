"""Centralized log path management for all modules."""

import os
from pathlib import Path


def get_log_directory() -> Path:
    """
    Get the standard log directory for Scan Batcher.
    
    Priority:
    1. SCAN_BATCHER_LOG_DIR environment variable (for custom setups and Docker)
    2. User home directory: ~/.scan-batcher/logs/ (default for the CLI)
    
    The directory is created automatically if it doesn't exist.
    
    Returns:
        Path: Absolute path to the log directory.
    
    Example:
        Linux/Mac: /home/user/.scan-batcher/logs/
        Windows: C:\\Users\\user\\.scan-batcher\\logs\\
        Docker/systemd: /var/log/scan-batcher/ (if SCAN_BATCHER_LOG_DIR is set)
    """
    # Check environment variable first (for systemd, Docker, custom deployments)
    env_log_dir = os.getenv("SCAN_BATCHER_LOG_DIR")
    if env_log_dir:
        log_dir = Path(env_log_dir)
    else:
        # Default: user home directory
        log_dir = Path.home() / ".scan-batcher" / "logs"
    
    # Ensure directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    
    return log_dir


def get_log_file(module_name: str) -> Path:
    """
    Get the standard log file path for a specific module.
    
    Args:
        module_name: Name of the module (e.g., "scan_batcher")
    
    Returns:
        Path: Absolute path to the log file.
    
    Example:
        >>> get_log_file("scan_batcher")
        Path('/home/user/.scan-batcher/logs/scan_batcher.log')
    """
    return get_log_directory() / f"{module_name}.log"
