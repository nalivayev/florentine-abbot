"""
Configuration management for Preview Maker.
"""

from pathlib import Path
from typing import Any

from common.logger import Logger
from common.config_utils import get_config_dir, ensure_config_exists, load_config, get_template_path
from preview_maker.constants import DEFAULT_FORMAT_OPTIONS, DEFAULT_SIZE, DEFAULT_FORMAT


class Config:
    """Configuration manager for Preview Maker.

    Handles loading and access to preview-maker config file.
    Falls back to defaults when no config file is present.

    Source patterns are glob patterns matched against filenames to identify
    master images eligible for preview generation.  They are listed in
    **priority order** — when multiple sources exist for the same shot,
    the file matching the earliest pattern wins.

    The preview filename template uses the same ``{field}`` / ``{field:spec}``
    syntax as ``archive_filename_template`` in ``formats.json``.
    """

    _DEFAULT_SOURCE_PRIORITY: list[str] = [
        "*.MSR.*",
        "*.RAW.*",
    ]
    _DEFAULT_TEMPLATE: str = (
        "{year:04d}.{month:02d}.{day:02d}"
        ".{hour:02d}.{minute:02d}.{second:02d}"
        ".{modifier}.{group}.{subgroup}"
        ".{sequence:04d}.{side}.PRV"
    )

    def __init__(self, logger: Logger, config_path: str | Path | None = None) -> None:
        """Initialize configuration.

        Args:
            logger: Logger instance for this config.
            config_path: Path to JSON config file. If None, uses
                preview-maker/config.json in the standard location.
        """
        self._logger = logger

        if config_path:
            self._config_path = Path(config_path)
        else:
            config_dir = get_config_dir()
            self._config_path = config_dir / "preview-maker" / "config.json"

        template_path = get_template_path("preview_maker", "config.template.json")
        default_config: dict[str, Any] = {
            "help": "Configuration for Preview Maker"
        }

        if ensure_config_exists(self._logger, self._config_path, default_config, template_path):
            self._logger.info(f"Created new config at {self._config_path}")
            self._logger.info("Please edit the configuration file and restart")

        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from file."""
        self._data = load_config(self._logger, self._config_path)
        if self._data:
            self._logger.info(f"Loaded configuration from {self._config_path}")
        else:
            self._logger.debug("Config not found or empty — using defaults")

    @property
    def source_priority(self) -> list[str]:
        """Ordered list of glob patterns identifying source files.

        The first pattern has the highest priority.  When multiple files
        in a folder match different patterns, the one matching an earlier
        pattern is preferred as the preview source.
        """
        return self._data.get("priority", self._DEFAULT_SOURCE_PRIORITY)

    @property
    def template(self) -> str:
        """Template for preview filename stem (without extension).

        Uses the same ``{field}`` syntax as ``archive_filename_template``.
        The literal preview marker (e.g. ``PRV``) should be embedded
        directly in the template string.
        """
        return self._data.get("template", self._DEFAULT_TEMPLATE)

    @property
    def image_format(self) -> str:
        """Output image format name (jpeg, png, webp, tiff)."""
        image = self._data.get("image", {})
        return image.get("format", DEFAULT_FORMAT)

    @property
    def image_size(self) -> int:
        """Maximum long edge in pixels for preview images."""
        image = self._data.get("image", {})
        return int(image.get("size", DEFAULT_SIZE))

    @property
    def save_options(self) -> dict[str, Any]:
        """PIL save keyword arguments for the configured image format.

        Merges built-in defaults with user overrides from the
        format-specific section (e.g. ``image.jpeg.quality``).
        """
        fmt = self.image_format
        defaults = dict(DEFAULT_FORMAT_OPTIONS.get(fmt, {}))
        image = self._data.get("image", {})
        overrides = image.get(fmt, {})
        defaults.update(overrides)
        return defaults

    def get(self, key: str, default: Any = None) -> Any:
        """Get a raw configuration value by key.

        Args:
            key: Configuration key.
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        return self._data.get(key, default)
