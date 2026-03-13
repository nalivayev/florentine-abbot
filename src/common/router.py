"""File routing logic for organizing files in the archive structure.

This module provides the Router class that determines target folders
for files based on glob-pattern rules and configurable path templates.
Used by both file-organizer and preview-maker.
"""

import fnmatch
from pathlib import Path
from typing import Any, Optional

from common.formatter import ParsedFilename, Formatter
from common.logger import Logger
from common.constants import DEFAULT_ROUTES


class Router:
    """Determines target folders for files based on pattern-based routing rules.

    Archive structure (configurable via Formatter):
        Default: archive_root/{year:04d}/{year:04d}.{month:02d}.{day:02d}/
            ├── SOURCES/      - Raw scans and master files
            ├── DERIVATIVES/  - Processed derivatives
            └── (date folder)  - Preview files stored directly here

    Routing is configured via an ordered list of
    ``[glob_pattern, subfolder, protect?]`` rules.  Each filename is tested
    against the patterns in order; the first match determines the subfolder.
    The optional third element *protect* (default ``False``) indicates whether
    the destination file should be made read-only after placement:

    - ``"SOURCES"`` → ``date_folder/SOURCES/``
    - ``"."`` → ``date_folder/`` (date root)
    - ``"DERIVATIVES"`` → ``date_folder/DERIVATIVES/``

    Patterns use standard ``fnmatch`` syntax (``*``, ``?``, ``[seq]``).
    Matching is **case-insensitive**.
    """

    def __init__(
        self,
        routes: Optional[dict[str, Any]] = None,
        logger: Logger | None = None,
        formats: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize Router.

        Args:
            routes: The ``routes`` section from :class:`ProjectConfig`.
                If *None*, uses :data:`DEFAULT_ROUTES`.
            logger: Optional logger for diagnostic messages.
            formats: ``formats`` section from :class:`ProjectConfig`,
                forwarded to :class:`Formatter`.
        """
        self._logger = logger
        self._formatter = Formatter(logger=logger, formats=formats)
        section = routes if routes is not None else DEFAULT_ROUTES
        self._routes: list[list[Any]] = section.get("rules", [])

    def get_target_folder(
        self, parsed: ParsedFilename, base_path: Path, filename: str | None = None,
    ) -> tuple[Path, bool]:
        """Determine target folder for a file.

        Builds the date-based path from *parsed* via :class:`Formatter`,
        then matches *filename* against routing rules to pick a subfolder.

        When *filename* is not supplied it is reconstructed from *parsed*
        using the archive filename template + extension.

        Args:
            parsed: Parsed filename data (used for date path).
            base_path: Archive root or processed root.
            filename: Original filename for pattern matching.  Optional —
                if omitted, derived from *parsed*.

        Returns:
            Tuple of (target_folder_path, protect_flag).
        """
        formatted_path = self._formatter.format_path(parsed)
        date_root_dir = base_path / formatted_path

        if filename is None:
            filename = self._formatter.format_filename(parsed) + f".{parsed.extension}"

        subfolder, protect = self._match_route(filename)
        if subfolder == ".":
            return date_root_dir, protect
        return date_root_dir / subfolder, protect

    def get_normalized_filename(self, parsed: ParsedFilename) -> str:
        """Format filename according to the configured archive template.

        Args:
            parsed: Parsed filename data.

        Returns:
            Formatted filename **without** extension.
        """
        return self._formatter.format_filename(parsed)

    def get_folders_for_patterns(self, patterns: list[str]) -> set[str]:
        """Get unique subfolder names assigned to the given patterns.

        For each *pattern* the routing table is scanned for the **first**
        rule whose glob also matches a hypothetical filename satisfying
        *pattern*.  Because exact intersection of globs is non-trivial,
        this implementation simply returns the subfolder directly
        associated with each supplied pattern (looked up literally in the
        routing table).  If the pattern is not found, the fallback rule
        (last entry, typically ``"*"``) is used.

        ``"."`` entries are excluded because they represent the date root,
        not a named subfolder.

        Args:
            patterns: List of glob patterns (e.g. ``["*.MSR.*", "*.RAW.*"]``).

        Returns:
            Set of subfolder names.
        """
        folders: set[str] = set()
        for pattern in patterns:
            # Direct lookup: find the route whose pattern matches ours.
            for rule in self._routes:
                if rule[0] == pattern:
                    if rule[1] != ".":
                        folders.add(rule[1])
                    break
            else:
                # Fallback: last route (catch-all).
                if self._routes:
                    last_subfolder = self._routes[-1][1]
                    if last_subfolder != ".":
                        folders.add(last_subfolder)
        return folders

    def _match_route(self, filename: str) -> tuple[str, bool]:
        """Return ``(subfolder, protect)`` for the first matching route.

        The *protect* flag is the optional third element of the rule
        (defaults to ``False``).

        Raises:
            ValueError: If no rule matches — indicates a missing catch-all
                (e.g. ``["*", "DERIVATIVES"]``) in the routing configuration.
        """
        filename_lower = filename.lower()
        for rule in self._routes:
            if fnmatch.fnmatch(filename_lower, rule[0].lower()):
                protect = rule[2] if len(rule) > 2 else False
                return rule[1], protect
        raise ValueError(
            f"No routing rule matched '{filename}'. "
            f"Add a catch-all rule like [\"*\", \"DERIVATIVES\"] to your routes."
        )
