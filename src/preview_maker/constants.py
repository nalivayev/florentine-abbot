"""
Shared constants for Preview Maker.
"""

from typing import Any

# Maps user-facing format name → (PIL format string, file extension)
FORMAT_MAP: dict[str, tuple[str, str]] = {
    "jpeg": ("JPEG", ".jpg"),
    "png":  ("PNG",  ".png"),
    "webp": ("WEBP", ".webp"),
    "tiff": ("TIFF", ".tif"),
}

# Default PIL save kwargs per format
DEFAULT_FORMAT_OPTIONS: dict[str, dict[str, Any]] = {
    "jpeg": {"quality": 80, "optimize": True},
    "webp": {"quality": 80},
    "png":  {"optimize": True},
    "tiff": {},
}

# Common aliases → canonical format name
FORMAT_ALIASES: dict[str, str] = {
    "jpg": "jpeg",
    "tif": "tiff",
}

DEFAULT_SIZE: int = 2000
DEFAULT_FORMAT: str = "jpeg"
