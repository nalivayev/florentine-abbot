"""Shared data classes for Preview Maker."""

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, cast

from common.constants import DEFAULT_CONFIG
from preview_maker.constants import DEFAULT_FORMAT, DEFAULT_FORMAT_OPTIONS, DEFAULT_SIZE

_DEFAULT_SOURCE_PRIORITY = [
    "*.MSR.*",
    "*.RAW.*",
]

_DEFAULT_TEMPLATE = (
    "{year:04d}.{month:02d}.{day:02d}"
    ".{hour:02d}.{minute:02d}.{second:02d}"
    ".{modifier}.{group}.{subgroup}"
    ".{sequence:04d}.{side}.PRV"
)


@dataclass(slots=True)
class MakerSettings:
    """Normalized Preview Maker settings for batch and daemon orchestration."""

    source_priority: list[str]
    template: str
    image_format: str
    image_size: int
    save_options: dict[str, Any]
    formats: dict[str, Any]
    routes: dict[str, Any]
    no_metadata: bool = False

    @classmethod
    def from_data(
        cls,
        *,
        local_data: dict[str, Any] | None = None,
        project_data: dict[str, Any] | None = None,
        no_metadata: bool = False,
    ) -> "MakerSettings":
        """Build settings from already-loaded local and project config data."""
        local = local_data or {}
        project = project_data or DEFAULT_CONFIG

        image_value = local.get("image")
        image: dict[str, Any] = cast(dict[str, Any], image_value) if isinstance(image_value, dict) else {}

        image_format_value = image.get("format", DEFAULT_FORMAT)
        image_format = str(image_format_value)
        save_options = dict(DEFAULT_FORMAT_OPTIONS.get(image_format, {}))
        overrides_value = image.get(image_format, {})
        overrides: dict[str, Any] = cast(dict[str, Any], overrides_value) if isinstance(overrides_value, dict) else {}
        save_options.update(overrides)

        source_priority_value = local.get("priority")
        if not isinstance(source_priority_value, list):
            source_priority = _DEFAULT_SOURCE_PRIORITY
        else:
            source_priority = [str(pattern) for pattern in cast(list[Any], source_priority_value)]

        template_value = local.get("template", _DEFAULT_TEMPLATE)
        if not isinstance(template_value, str):
            template = _DEFAULT_TEMPLATE
        else:
            template = template_value

        default_formats = cast(dict[str, Any], DEFAULT_CONFIG["formats"])
        formats_value = project.get("formats", default_formats)
        formats: dict[str, Any] = cast(dict[str, Any], formats_value) if isinstance(formats_value, dict) else default_formats

        default_routes = cast(dict[str, Any], DEFAULT_CONFIG["routes"])
        routes_value = project.get("routes", default_routes)
        routes: dict[str, Any] = cast(dict[str, Any], routes_value) if isinstance(routes_value, dict) else default_routes

        image_size_value = image.get("size", DEFAULT_SIZE)
        image_size = int(image_size_value)

        return cls(
            source_priority=list(source_priority),
            template=template,
            image_format=image_format,
            image_size=image_size,
            save_options=save_options,
            formats=deepcopy(formats),
            routes=deepcopy(routes),
            no_metadata=no_metadata,
        )
