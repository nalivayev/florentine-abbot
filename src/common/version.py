"""
Version utilities for florentine-abbot package.
"""

import importlib.metadata


def get_version() -> str:
    """Get the installed version of florentine-abbot package.

    Returns:
        Version string, or '0.0.0' if package is not installed
        (e.g., during development without installation).
    """
    try:
        return importlib.metadata.version('florentine-abbot')
    except importlib.metadata.PackageNotFoundError:
        return '0.0.0'
