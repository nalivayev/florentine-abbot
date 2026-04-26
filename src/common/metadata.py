"""Reusable semantic metadata profiles and image-tag projection.

The metadata config intentionally stores user-facing semantic fields grouped
by language. Concrete EXIF/XMP tag mapping stays in code.
"""

from copy import deepcopy
from typing import Any, Optional, cast

from common.constants import TAG_XMP_DC_CREATOR, TAG_XMP_DC_DESCRIPTION, TAG_XMP_DC_RIGHTS, TAG_XMP_DC_SOURCE, TAG_XMP_PHOTOSHOP_CREDIT, TAG_XMP_XMPRIGHTS_MARKED, TAG_XMP_XMPRIGHTS_USAGE_TERMS
from common.logger import Logger


IMAGE_METADATA_TAGS: dict[str, str] = {
    "description": TAG_XMP_DC_DESCRIPTION,
    "creator": TAG_XMP_DC_CREATOR,
    "rights": TAG_XMP_DC_RIGHTS,
    "source": TAG_XMP_DC_SOURCE,
    "credit": TAG_XMP_PHOTOSHOP_CREDIT,
    "terms": TAG_XMP_XMPRIGHTS_USAGE_TERMS,
    "marked": TAG_XMP_XMPRIGHTS_MARKED,
}

IMAGE_MULTILINGUAL_FIELDS: set[str] = {
    "description",
    "rights",
    "terms",
}

DEFAULT_METADATA_CONFIG: dict[str, Any] = {
    "help": [
        "Reusable metadata defaults for import and post-import workflows.",
        "",
        "languages: BCP-47 language codes like 'ru-RU' or 'en-US'.",
        "Exactly one language SHOULD have 'default': true.",
        "",
        "Fields:",
        "  description, creator, rights, source, credit, terms, marked",
        "",
        "Values may be strings or arrays of strings.",
        "For creator, newline-separated text in the UI is normalized to a list.",
    ],
    "languages": {
        "ru-RU": {
            "default": True,
            "description": "",
            "creator": [],
            "rights": "",
            "source": "",
            "credit": "",
            "terms": "",
            "marked": "",
        },
        "en-US": {
            "description": "",
            "creator": [],
            "rights": "",
            "source": "",
            "credit": "",
            "terms": "",
            "marked": "",
        },
    },
}


class ArchiveMetadata:
    """Semantic metadata provider with code-owned tag mapping rules."""

    def __init__(
        self,
        metadata: Optional[dict[str, Any]] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        self._logger = logger
        section = deepcopy(metadata) if metadata is not None else deepcopy(DEFAULT_METADATA_CONFIG)
        self._legacy_tags: dict[str, str] = {
            key: value
            for key, value in section.get("tags", {}).items()
            if key != "help" and isinstance(value, str)
        }
        self._languages: dict[str, dict[str, Any]] = {}
        raw_languages = section.get("languages", {})
        if isinstance(raw_languages, dict):
            for lang_code, block in cast(dict[Any, Any], raw_languages).items():
                if isinstance(block, dict):
                    block_dict = cast(dict[Any, Any], block)
                    self._languages[str(lang_code)] = {
                        str(key): value for key, value in block_dict.items()
                    }

    def get_configurable_tags(self, tag_mapping: Optional[dict[str, str]] = None) -> list[str]:
        """Return concrete tag names for the current target mapping."""
        mapping = tag_mapping or self._legacy_tags or IMAGE_METADATA_TAGS
        return list(mapping.values())

    def get_default_language_values(self) -> dict[str, Any]:
        """Return normalized semantic field values for the default language block."""
        default_language = self._get_default_language()
        if default_language is None:
            return {}

        block = self._languages.get(default_language)
        if not isinstance(block, dict):
            return {}

        fields = list((self._legacy_tags or IMAGE_METADATA_TAGS).keys())
        values: dict[str, Any] = {}
        for field_name in fields:
            normalized = self._normalize_field(field_name, block.get(field_name))
            if normalized:
                values[field_name] = normalized
        return values

    def get_metadata_values(
        self,
        *,
        tag_mapping: Optional[dict[str, str]] = None,
        multilingual_fields: Optional[set[str]] = None,
        logger: Optional[Logger] = None,
    ) -> dict[str, Any]:
        """Project semantic fields into concrete metadata tags.

        By default this returns the image/XMP projection used by import flows.
        Fields whose target tags do not support language alternatives are written
        from the default language block only.
        """
        tags: dict[str, Any] = {}

        if not self._languages:
            if logger:
                logger.debug("No languages in metadata config; skipping")
            return tags

        mapping = tag_mapping or self._legacy_tags or IMAGE_METADATA_TAGS
        multi_fields = IMAGE_MULTILINGUAL_FIELDS if multilingual_fields is None else multilingual_fields
        default_language = self._get_default_language()
        if default_language is None:
            return tags

        for lang_code, block in self._languages.items():
            for field_name, tag_base in mapping.items():
                normalized = self._normalize_field(field_name, block.get(field_name))
                if not normalized:
                    continue

                if field_name in multi_fields:
                    tags[f"{tag_base}-{lang_code}"] = normalized
                    if lang_code == default_language:
                        tags[tag_base] = normalized
                elif lang_code == default_language:
                    tags[tag_base] = normalized

        return tags

    def _get_default_language(self) -> Optional[str]:
        for lang_code, block in self._languages.items():
            if block.get("default"):
                return lang_code

        for lang_code in self._languages:
            return lang_code

        return None

    def _normalize_field(self, field_name: str, value: Any) -> Optional[Any]:
        if field_name == "creator":
            return self._normalize_creator(value)
        return self._normalize_text(value)

    def _normalize_creator(self, value: Any) -> Optional[list[str]]:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = [line.strip() for line in value.splitlines() if line.strip()]
            return normalized or None
        if isinstance(value, list):
            items = cast(list[Any], value)
            normalized = [str(item).strip() for item in items if str(item).strip()]
            return normalized or None
        normalized = str(value).strip()
        return [normalized] if normalized else None

    def _normalize_text(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, bool):
            return "True" if value else "False"
        if isinstance(value, list):
            items = cast(list[Any], value)
            joined = "\n".join(str(item) for item in items if str(item).strip())
            return joined or None
        if isinstance(value, str):
            return value or None
        return str(value)
