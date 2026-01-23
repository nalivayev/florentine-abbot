"""Shared archival metadata policy built on top of Exifer.

This module centralizes the list of EXIF/XMP tags used by the
File Organizer and Preview Maker workflows and provides
high-level helpers for writing metadata to master files and
preview (PRV) derivatives.
"""

import uuid
from pathlib import Path
from typing import Any, Optional

from common.constants import EXIFTOOL_LARGE_FILE_TIMEOUT, DEFAULT_METADATA_TAGS
from common.exifer import Exifer
from common.logger import Logger


class ArchiveMetadata:
    """High-level archival metadata helper built on top of Exifer.

    This class knows *which* tags we use in the archive and *how* to
    populate them for master files and PRV derivatives. Lower-level
    interaction with exiftool is delegated to :class:`Exifer`.
    """

    # Tag names (shared across organizer and preview maker)
    TAG_XMP_EXIF_DATETIME_DIGITIZED = "XMP-exif:DateTimeDigitized"
    TAG_EXIFIFD_DATETIME_DIGITIZED = "ExifIFD:DateTimeDigitized"
    TAG_EXIFIFD_CREATE_DATE = "ExifIFD:CreateDate"
    TAG_EXIF_DATETIME_ORIGINAL = "Exif:DateTimeOriginal"
    TAG_XMP_PHOTOSHOP_DATE_CREATED = "XMP-photoshop:DateCreated"
    TAG_XMP_XMP_IDENTIFIER = "XMP-xmp:Identifier"  # XMP-xmp:Identifier
    TAG_XMP_DC_IDENTIFIER = "XMP-dc:Identifier"    # XMP-dc:Identifier
    TAG_XMP_DC_DESCRIPTION = "XMP-dc:Description"
    TAG_XMP_DC_TITLE = "XMP-dc:Title"
    TAG_XMP_DC_CREATOR = "XMP-dc:Creator"
    TAG_XMP_PHOTOSHOP_CREDIT = "XMP-photoshop:Credit"
    TAG_XMP_DC_RIGHTS = "XMP-dc:Rights"
    TAG_XMP_XMPRIGHTS_USAGE_TERMS = "XMP-xmpRights:UsageTerms"
    TAG_XMP_DC_SOURCE = "XMP-dc:Source"
    TAG_XMP_DC_RELATION = "XMP-dc:Relation"

    # Groupings for easier reuse
    IDENTIFIER_TAGS = (TAG_XMP_DC_IDENTIFIER, TAG_XMP_XMP_IDENTIFIER)
    CONTEXT_TAGS = (
        TAG_XMP_DC_DESCRIPTION,
        TAG_XMP_DC_TITLE,
        TAG_XMP_DC_CREATOR,
        TAG_XMP_PHOTOSHOP_CREDIT,
        TAG_XMP_DC_RIGHTS,
        TAG_XMP_XMPRIGHTS_USAGE_TERMS,
        TAG_XMP_DC_SOURCE,
    )
    DATE_TAGS = (
        TAG_EXIF_DATETIME_ORIGINAL,
        TAG_XMP_PHOTOSHOP_DATE_CREATED,
        TAG_XMP_EXIF_DATETIME_DIGITIZED,
    )

    def __init__(self, exifer: Optional[Exifer] = None, metadata_tags: Optional[dict[str, str]] = None) -> None:
        """Initialize ArchiveMetadata.
        
        Args:
            exifer: Optional Exifer instance for EXIF operations.
            metadata_tags: Optional mapping of field names to XMP tag names.
                          If None, will use DEFAULT_METADATA_TAGS from constants.
        """
        self._exifer = exifer or Exifer()
        self._metadata_tags = metadata_tags

    @classmethod
    def _get_master_tags(cls) -> list[str]:
        """Tags that may be read from the source before writing master.

        Used primarily to derive XMP-exif:DateTimeDigitized from
        existing EXIFIFD:CreateDate / DateTimeDigitized.
        """

        return [
            cls.TAG_XMP_EXIF_DATETIME_DIGITIZED,
            cls.TAG_EXIFIFD_DATETIME_DIGITIZED,
            cls.TAG_EXIFIFD_CREATE_DATE,
        ]

    @classmethod
    def _get_derivative_tags(cls) -> list[str]:
        """Tags that should be read from the master before writing PRV."""

        # Also include EXIFIFD DateTimeDigitized as a fallback source for
        # XMP-exif:DateTimeDigitized.
        return list(cls.IDENTIFIER_TAGS + cls.CONTEXT_TAGS + cls.DATE_TAGS) + [
            cls.TAG_EXIFIFD_DATETIME_DIGITIZED,
        ]

    def write_master_tags(
        self,
        *,
        file_path: Path,
        parsed: Any,
        config: dict[str, Any] | None,
        logger: Logger,
    ) -> None:
        """Write EXIF/XMP metadata for a master/derivative file.

        This implements the same policy that :class:`FileProcessor`
        previously carried inline:

        - generate UUID identifiers
        - write human-readable description and title
        - derive DateTimeDigitized from existing CreateDate if needed
        - encode DateTimeOriginal / DateCreated from parsed filename
        - apply configurable fields (creator, rights, etc.) if config provided
        
        Args:
            file_path: Path to the file to tag.
            parsed: Parsed filename data.
            config: Metadata configuration dict (with 'languages' key), or None to skip configurable fields.
            logger: Logger instance.
        """

        tags: dict[str, Any] = {}

        # 1. Identifiers (XMP)
        file_uuid = str(uuid.uuid4())
        tags[self.TAG_XMP_DC_IDENTIFIER] = file_uuid
        tags[self.TAG_XMP_XMP_IDENTIFIER] = file_uuid

        def _normalize_text(value: Any) -> Optional[str]:
            """Normalize config text field to a single string.

            Supports both scalar strings and lists of strings. Lists are
            joined with newlines so that multi-line / bilingual values end up
            in a single XMP field. Empty values result in None.
            """

            if value is None:
                return None

            if isinstance(value, list):
                joined = "\n".join(str(item) for item in value if item)
                return joined or None

            if isinstance(value, str):
                return value or None

            return str(value)

        # 2. Title (description is handled in configurable fields section
        # to support per-language values and x-default mapping).
        tags[self.TAG_XMP_DC_TITLE] = file_path.stem

        # 3. Dates
        # 3.1 DateTimeDigitized - preserve scanning date from CreateDate
        try:
            existing_tags = self._exifer.read(
                file_path,
                self._get_master_tags(),
            )

            date_digitized = (
                existing_tags.get(self.TAG_XMP_EXIF_DATETIME_DIGITIZED)
                or existing_tags.get(self.TAG_EXIFIFD_DATETIME_DIGITIZED)
            )

            if not date_digitized:
                create_date = existing_tags.get(self.TAG_EXIFIFD_CREATE_DATE)
                if create_date:
                    tags[self.TAG_XMP_EXIF_DATETIME_DIGITIZED] = create_date
                    logger.debug("Set DateTimeDigitized from CreateDate: %s", create_date)
            else:
                logger.debug("DateTimeDigitized already set: %s", date_digitized)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Could not process DateTimeDigitized: %s", exc)

        # 3.2 DateTimeOriginal - date from filename (original photo date)
        if parsed.modifier == "E":
            dt_str = (
                f"{parsed.year:04d}:{parsed.month:02d}:{parsed.day:02d} "
                f"{parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d}"
            )
            tags[self.TAG_EXIF_DATETIME_ORIGINAL] = dt_str
            tags[self.TAG_XMP_PHOTOSHOP_DATE_CREATED] = dt_str.replace(":", "-", 2).replace(" ", "T")
        else:
            # Partial date: clear EXIF DateTimeOriginal and encode partial
            # date in XMP-photoshop:DateCreated.
            tags[self.TAG_EXIF_DATETIME_ORIGINAL] = ""

            if parsed.year > 0:
                date_val = f"{parsed.year:04d}"
                if parsed.month > 0:
                    date_val += f"-{parsed.month:02d}"
                    if parsed.day > 0:
                        date_val += f"-{parsed.day:02d}"

                tags[self.TAG_XMP_PHOTOSHOP_DATE_CREATED] = date_val

        # 4. Configurable fields (new multi-language configuration only)
        #
        # Config is expected to contain a "languages" mapping where each key
        # is a BCP-47 language code (e.g. "ru-RU", "en-US"), and each value
        # is a dict with optional fields: creator, credit, description,
        # rights, terms, source. One language may be marked with
        # "default": true to indicate which value should become x-default /
        # plain XMP tag.
        #
        # If config is None or does not contain 'languages', skip writing
        # configurable metadata fields entirely.

        if config is None or not isinstance(config, dict) or "languages" not in config:
            logger.debug("No 'languages' in config; skipping configurable metadata fields (creator, rights, etc.)")
        else:
            languages = config["languages"]
            if not isinstance(languages, dict) or not languages:
                logger.warning("Config 'languages' is empty or invalid; skipping configurable metadata fields")
            else:
                # Choose default language block (first with default=True, else fall
                # back to the first language in the mapping for stability).
                default_lang_code: Optional[str] = None
                default_block: Optional[dict[str, Any]] = None
                for lang_code, block in languages.items():
                    if isinstance(block, dict) and block.get("default"):
                        default_lang_code = lang_code
                        default_block = block
                        break

                if default_block is None:
                    # Fallback: pick the first language deterministically
                    default_lang_code, default_block = next(iter(languages.items()))

                # Creator is not LangAlt in XMP – it is a bag of names. We take it
                # from the default language block (if present) and encode it once, as
                # a list of authors.
                if isinstance(default_block, dict):
                    creator_value = default_block.get("creator")
                    if creator_value:
                        tags[self.TAG_XMP_DC_CREATOR] = creator_value if isinstance(creator_value, list) else [creator_value]

                # Language-aware text fields. For each language we write TAG-langCode,
                # and for the default language we also write the plain TAG (which
                # exiftool maps to x-default for LangAlt tags).
                #
                # Note: Only some XMP tags support LangAlt (language alternatives):
                # - Description, Rights, UsageTerms, Title: support language variants
                # - Credit, Source, Creator: do NOT support language variants (write only plain tag)
                
                # Use provided metadata tags mapping, or fall back to defaults
                text_field_map = self._metadata_tags if self._metadata_tags is not None else DEFAULT_METADATA_TAGS

                for lang_code, block in languages.items():
                    if not isinstance(block, dict):
                        continue

                    for field_name, tag_base in text_field_map.items():
                        raw_value = block.get(field_name)
                        normalized = _normalize_text(raw_value)
                        if not normalized:
                            continue

                        # Try to write language-specific variant
                        # Exiftool will warn if tag doesn't support it, but that's OK
                        # We write it for LangAlt tags, exiftool ignores for non-LangAlt
                        lang_tag = f"{tag_base}-{lang_code}"
                        tags[lang_tag] = normalized

                        # Default/plain variant for the chosen default language
                        if block is default_block:
                            tags[tag_base] = normalized

        # Log file size for large files (useful for performance tracking)
        file_size = file_path.stat().st_size
        if file_size > 100 * 1024 * 1024:  # > 100MB
            logger.info(
                "Running exiftool on large file (%.1f MB): %s",
                file_size / (1024**2),
                file_path.name,
            )
            # Use timeout for large files to prevent hanging
            self._exifer.write(file_path, tags, timeout=EXIFTOOL_LARGE_FILE_TIMEOUT)
        else:
            logger.info("Running exiftool on %s...", file_path.name)
            self._exifer.write(file_path, tags)
        
        logger.info("  Metadata written successfully.")

    def write_derivative_tags(
        self,
        *,
        master_path: Path,
        prv_path: Path,
        logger: Optional[Logger] = None,
    ) -> None:
        """Write EXIF/XMP metadata for a PRV derivative based on master.

        The PRV receives its own identifier while inheriting descriptive
        context (dates, description, authorship, rights, etc.) from the
        master MSR/RAW file. A relation back to the master identifier is
        also recorded.
        """

        existing = self._exifer.read(
            master_path,
            self._get_derivative_tags(),
        )

        tags_to_write: dict[str, Any] = {}

        # Fresh identifier for PRV
        file_uuid = str(uuid.uuid4())
        tags_to_write[self.TAG_XMP_DC_IDENTIFIER] = file_uuid
        tags_to_write[self.TAG_XMP_XMP_IDENTIFIER] = file_uuid

        # Link back to master identifier if present
        master_id = existing.get(self.TAG_XMP_DC_IDENTIFIER) or existing.get(self.TAG_XMP_XMP_IDENTIFIER)
        if master_id:
            tags_to_write[self.TAG_XMP_DC_RELATION] = master_id

        # Title is based on PRV filename; rest of contextual fields are
        # inherited when present.
        tags_to_write[self.TAG_XMP_DC_TITLE] = prv_path.stem

        for key in (
            self.TAG_XMP_DC_DESCRIPTION,
            self.TAG_XMP_DC_CREATOR,
            self.TAG_XMP_PHOTOSHOP_CREDIT,
            self.TAG_XMP_DC_RIGHTS,
            self.TAG_XMP_XMPRIGHTS_USAGE_TERMS,
            self.TAG_XMP_DC_SOURCE,
        ):
            value = existing.get(key)
            if value is not None:
                tags_to_write[key] = value

        # Dates: inherit from master, with fallback for DateTimeDigitized.
        for key in (
            self.TAG_EXIF_DATETIME_ORIGINAL,
            self.TAG_XMP_PHOTOSHOP_DATE_CREATED,
            self.TAG_XMP_EXIF_DATETIME_DIGITIZED,
        ):
            value = existing.get(key)
            if value is None and key == self.TAG_XMP_EXIF_DATETIME_DIGITIZED:
                value = existing.get(self.TAG_EXIFIFD_DATETIME_DIGITIZED)
            if value is not None:
                tags_to_write[key] = value

        if logger is not None:
            logger.debug(
                "Writing metadata to PRV %s based on master %s", prv_path, master_path
            )

        if tags_to_write:
            self._exifer.write(prv_path, tags_to_write)
