"""Shared data classes for Tile Cutter."""

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, cast

from common.constants import DEFAULT_CONFIG
from tile_cutter.constants import DEFAULT_SIZE, DEFAULT_TILE_SIZE

_DEFAULT_SOURCE_PRIORITY = [
    "*.MSR.*",
    "*.RAW.*",
]


@dataclass(slots=True)
class CutterSettings:
    """Normalized Tile Cutter settings for batch and daemon orchestration."""

    source_priority: list[str]
    preview_size: int
    tile_size: int
    formats: dict[str, Any]

    @classmethod
    def from_data(
        cls,
        *,
        local_data: dict[str, Any] | None = None,
        project_data: dict[str, Any] | None = None,
    ) -> "CutterSettings":
        """Build settings from already-loaded local and project config data."""
        local = local_data or {}
        project = project_data or DEFAULT_CONFIG

        image_value = local.get("image")
        image: dict[str, Any] = image_value if isinstance(image_value, dict) else {}

        source_priority_value = local.get("priority")
        if not isinstance(source_priority_value, list):
            source_priority = _DEFAULT_SOURCE_PRIORITY
        else:
            source_priority = [str(pattern) for pattern in source_priority_value]

        default_formats = cast(dict[str, Any], DEFAULT_CONFIG["formats"])
        formats_value = project.get("formats", default_formats)
        formats = formats_value if isinstance(formats_value, dict) else default_formats

        preview_size_value = image.get("size", DEFAULT_SIZE)
        tile_size_value = image.get("tile_size", DEFAULT_TILE_SIZE)

        return cls(
            source_priority=list(source_priority),
            preview_size=int(preview_size_value),
            tile_size=int(tile_size_value),
            formats=deepcopy(formats),
        )
