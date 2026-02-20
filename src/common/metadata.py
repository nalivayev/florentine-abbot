"""Shared archival metadata configuration provider.

This module provides :class:`ArchiveMetadata` which is a thin configuration
provider for metadata tags and values. It loads tags.json and metadata.json
and provides methods to retrieve tag lists and values.

Actual reading/writing of metadata is done by individual components
(FileProcessor, PreviewMaker) using :class:`~common.tagger.Tagger`.
"""

from typing import Any, Optional

from common.constants import DEFAULT_TAGS, DEFAULT_METADATA
from common.logger import Logger
from common.config_utils import get_config_dir, load_optional_config, ensure_config_exists, get_template_path


class ArchiveMetadata:
    """
    Thin configuration provider for archival metadata.

    Loads tags.json and metadata.json and provides methods to retrieve:
        - List of configurable tags (for reading/copying)
        - Dictionary of tag values with language variants (for writing)

    Actual reading/writing of metadata is done by individual components
    using :class:`~common.tagger.Tagger`.
    """

    def __init__(self, logger: Optional[Logger] = None) -> None:
        """
        Initialize ArchiveMetadata configuration provider.

        Args:
            logger (Optional[Logger]): Logger for config loading/debug output.
        """
        self._logger: Optional[Logger] = logger

        # Load tags mapping (field names -> XMP tag names)
        tags_path = get_config_dir() / "tags.json"
        self._metadata_tags: dict[str, str] = load_optional_config(self._logger, tags_path, DEFAULT_TAGS)

        # Ensure metadata.json exists, create from template if needed
        metadata_path = get_config_dir() / "metadata.json"
        template_path = get_template_path('common', 'metadata.template.json')
        ensure_config_exists(self._logger, metadata_path, DEFAULT_METADATA, template_path)

        # Load metadata configuration (languages and their values)
        self._metadata_config: dict[str, Any] = load_optional_config(self._logger, metadata_path, DEFAULT_METADATA)

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
        """
        Return list of XMP tags from tags.json for reading/copying.

        Returns:
            list[str]: List of tag names like ["XMP-dc:Description", ...]
        """
        if self._metadata_tags is None:
            return list(DEFAULT_TAGS.values())
        # Filter out _comment key and any non-string values
        return [v for k, v in self._metadata_tags.items() if k != "_comment" and isinstance(v, str)]

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

        if self._metadata_config is None or not isinstance(self._metadata_config, dict):
            if logger:
                logger.debug("No metadata config; skipping configurable metadata fields")
            return tags

        if "languages" not in self._metadata_config:
            if logger:
                logger.debug("No 'languages' in metadata config; skipping configurable metadata fields")
            return tags

        languages = self._metadata_config["languages"]
        if not isinstance(languages, dict) or not languages:
            if logger:
                logger.warning("Config 'languages' is empty or invalid; skipping configurable metadata fields")
            return tags

        # Choose default language block (first with default=True, else first in mapping)
        default_block: Optional[dict[str, Any]] = None
        for lang_code, block in languages.items():
            if isinstance(block, dict) and block.get("default"):
                default_block = block
                break

        if default_block is None:
            # Fallback: pick the first language deterministically
            _, default_block = next(iter(languages.items()))

        # Use provided metadata tags mapping, or fall back to defaults
        text_field_map = self._metadata_tags if self._metadata_tags is not None else DEFAULT_TAGS

        for lang_code, block in languages.items():
            if not isinstance(block, dict):
                continue

            for field_name, tag_base in text_field_map.items():
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
