"""Shared archival metadata policy built on top of Exifer.

This module centralizes the list of EXIF/XMP tags used by the
File Organizer and Preview Maker workflows and provides
high-level helpers for writing metadata to master files and
preview (PRV) derivatives.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from common.constants import EXIFTOOL_LARGE_FILE_TIMEOUT
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

    def __init__(self, exifer: Exifer | None = None) -> None:
        self._exifer = exifer or Exifer()

    # ------------------------------------------------------------------
    # Tag lists for read operations
    # ------------------------------------------------------------------

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
        description: str,
        parsed: Any,
        config: dict[str, Any],
        logger: Logger,
    ) -> None:
        """Write EXIF/XMP metadata for a master/derivative file.

        This implements the same policy that :class:`FileProcessor`
        previously carried inline:

        - generate UUID identifiers
        - write human-readable description and title
        - derive DateTimeDigitized from existing CreateDate if needed
        - encode DateTimeOriginal / DateCreated from parsed filename
        - apply configurable fields (creator, rights, etc.)
        """

        tags: dict[str, Any] = {}

        # 1. Identifiers (XMP)
        file_uuid = str(uuid.uuid4())
        tags[self.TAG_XMP_DC_IDENTIFIER] = file_uuid
        tags[self.TAG_XMP_XMP_IDENTIFIER] = file_uuid

        # 2. Description & Title
        tags[self.TAG_XMP_DC_DESCRIPTION] = description
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

        # 4. Configurable fields
        creator_value = config.get("creator")
        if creator_value:
            if isinstance(creator_value, list):
                tags[self.TAG_XMP_DC_CREATOR] = creator_value
            else:
                tags[self.TAG_XMP_DC_CREATOR] = [creator_value]

        credit = config.get("credit")
        if credit:
            tags[self.TAG_XMP_PHOTOSHOP_CREDIT] = credit

        rights = config.get("rights")
        if rights:
            tags[self.TAG_XMP_DC_RIGHTS] = rights

        usage_terms = config.get("usage_terms")
        if usage_terms:
            tags[self.TAG_XMP_XMPRIGHTS_USAGE_TERMS] = usage_terms

        source = config.get("source")
        if source:
            tags[self.TAG_XMP_DC_SOURCE] = source

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
        logger: Logger | None = None,
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
