"""Core logic for processing files: parsing, metadata extraction, and organization."""

import logging
import shutil
import uuid
from pathlib import Path
from typing import Any

from common.exifer import Exifer
from .parser import FilenameParser, ParsedFilename
from .validator import FilenameValidator


class ArchiveProcessor:
    """Processor that extracts metadata from structured photo filenames and writes to EXIF/XMP."""

    SUPPORTED_EXTENSIONS = {".tiff", ".tif", ".jpg", ".jpeg"}

    def __init__(self) -> None:
        """Initialize the processor."""
        self.logger = logging.getLogger(__name__)
        self.parser = FilenameParser()
        self.validator = FilenameValidator()

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
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return False

        # Try to parse and validate filename
        parsed = self._parse_and_validate(file_path.name)
        return parsed is not None

    def process(self, file_path: Path, config: dict[str, Any]) -> bool:
        """Process a file: parse filename, validate, write EXIF/XMP metadata, and move to processed folder.

        Args:
            file_path: Path to the file to process.
            config: Configuration parameters.

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

    def _generate_description(self, parsed: ParsedFilename) -> str:
        """Generate a human-readable description from parsed data."""
        parts = []
        
        # Date description
        if parsed.modifier == 'E':
            parts.append(f"Exact date: {parsed.year:04d}-{parsed.month:02d}-{parsed.day:02d}")
        elif parsed.modifier == 'C':
            parts.append(f"Circa {parsed.year:04d}")
        elif parsed.modifier == 'B':
            parts.append(f"Before {parsed.year:04d}")
        elif parsed.modifier == 'F':
            parts.append(f"After {parsed.year:04d}")
        elif parsed.modifier == 'A':
            parts.append("Date unknown")
            
        # Add other parts if needed (Group, Subgroup etc)
        
        return ". ".join(parts)

    def _write_metadata(self, file_path: Path, parsed: ParsedFilename, config: dict[str, Any]) -> bool:
        """Write metadata to EXIF/XMP fields using exiftool.

        Args:
            file_path: Path to the file.
            parsed: Parsed filename data.
            config: Plugin configuration.

        Returns:
            True if all metadata written successfully, False otherwise.
        """
        try:
            tags = {}
            
            # 1. Identifiers (XMP)
            file_uuid = str(uuid.uuid4())
            tags["XMP-dc:Identifier"] = file_uuid
            tags["XMP-xmp:Identifier"] = file_uuid

            # 2. Description & Title
            description = self._generate_description(parsed)
            tags["XMP-dc:Description"] = description
            tags["XMP-dc:Title"] = file_path.stem

            # 3. Dates
            if parsed.modifier == 'E':
                # Exact date
                dt_str = f"{parsed.year:04d}:{parsed.month:02d}:{parsed.day:02d} {parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d}"
                tags["Exif:DateTimeOriginal"] = dt_str
                tags["XMP-photoshop:DateCreated"] = dt_str.replace(':', '-', 2).replace(' ', 'T')
            else:
                # Partial date
                tags["Exif:DateTimeOriginal"] = "" # Clear it
                
                # XMP DateCreated (partial)
                if parsed.year > 0:
                    date_val = f"{parsed.year:04d}"
                    if parsed.month > 0:
                        date_val += f"-{parsed.month:02d}"
                        if parsed.day > 0:
                            date_val += f"-{parsed.day:02d}"
                    
                    tags["XMP-photoshop:DateCreated"] = date_val

            # 4. Configurable fields
            if config.get('creator'):
                tags["XMP-dc:Creator"] = config['creator']
            if config.get('credit'):
                tags["XMP-photoshop:Credit"] = config['credit']
            if config.get('rights'):
                tags["XMP-dc:Rights"] = config['rights']
            if config.get('usage_terms'):
                tags["XMP-xmpRights:UsageTerms"] = config['usage_terms']
            if config.get('source'):
                tags["XMP-dc:Source"] = config['source']

            # Log file size for large files (useful for performance tracking)
            file_size = file_path.stat().st_size
            if file_size > 100 * 1024 * 1024:  # > 100MB
                self.logger.info(f"Running exiftool on large file ({file_size / (1024**2):.1f} MB): {file_path.name}")
            else:
                self.logger.info(f"Running exiftool on {file_path.name}...")
            
            tool = Exifer()
            tool.write(file_path, tags)
            
            self.logger.info("  Metadata written successfully.")
            return True

        except Exifer.Exception as e:
            self.logger.error(f"Exiftool failed: {e}")
            return False
        except Exception as e:
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
            # Determine the base directory (parent of the file)
            file_dir = file_path.parent
            processed_root = file_dir / "processed"

            # Determine destination filename
            dest_filename = file_path.name
            dest_log_filename = None

            if parsed:
                # Reconstruct filename with normalized components (leading zeros)
                base_name = (
                    f"{parsed.year:04d}.{parsed.month:02d}.{parsed.day:02d}."
                    f"{parsed.hour:02d}.{parsed.minute:02d}.{parsed.second:02d}."
                    f"{parsed.modifier}.{parsed.group}.{parsed.subgroup}.{int(parsed.sequence):04d}."
                    f"{parsed.side}.{parsed.suffix}"
                )
                dest_filename = f"{base_name}.{parsed.extension}"
                
                if log_file_path:
                    dest_log_filename = f"{base_name}.log"

                # Build folder structure:
                # Level 1: YYYY.M (e.g. 1945.E, 1950.B)
                level1 = f"{parsed.year:04d}.{parsed.modifier}"

                # Level 2: YYYY.MM.DD.M (e.g. 1945.06.15.E)
                level2 = f"{parsed.year:04d}.{parsed.month:02d}.{parsed.day:02d}.{parsed.modifier}"

                # Level 3: SUFFIX (e.g. RAW, MSR)
                level3 = parsed.suffix

                processed_dir = processed_root / level1 / level2 / level3

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
