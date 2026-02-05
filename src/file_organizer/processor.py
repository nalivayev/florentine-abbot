"""Per-file processing logic for the File Organizer.

This module contains :class:`FileProcessor`, which is responsible for
parsing structured filenames, validating them, writing EXIF/XMP metadata,
and moving files into the ``processed/`` tree. Higher-level orchestration
(batch/daemon) is handled by :class:`file_organizer.organizer.FileOrganizer`.
"""

import uuid
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from common.logger import Logger
from common.naming import FilenameParser, ParsedFilename, FilenameValidator
from common.constants import SUPPORTED_IMAGE_EXTENSIONS, EXIFTOOL_LARGE_FILE_TIMEOUT
from common.metadata import (
    ArchiveMetadata,
    TAG_XMP_DC_IDENTIFIER,
    TAG_XMP_XMP_IDENTIFIER,
    TAG_EXIF_DATETIME_ORIGINAL,
    TAG_XMP_PHOTOSHOP_DATE_CREATED,
    TAG_XMP_EXIF_DATETIME_DIGITIZED,
    TAG_EXIFIFD_DATETIME_DIGITIZED,
    TAG_EXIFIFD_CREATE_DATE,
)
from common.exifer import Exifer
from common.historian import XMPHistorian, TAG_XMP_XMPMM_INSTANCE_ID, TAG_XMP_XMPMM_DOCUMENT_ID, XMP_ACTION_EDITED
from common.version import get_version


