"""
Scan Batcher utilities.
"""

import importlib.metadata

from scan_batcher.logger import Logger


def get_version() -> str:
    """Get the installed version of scan-batcher package.

    Returns:
        Version string, or '0.0.0' if package is not installed
        (e.g., during development without installation).
    """
    try:
        return importlib.metadata.version('scan-batcher')
    except importlib.metadata.PackageNotFoundError:
        return '0.0.0'


def log_banner(logger: Logger, app_name: str, version: str, fields: dict[str, str]) -> None:
    """Log a startup banner with app name, version, and key/value fields."""
    logger.info("-" * 45)
    logger.info("  %s %s", app_name, version)
    for label, value in fields.items():
        logger.info("  %-14s %s", label + ":", value)
    logger.info("-" * 45)
