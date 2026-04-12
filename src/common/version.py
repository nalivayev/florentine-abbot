"""
Version utilities for scan-batcher package.
"""

import importlib.metadata


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
