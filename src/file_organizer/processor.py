"""Per-file processing logic for the File Organizer.

This module contains :class:`FileProcessor`, which is responsible for
parsing structured filenames, validating them, writing EXIF/XMP metadata,
and moving files into the ``processed/`` tree. Higher-level orchestration
(batch/daemon) is handled by :class:`file_organizer.organizer.FileOrganizer`.
"""

from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from common.logger import Logger
from common.naming import FilenameParser, ParsedFilename, FilenameValidator
from common.constants import SUPPORTED_IMAGE_EXTENSIONS
from common.archive_metadata import ArchiveMetadata
from common.historian import XMPHistorian, TAG_XMP_XMPMM_INSTANCE_ID, XMP_ACTION_EDITED
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

    def __init__(
        self,
        logger: Logger,
        metadata_tags: dict[str, str] | None = None,
    ) -> None:
        """Initialize FileProcessor.
        
        Args:
            logger: Logger instance.
            metadata_tags: Optional metadata field to XMP tag mapping.
        """
        self.logger = logger
        self.parser = FilenameParser()
        self.validator = FilenameValidator()
        self._metadata = ArchiveMetadata(metadata_tags=metadata_tags, logger=logger)
        self._historian = XMPHistorian()

    def process(self, file_path: Path, config: dict[str, Any] | None) -> bool:
        """Process a file: parse filename, validate, write EXIF/XMP metadata.

        Args:
            file_path: Path to the file to process.
            config: Configuration parameters (metadata dict), or None to skip metadata writing.

        Returns:
            True if processing successful, False otherwise.
        """
        self.logger.info(f"Processing file: {file_path}")

        # Parse and validate filename
        parsed = self._parse_and_validate(file_path.name)
        if not parsed:
            self.logger.error(f"Failed to parse or validate filename: {file_path.name}")
            return False

        # Write EXIF/XMP metadata
        if not self._write_metadata(file_path, parsed, config):
            return False

        self.logger.info(f"Successfully processed: {file_path.name}")
        return True

    def _parse_and_validate(self, filename: str) -> ParsedFilename | None:
        """Parse and validate a filename.

        Args:
            filename: The filename to parse and validate.

        Returns:
            Parsed filename data if valid, None otherwise.
        """
        parsed = self.parser.parse(filename)
        if not parsed:
            return None

        validation_errors = self.validator.validate(parsed)
        if validation_errors:
            return None

        return parsed

    def _write_metadata(self, file_path: Path, parsed: ParsedFilename, config: dict[str, Any] | None) -> bool:
        """Write metadata to EXIF/XMP fields using exiftool.

        Args:
            file_path: Path to the file.
            parsed: Parsed filename data.
            config: Plugin configuration (metadata dict), or None to skip metadata writing.

        Returns:
            True if all metadata written successfully, False otherwise.
        """
        try:
            self._metadata.write_master_tags(
                file_path=file_path,
                parsed=parsed,
                config=config,
                logger=self.logger,
            )
            
            # Write XMP History entry for file-organizer
            self._write_history_entry(file_path)
            
            return True
        except (FileNotFoundError, RuntimeError, ValueError) as e:
            self.logger.error(f"Exiftool failed: {e}")
            return False
        except Exception as e:  # pragma: no cover - defensive
            self.logger.error(f"Failed to write metadata to {file_path}: {e}")
            return False

    def _write_history_entry(self, file_path: Path) -> None:
        """Write XMP History entry for file-organizer metadata changes.
        
        Args:
            file_path: Path to the file.
        """
        try:
            # Read InstanceID from file
            from common.exifer import Exifer
            exifer = Exifer()
            tags = exifer.read(file_path, [TAG_XMP_XMPMM_INSTANCE_ID])
            instance_id = tags.get(TAG_XMP_XMPMM_INSTANCE_ID)
            
            if not instance_id:
                self.logger.warning(f"No InstanceID found for {file_path.name}, skipping history entry")
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
                logger=self.logger,
            )
            
            if not success:
                self.logger.warning(f"Failed to write history entry for {file_path.name}")
        except Exception as e:
            self.logger.warning(f"Failed to write XMP history for {file_path.name}: {e}")
