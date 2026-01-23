"""Per-file processing logic for the File Organizer.

This module contains :class:`FileProcessor`, which is responsible for
parsing structured filenames, validating them, writing EXIF/XMP metadata,
and moving files into the ``processed/`` tree. Higher-level orchestration
(batch/daemon) is handled by :class:`file_organizer.organizer.FileOrganizer`.
"""

import shutil
from pathlib import Path
from typing import Any

from common.logger import Logger
from common.naming import FilenameParser, ParsedFilename, FilenameValidator
from common.constants import SUPPORTED_IMAGE_EXTENSIONS
from common.archive_metadata import ArchiveMetadata
from common.router import Router


class FileProcessor:
    """Processor that extracts metadata and organizes individual files."""

    def __init__(
        self,
        logger: Logger,
        root_path: Path | None = None,
        metadata_tags: dict[str, str] | None = None,
        suffix_routing: dict[str, str] | None = None
    ) -> None:
        """Initialize FileProcessor.
        
        Args:
            logger: Logger instance.
            root_path: Optional root path for validation.
            metadata_tags: Optional metadata field to XMP tag mapping.
            suffix_routing: Optional suffix routing rules (suffix -> 'sources'/'derivatives'/'preview').
        """
        self.logger = logger
        self.parser = FilenameParser()
        self.validator = FilenameValidator()
        self._metadata = ArchiveMetadata(metadata_tags=metadata_tags)
        self._root_path = root_path
        self._router = Router(suffix_routing=suffix_routing, logger=logger)

    def should_process(self, file_path: Path) -> bool:
        """Check if the file should be processed.

        Args:
            file_path: Path to the file to check.

        Returns:
            True if the file should be processed, False otherwise.
        """
        # Skip files in 'processed' subfolder to avoid re-processing
        # This check is a bit tricky if we are just given a path.
        # We assume the caller handles directory traversal or we check parent names.
        if 'processed' in file_path.parts:
            return False

        # Skip symlinks
        if file_path.is_symlink():
            return False

        # Check extension
        if file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            return False

        # Try to parse and validate filename
        parsed = self._parse_and_validate(file_path.name)
        return parsed is not None

    def process(self, file_path: Path, config: dict[str, Any] | None) -> bool:
        """Process a file: parse filename, validate, write EXIF/XMP metadata, and move to processed folder.

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

        # Check for associated log file
        log_file_path = file_path.with_suffix('.log')
        if not log_file_path.exists():
            log_file_path = None

        # Move to processed folder
        if not self._move_to_processed(file_path, parsed, log_file_path):
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
            return True
        except (FileNotFoundError, RuntimeError, ValueError) as e:
            self.logger.error(f"Exiftool failed: {e}")
            return False
        except Exception as e:  # pragma: no cover - defensive
            self.logger.error(f"Failed to write metadata to {file_path}: {e}")
            return False

    def _move_to_processed(self, file_path: Path, parsed: ParsedFilename | None = None, log_file_path: Path | None = None) -> bool:
        """Move file to processed subfolder, preserving directory structure.
        
        Args:
            file_path: Path to the file.
            parsed: Parsed filename data (optional).
            log_file_path: Path to the associated log file (optional).

        Returns:
            True if move successful, False otherwise.
        """
        try:
            # Determine the base directory for processed folder
            # If root_path is set (recursive mode), use it; otherwise use file's parent
            if self._root_path:
                processed_root = self._root_path / "processed"
            else:
                file_dir = file_path.parent
                processed_root = file_dir / "processed"

            # Determine destination filename
            dest_filename = file_path.name
            dest_log_filename = None

            if parsed:
                # Get normalized filename from router
                base_name = self._router.get_normalized_filename(parsed)
                dest_filename = f"{base_name}.{parsed.extension}"

                if log_file_path:
                    dest_log_filename = f"{base_name}.log"

                # Get target folder from router
                processed_dir = self._router.get_target_folder(parsed, processed_root)

            else:
                # Fallback for unparsed files (should not happen if should_process is checked)
                processed_dir = processed_root / "unparsed"
                if log_file_path:
                    dest_log_filename = log_file_path.name

            # Create processed directory if it doesn't exist
            processed_dir.mkdir(parents=True, exist_ok=True)

            # Destination path
            dest_path = processed_dir / dest_filename

            # Check if destination already exists
            if dest_path.exists():
                self.logger.error(
                    f"Destination file already exists: {dest_path}. "
                    f"Leaving source file in place."
                )
                return False
            
            # Check if log destination exists
            dest_log_path = None
            if log_file_path and dest_log_filename:
                dest_log_path = processed_dir / dest_log_filename
                if dest_log_path.exists():
                    self.logger.error(
                        f"Destination log file already exists: {dest_log_path}. "
                        f"Leaving source files in place."
                    )
                    return False

            # Move file
            shutil.move(str(file_path), str(dest_path))
            self.logger.info(f"  Moved to: {dest_path}")
            
            # Move log file
            if log_file_path and dest_log_path:
                shutil.move(str(log_file_path), str(dest_log_path))
                self.logger.info(f"  Moved log to: {dest_log_path}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to move file {file_path} to processed/: {e}")
            return False
