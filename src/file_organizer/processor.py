"""
Per-file processing logic for the File Organizer.

This module contains :class:`FileProcessor`, which is responsible for
parsing structured filenames, validating them, writing EXIF/XMP metadata,
and moving files into the ``processed/`` tree. Higher-level orchestration
(batch/daemon) is handled by :class:`file_organizer.organizer.FileOrganizer`.
"""

import uuid
from pathlib import Path
from datetime import datetime

from common.logger import Logger
from common.naming import FilenameParser, ParsedFilename, FilenameValidator
from common.constants import EXIFTOOL_LARGE_FILE_TIMEOUT, TAG_XMP_DC_IDENTIFIER, TAG_XMP_XMP_IDENTIFIER, TAG_EXIF_DATETIME_ORIGINAL, TAG_XMP_PHOTOSHOP_DATE_CREATED, TAG_XMP_XMPMM_INSTANCE_ID, TAG_XMP_XMPMM_DOCUMENT_ID, XMP_ACTION_EDITED
from common.metadata import ArchiveMetadata
from common.exifer import Exifer
from common.tagger import Tagger
from common.tags import KeyValueTag, HistoryTag
from common.version import get_version


class FileProcessor:
    """
    Processor that extracts metadata and writes it to files.
    
    This class is responsible ONLY for:
    - Parsing and validating filenames
    - Writing EXIF/XMP metadata to image files
    
    It does NOT handle:
    - File path filtering (handled by FileOrganizer)
    - File organization/movement (handled by FileOrganizer)
    """

    def __init__(self, logger: Logger) -> None:
        """
        Initialize FileProcessor.
        
        Args:
            logger: Logger instance.
        """
        self._logger = logger
        self._parser = FilenameParser()
        self._validator = FilenameValidator()
        self._metadata = ArchiveMetadata(logger=logger)
        self._exifer = Exifer()

    def validate(self, file_path: Path) -> ParsedFilename | None:
        """
        Validate source file before processing.
        
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
        tagger = Tagger(file_path, exifer=self._exifer)
        tagger.begin()
        tagger.read(KeyValueTag(TAG_XMP_XMPMM_DOCUMENT_ID))
        tagger.read(KeyValueTag(TAG_XMP_XMPMM_INSTANCE_ID))
        existing_ids = tagger.end() or {}
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

    def process(self, dest_path: Path, parsed: ParsedFilename, no_metadata: bool = False) -> bool:
        """
        Write EXIF/XMP metadata to destination file.

        Args:
            dest_path: Path to the destination file (already copied).
            parsed: Parsed filename data from source.
            no_metadata: If True, skip writing metadata.

        Returns:
            True if metadata written successfully (or skipped), False otherwise.
        """
        if no_metadata:
            self._logger.info(f"Skipping metadata write for {dest_path.name} (--no-metadata)")
            return True

        self._logger.info(f"Writing metadata to: {dest_path}")

        # Write EXIF/XMP metadata to destination
        if not self._write_metadata(dest_path, parsed):
            return False

        self._logger.info(f"Successfully processed: {dest_path.name}")
        return True

    def _parse_and_validate(self, filename: str) -> ParsedFilename | None:
        """
        Parse and validate a filename.

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
        """
        Write metadata to EXIF/XMP fields using exiftool.

        All tags, the new InstanceID, and the XMP History entry are written
        in a single exiftool call via :class:`Tagger` batch mode.

        Args:
            file_path: Path to the file.
            parsed: Parsed filename data.

        Returns:
            True if all metadata written successfully, False otherwise.
        """
        try:
            # Determine timeout for large files
            file_size = file_path.stat().st_size
            timeout = EXIFTOOL_LARGE_FILE_TIMEOUT if file_size > 100 * 1024 * 1024 else None
            if timeout:
                self._logger.info(
                    "Running exiftool on large file (%.1f MB): %s",
                    file_size / (1024**2),
                    file_path.name,
                )
            else:
                self._logger.info("Running exiftool on %s...", file_path.name)

            tagger = Tagger(file_path, exifer=self._exifer, timeout=timeout)
            tagger.begin()

            # 1. Identifiers (XMP) - generate unique UUID
            file_uuid = uuid.uuid4().hex
            tagger.write(KeyValueTag(TAG_XMP_DC_IDENTIFIER, file_uuid))
            tagger.write(KeyValueTag(TAG_XMP_XMP_IDENTIFIER, file_uuid))

            # 2. Dates
            # 2.1 DateTimeOriginal - date from filename (original photo date)
            if parsed.modifier == "E":
                dt_str = (
                    f"{parsed.year:04d}:{parsed.month:02d}:{parsed.day:02d} "
                    f"{parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d}"
                )
                tagger.write(KeyValueTag(TAG_EXIF_DATETIME_ORIGINAL, dt_str))
                tagger.write(KeyValueTag(
                    TAG_XMP_PHOTOSHOP_DATE_CREATED,
                    dt_str.replace(":", "-", 2).replace(" ", "T"),
                ))
            else:
                # Partial date: clear EXIF DateTimeOriginal and encode partial
                # date in XMP-photoshop:DateCreated.
                tagger.write(KeyValueTag(TAG_EXIF_DATETIME_ORIGINAL, ""))

                if parsed.year > 0:
                    date_val = f"{parsed.year:04d}"
                    if parsed.month > 0:
                        date_val += f"-{parsed.month:02d}"
                        if parsed.day > 0:
                            date_val += f"-{parsed.day:02d}"

                    tagger.write(KeyValueTag(TAG_XMP_PHOTOSHOP_DATE_CREATED, date_val))

            # 3. Configurable fields from metadata.json
            metadata_values = self._metadata.get_metadata_values(logger=self._logger)
            for tag, value in metadata_values.items():
                tagger.write(KeyValueTag(tag, value))

            # 4. New InstanceID for this version
            # One modification: metadata write (this exiftool call).
            # File copy is a filesystem operation, not a content modification.
            new_instance_id = uuid.uuid4().hex
            tagger.write(KeyValueTag(TAG_XMP_XMPMM_INSTANCE_ID, new_instance_id))
            self._logger.debug(f"Generated new InstanceID: {new_instance_id}")

            # 5. XMP History entry
            version = get_version()
            if version == "unknown":
                version = "0.0"
            else:
                parts = version.split(".")
                if len(parts) >= 2:
                    version = f"{parts[0]}.{parts[1]}"

            tagger.write(HistoryTag(
                action=XMP_ACTION_EDITED,
                when=datetime.now().astimezone(),
                software_agent=f"file-organizer {version}",
                changed="metadata",
                instance_id=new_instance_id,
            ))

            tagger.end()  # single exiftool call

            self._logger.info("  Metadata written successfully.")
            return True
        except (FileNotFoundError, RuntimeError, ValueError) as e:
            self._logger.error(f"Exiftool failed: {e}")
            return False
        except Exception as e:  # pragma: no cover - defensive
            self._logger.error(f"Failed to write metadata to {file_path}: {e}")
            return False
