"""
Shared constants for Tile Cutter.
"""

from typing import Any

# Default PIL save kwargs for tile output
DEFAULT_FORMAT_OPTIONS: dict[str, Any] = {
    "quality": 85,
    "optimize": True,
}

DEFAULT_SIZE: int = 4000       # short side in pixels for the intermediate image
DEFAULT_TILE_SIZE: int = 256   # tile side in pixels
