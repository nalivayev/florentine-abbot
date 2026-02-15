"""File routing logic for organizing files in the archive structure.

This module provides the Router class that determines target folders
for files based on parsed filename data and routing configuration.
Used by both file-organizer and preview-maker.
"""

from pathlib import Path
from typing import Optional

from common.naming import ParsedFilename
from common.constants import DEFAULT_SUFFIX_ROUTING
from common.formatter import Formatter
from common.config_utils import get_config_dir, load_optional_config


class Router:
    """
    Determines target folders for files based on routing rules.

    Uses suffix-based routing rules and configurable path templates to determine where files should be placed in the archive structure.

    Archive structure (configurable via Formatter):
        Default: archive_root/{year:04d}/{year:04d}.{month:02d}.{day:02d}/
            ├── SOURCES/      - Raw scans and master files
            ├── DERIVATIVES/  - Processed derivatives
            └── (date folder)  - Preview files stored directly here

    Path structure can be customized via formats.json:
        - Flat: {year:04d}.{month:02d}.{day:02d}/
        - By month: {year:04d}/{year:04d}.{month:02d}/
        - By group: {group}/{year:04d}/{year:04d}.{month:02d}.{day:02d}/

    Routing is configured via a suffix mapping (suffix -> subfolder):
        - "SOURCES": File goes to SOURCES/ subfolder
        - "DERIVATIVES": File goes to DERIVATIVES/ subfolder
        - ".": File goes directly to date folder root
    """
    
    def __init__(self, suffix_routing: Optional[dict[str, str]] = None, logger = None) -> None:
        """
        Initialize Router.

        Args:
            suffix_routing (dict[str, str]|None): Optional suffix routing rules (suffix -> 'SOURCES'/'DERIVATIVES'/'.').
                If None, loads from routes.json or uses DEFAULT_SUFFIX_ROUTING.
            logger: Optional logger for diagnostic messages.
        """
        self._logger = logger
        self._formatter = Formatter(logger=logger)

        if suffix_routing is not None:
            self._suffix_routing = suffix_routing
        else:
            # Load from routes.json if available
            config_dir = get_config_dir()
            routes_path = config_dir / "routes.json"
            self._suffix_routing = load_optional_config(logger, routes_path, DEFAULT_SUFFIX_ROUTING)
    
    def get_target_folder(self, parsed: ParsedFilename, base_path: Path) -> Path:
        """
        Determine target folder for a file based on parsed filename.

        Uses Formatter to build path from template, then applies suffix routing to determine subfolder (SOURCES/DERIVATIVES/date root).

        Args:
            parsed (ParsedFilename): Parsed filename data.
            base_path (Path): Base path (e.g., archive root or processed root).

        Returns:
            Path: Full path to target folder where file should be placed (e.g., base_path/2024/2024.03.15/SOURCES or custom structure).
        """
        formatted_path = self._formatter.format_path(parsed)
        suffix_upper = parsed.suffix.upper()
        date_root_dir = base_path / formatted_path
        subfolder = self._suffix_routing.get(suffix_upper, self._suffix_routing.get("*", "DERIVATIVES"))
        if subfolder == ".":
            return date_root_dir
        else:
            return date_root_dir / subfolder
    
    def get_normalized_filename(self, parsed: ParsedFilename) -> str:
        """
        Format filename according to configured template.

        Uses Formatter to apply filename template with format specifiers (e.g., {year:04d}.{month:02d}.{day:02d}... or custom format).

        Args:
            parsed (ParsedFilename): Parsed filename data.

        Returns:
            str: Formatted filename (without extension).
        """
        return self._formatter.format_filename(parsed)
    
    def get_folders_for_suffixes(self, suffixes: list[str]) -> set[str]:
        """
        Get unique folder names where files with given suffixes are stored.

        Args:
            suffixes (list[str]): List of file suffixes (e.g., ['RAW', 'MSR']).

        Returns:
            set[str]: Set of folder names (e.g., {'SOURCES', 'MASTERS'}). '.' is excluded as it represents date root, not a subfolder.
        """
        folders = set()
        for suffix in suffixes:
            suffix_upper = suffix.upper()
            folder = self._suffix_routing.get(suffix_upper, self._suffix_routing.get("*", "DERIVATIVES"))
            if folder != ".":  # Exclude date root
                folders.add(folder)
        return folders
