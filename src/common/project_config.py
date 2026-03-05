"""Unified project configuration singleton.

:class:`ProjectConfig` loads the shared ``config.json`` that contains
formats, routes and metadata sections.  Every module accesses it
via ``ProjectConfig.instance()``.

Typical usage — CLI entry point::

    config = ProjectConfig.instance(logger=logger, config_path=args.config)

Typical usage — library code::

    config = ProjectConfig.instance()
    routes = config.routes

Testing::

    ProjectConfig.instance(data=DEFAULT_CONFIG)
    # ... singleton is now available
"""

import json
from pathlib import Path
from typing import Any, Optional

from common.config_utils import get_config_dir, ensure_config_exists, get_template_path
from common.constants import DEFAULT_CONFIG


class ProjectConfig:
    """Singleton holder for the unified project configuration.

    The configuration is stored in ``config.json`` inside the standard
    config directory (``%APPDATA%/florentine-abbot`` on Windows,
    ``~/.config/florentine-abbot`` on Linux).

    Sections:

    * **formats** — ``source_filename_template``, ``archive_path_template``,
      ``archive_filename_template``
    * **routes** — ``rules`` list of ``[glob_pattern, subfolder]``
    * **metadata** — ``tags`` mapping + ``languages`` dict with per-language values
    """

    _instance: Optional["ProjectConfig"] = None

    def __init__(self, *, logger: Any = None, data: dict[str, Any]) -> None:
        """Private — use :meth:`instance`.

        Args:
            logger: Optional logger.
            data: Parsed JSON content of ``config.json``.
        """
        self._logger = logger
        self._data: dict[str, Any] = data

    @classmethod
    def instance(
        cls,
        *,
        logger: Any = None,
        config_path: str | Path | None = None,
        data: dict[str, Any] | None = None,
    ) -> "ProjectConfig":
        """Return the singleton, creating or replacing it when arguments are given.

        When called **with** ``data`` or ``config_path`` the singleton is
        (re-)created.  When called **without** arguments the existing
        singleton is returned.

        Args:
            logger: Logger for diagnostics.
            config_path: Explicit path to ``config.json``.
            data: If supplied, used directly (no file I/O) — handy for tests.

        Returns:
            The :class:`ProjectConfig` singleton.

        Raises:
            RuntimeError: If called without arguments before the singleton
                has been created.
        """
        if data is not None or config_path is not None:
            return cls._initialize(logger=logger, config_path=config_path, data=data)

        if cls._instance is None:
            raise RuntimeError(
                "ProjectConfig has not been initialized. "
                "Call ProjectConfig.instance(data=...) or "
                "ProjectConfig.instance(config_path=...) first."
            )
        return cls._instance

    @classmethod
    def _initialize(
        cls,
        *,
        logger: Any = None,
        config_path: str | Path | None = None,
        data: dict[str, Any] | None = None,
    ) -> "ProjectConfig":
        """Create (or replace) the singleton."""
        if data is not None:
            cls._instance = cls(logger=logger, data=data)
            return cls._instance

        path = Path(config_path) if config_path else cls._default_path()

        # Ensure config file exists, creating from template if needed
        template_path = get_template_path("common", "config.template.json")
        ensure_config_exists(logger, path, DEFAULT_CONFIG, template_path)

        loaded = cls._load(path, logger)
        cls._instance = cls(logger=logger, data=loaded)
        return cls._instance

    @property
    def formats(self) -> dict[str, Any]:
        """The ``formats`` section (templates for parsing / formatting)."""
        return self._data.get("formats", {})

    @property
    def routes(self) -> dict[str, Any]:
        """The ``routes`` section (routing rules)."""
        return self._data.get("routes", {})

    @property
    def metadata(self) -> dict[str, Any]:
        """The ``metadata`` section (tags mapping + languages)."""
        return self._data.get("metadata", {})

    @property
    def data(self) -> dict[str, Any]:
        """Full raw config dict (read-only intent)."""
        return self._data

    @classmethod
    def _default_path(cls) -> Path:
        return get_config_dir() / "config.json"

    @staticmethod
    def _load(path: Path, logger: Any) -> dict[str, Any]:
        """Load and return parsed JSON from *path*."""
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if logger:
                logger.info(f"Loaded project config from {path}")
            return data
        except FileNotFoundError:
            if logger:
                logger.warning(
                    f"Config not found at {path}, using defaults"
                )
            return DEFAULT_CONFIG
        except json.JSONDecodeError as exc:
            if logger:
                logger.error(
                    f"Invalid JSON in {path}: {exc}, using defaults"
                )
            return DEFAULT_CONFIG
        except Exception as exc:
            if logger:
                logger.error(
                    f"Error loading {path}: {exc}, using defaults"
                )
            return DEFAULT_CONFIG
