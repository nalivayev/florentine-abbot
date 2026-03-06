"""Shared archival metadata configuration provider.

This module provides :class:`ArchiveMetadata` which is a thin configuration
provider for metadata tags and values.  It receives the ``metadata`` section
(from :class:`~common.project_config.ProjectConfig`) and provides methods
to retrieve tag lists and values.

Actual reading/writing of metadata is done by individual components
(FileProcessor, PreviewMaker) using :class:`~common.tagger.Tagger`.
"""

from typing import Any, Optional

from common.constants import DEFAULT_METADATA
from common.logger import Logger


class ArchiveMetadata:
    """
    Thin configuration provider for archival metadata.

    Provides methods to retrieve:
        - List of configurable tags (for reading/copying)
        - Dictionary of tag values with language variants (for writing)

    Actual reading/writing of metadata is done by individual components
    using :class:`~common.tagger.Tagger`.
    """

    def __init__(
        self,
        metadata: Optional[dict[str, Any]] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        """
        Initialize ArchiveMetadata configuration provider.

        Args:
            metadata: The ``metadata`` section from :class:`ProjectConfig`.
                Contains ``tags`` (field→XMP mapping) and ``languages``
                (per-language values).  Falls back to :data:`DEFAULT_METADATA`
                when *None*.
            logger: Logger for debug output.
        """
        self._logger = logger
        section = metadata if metadata is not None else DEFAULT_METADATA
        self._tags: dict[str, str] = {
            k: v for k, v in section.get("tags", {}).items()
            if k != "help" and isinstance(v, str)
        }
        self._languages: dict[str, Any] = section.get("languages", {})

    def _normalize_text(self, value: Any) -> Optional[str]:
        """
        Normalize a config text field to a single string.

        Supports both scalar strings and lists of strings. Lists are joined with newlines so that multi-line / bilingual values end up in a single XMP field. Empty values result in None.

        Args:
            value (Any): The value to normalize (str, list, or None).
        Returns:
            Optional[str]: Normalized string or None if empty.
        """
        if value is None:
            return None
        if isinstance(value, list):
            joined = "\n".join(str(item) for item in value if item)
            return joined or None
        if isinstance(value, str):
            return value or None
        return str(value)

    def get_configurable_tags(self) -> list[str]:
        """Return list of XMP tags for reading/copying."""
        return list(self._tags.values())

    def get_metadata_values(self, logger: Optional[Logger] = None) -> dict[str, Any]:
        """
        Return dictionary of tag -> value with language variants from metadata.json.

        Processes the metadata.json configuration and returns a flat dictionary with all tags and their values, including language-specific variants.

        Args:
            logger (Optional[Logger]): Logger for debug messages.
        Returns:
            dict[str, Any]: Dictionary like:
                {
                    "XMP-dc:Description": "Описание",
                    "XMP-dc:Description-ru-RU": "Описание",
                    "XMP-dc:Description-en-US": "Description",
                    "XMP-dc:Creator": ["Автор"],
                    ...
                }
        """
        tags: dict[str, Any] = {}

        if not self._languages:
            if logger:
                logger.debug("No languages in metadata config; skipping")
            return tags

        # Choose default language block (first with default=True, else first)
        default_block: Optional[dict[str, Any]] = None
        for lang_code, block in self._languages.items():
            if isinstance(block, dict) and block.get("default"):
                default_block = block
                break

        if default_block is None:
            _, default_block = next(iter(self._languages.items()))

        for lang_code, block in self._languages.items():
            if not isinstance(block, dict):
                continue

            for field_name, tag_base in self._tags.items():
                raw_value = block.get(field_name)

                # Special handling for Creator: must be a list
                if field_name == "creator":
                    if raw_value is None:
                        continue
                    if isinstance(raw_value, str):
                        normalized = [raw_value] if raw_value else None
                    elif isinstance(raw_value, list):
                        normalized = [str(item) for item in raw_value if item]
                        if not normalized:
                            normalized = None
                    else:
                        normalized = [str(raw_value)]
                else:
                    normalized = self._normalize_text(raw_value)

                if not normalized:
                    continue

                # Language-specific variant (TAG-langCode)
                lang_tag = f"{tag_base}-{lang_code}"
                tags[lang_tag] = normalized

                # Default/plain variant for the chosen default language
                if block is default_block:
                    tags[tag_base] = normalized

        return tags
