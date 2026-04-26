"""
Configuration management for Preview Maker.
"""

from pathlib import Path
from typing import Any

from common.logger import Logger
from common.config_utils import get_config_dir, ensure_config_exists, load_config, get_template_path
from preview_maker.classes import MakerSettings
from preview_maker.constants import DAEMON_NAME


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
            self._config_path = config_dir / DAEMON_NAME / "config.json"

        template_path = get_template_path("preview_maker", "config.template.json")
        default_config: dict[str, Any] = {
            "help": "Configuration for Preview Maker"
        }

        if ensure_config_exists(self._logger, self._config_path, default_config, template_path):
            self._logger.info(f"Created new config at {self._config_path}")

        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from file."""
        self._data = load_config(self._logger, self._config_path)
        if self._data:
            self._logger.info(f"Loaded configuration from {self._config_path}")
        else:
            self._logger.debug("Config not found or empty — using defaults")

    def to_settings(
        self,
        *,
        project_data: dict[str, Any] | None = None,
        no_metadata: bool = False,
    ) -> MakerSettings:
        """Convert loaded file-backed config data to normalized settings."""
        return MakerSettings.from_data(
            local_data=self._data,
            project_data=project_data,
            no_metadata=no_metadata,
        )