class FileProcessor:
    """Processor that extracts metadata and writes it to files.
    
    This class is responsible ONLY for:
    - Parsing and validating filenames
    - Writing EXIF/XMP metadata to image files
    
    It does NOT handle:
    - File path filtering (handled by FileOrganizer)
    - File organization/movement (handled by FileOrganizer)
    """

    def __init__(self, logger: Logger) -> None:
        """Initialize FileProcessor.
        
        Args:
            logger: Logger instance.
        """
        self._logger = logger
        self._parser = FilenameParser()
        self._validator = FilenameValidator()
        self._metadata = ArchiveMetadata(logger=logger)
        self._exifer = Exifer()
        self._historian = XMPHistorian()

    def validate(self, file_path: Path) -> ParsedFilename | None:
        """Validate source file before processing.
        
        Checks:
        - DocumentID/InstanceID exist (must be set by scan-batcher)
        - Filename can be parsed
        - Filename passes validation rules
        
        Args:
            file_path: Path to the source file to validate.
            
        Returns:
            ParsedFilename if validation successful, None otherwise.
        """
        # Check for DocumentID/InstanceID (must be set by scan-batcher)
        existing_ids = self._exifer.read(file_path, [TAG_XMP_XMPMM_DOCUMENT_ID, TAG_XMP_XMPMM_INSTANCE_ID])
        if not existing_ids.get(TAG_XMP_XMPMM_DOCUMENT_ID) or not existing_ids.get(TAG_XMP_XMPMM_INSTANCE_ID):
            self._logger.error(
                f"File {file_path.name} is missing DocumentID or InstanceID. "
                "These must be set by scan-batcher before processing."
            )
            return None

        # Parse and validate filename
        parsed = self._parse_and_validate(file_path.name)
        if not parsed:
            self._logger.error(f"Failed to parse or validate filename: {file_path.name}")
            return None
        
        return parsed

    def process(self, dest_path: Path, parsed: ParsedFilename) -> bool:
        """Write EXIF/XMP metadata to destination file.

        Args:
            dest_path: Path to the destination file (already copied).
            parsed: Parsed filename data from source.

        Returns:
            True if metadata written successfully, False otherwise.
        """
        self._logger.info(f"Writing metadata to: {dest_path}")

        # Write EXIF/XMP metadata to destination
        if not self._write_metadata(dest_path, parsed):
            return False

        self._logger.info(f"Successfully processed: {dest_path.name}")
        return True

    def _parse_and_validate(self, filename: str) -> ParsedFilename | None:
        """Parse and validate a filename.

        Args:
            filename: The filename to parse and validate.

        Returns:
            Parsed filename data if valid, None otherwise.
        """
        parsed = self._parser.parse(filename)
        if not parsed:
            return None

        validation_errors = self._validator.validate(parsed)
        if validation_errors:
            return None

        return parsed

    def _write_metadata(self, file_path: Path, parsed: ParsedFilename) -> bool:
        """Write metadata to EXIF/XMP fields using exiftool.

        Args:
            file_path: Path to the file.
            parsed: Parsed filename data.

        Returns:
            True if all metadata written successfully, False otherwise.
        """
        try:
            tags: dict[str, Any] = {}

            # 1. Identifiers (XMP) - generate unique UUID
            file_uuid = uuid.uuid4().hex
            tags[TAG_XMP_DC_IDENTIFIER] = file_uuid
            tags[TAG_XMP_XMP_IDENTIFIER] = file_uuid

            # 2. Dates
            # 2.1 DateTimeDigitized - preserve scanning date from CreateDate
            try:
                existing_tags = self._exifer.read(
                    file_path,
                    [TAG_XMP_EXIF_DATETIME_DIGITIZED, TAG_EXIFIFD_DATETIME_DIGITIZED, TAG_EXIFIFD_CREATE_DATE],
                )

                date_digitized = (
                    existing_tags.get(TAG_XMP_EXIF_DATETIME_DIGITIZED)
                    or existing_tags.get(TAG_EXIFIFD_DATETIME_DIGITIZED)
                )

                if not date_digitized:
                    create_date = existing_tags.get(TAG_EXIFIFD_CREATE_DATE)
                    if create_date:
                        tags[TAG_XMP_EXIF_DATETIME_DIGITIZED] = create_date
                        self._logger.debug("Set DateTimeDigitized from CreateDate: %s", create_date)
                else:
                    self._logger.debug("DateTimeDigitized already set: %s", date_digitized)
            except Exception as exc:  # pragma: no cover - defensive
                self._logger.warning("Could not process DateTimeDigitized: %s", exc)

            # 2.2 DateTimeOriginal - date from filename (original photo date)
            if parsed.modifier == "E":
                dt_str = (
                    f"{parsed.year:04d}:{parsed.month:02d}:{parsed.day:02d} "
                    f"{parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d}"
                )
                tags[TAG_EXIF_DATETIME_ORIGINAL] = dt_str
                tags[TAG_XMP_PHOTOSHOP_DATE_CREATED] = dt_str.replace(":", "-", 2).replace(" ", "T")
            else:
                # Partial date: clear EXIF DateTimeOriginal and encode partial
                # date in XMP-photoshop:DateCreated.
                tags[TAG_EXIF_DATETIME_ORIGINAL] = ""

                if parsed.year > 0:
                    date_val = f"{parsed.year:04d}"
                    if parsed.month > 0:
                        date_val += f"-{parsed.month:02d}"
                        if parsed.day > 0:
                            date_val += f"-{parsed.day:02d}"

                    tags[TAG_XMP_PHOTOSHOP_DATE_CREATED] = date_val

            # 3. Configurable fields from metadata.json
            metadata_values = self._metadata.get_metadata_values(logger=self._logger)
            tags.update(metadata_values)

            # 4. Write all tags using Exifer
            file_size = file_path.stat().st_size
            if file_size > 100 * 1024 * 1024:  # > 100MB
                self._logger.info(
                    "Running exiftool on large file (%.1f MB): %s",
                    file_size / (1024**2),
                    file_path.name,
                )
                self._exifer.write(file_path, tags, timeout=EXIFTOOL_LARGE_FILE_TIMEOUT)
            else:
                self._logger.info("Running exiftool on %s...", file_path.name)
                self._exifer.write(file_path, tags)
            
            self._logger.info("  Metadata written successfully.")
            
            # Write XMP History entry for file-organizer
            self._write_history_entry(file_path)
            
            return True
        except (FileNotFoundError, RuntimeError, ValueError) as e:
            self._logger.error(f"Exiftool failed: {e}")
            return False
        except Exception as e:  # pragma: no cover - defensive
            self._logger.error(f"Failed to write metadata to {file_path}: {e}")
            return False

    def _write_history_entry(self, file_path: Path) -> None:
        """Write XMP History entry for file-organizer metadata changes.
        
        Args:
            file_path: Path to the file.
        """
        try:
            # Read InstanceID from file
            tags = self._exifer.read(file_path, [TAG_XMP_XMPMM_INSTANCE_ID])
            instance_id = tags.get(TAG_XMP_XMPMM_INSTANCE_ID)
            
            if not instance_id:
                self._logger.warning(f"No InstanceID found for {file_path.name}, skipping history entry")
                return
            
            # Get version for software agent
            version = get_version()
            if version == "unknown":
                version = "0.0"
            else:
                parts = version.split(".")
                if len(parts) >= 2:
                    version = f"{parts[0]}.{parts[1]}"
            
            software_agent = f"file-organizer {version}"
            
            # Write history entry with current time
            success = self._historian.append_entry(
                file_path=file_path,
                action=XMP_ACTION_EDITED,
                software_agent=software_agent,
                when=datetime.now(timezone.utc),
                changed="metadata",
                instance_id=instance_id,
                logger=self._logger,
            )
            
            if not success:
                self._logger.warning(f"Failed to write history entry for {file_path.name}")
        except Exception as e:
            self._logger.warning(f"Failed to write XMP history for {file_path.name}: {e}")
