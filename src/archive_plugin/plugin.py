"""Photo naming EXIF plugin for folder-monitor."""

import logging
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, Optional

from folder_monitor.base_plugin import FileProcessorPlugin

from .parser import FilenameParser, ParsedFilename
from .validator import FilenameValidator


class PhotoNamingExifPlugin(FileProcessorPlugin):
    """Plugin that extracts metadata from structured photo filenames and writes to EXIF/XMP."""

    SUPPORTED_EXTENSIONS = {".tiff", ".tif", ".jpg", ".jpeg"}

    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.parser = FilenameParser()
        self.validator = FilenameValidator()

    @property
    def name(self) -> str:
        """Get the unique name of the plugin.

        Returns:
            The plugin name.
        """
        return "naming_exif"

    @property
    def version(self) -> str:
        """Get the version of the plugin.

        Returns:
            The plugin version string.
        """
        return "0.1.0"

    def can_handle(self, file_path: str) -> bool:
        """Check if the plugin can handle the given file.

        Args:
            file_path: Path to the file to check.

        Returns:
            True if the plugin can process the file, False otherwise.
        """
        path = Path(file_path)

        # Skip files in 'processed' subfolder to avoid re-processing
        if 'processed' in path.parts:
            return False

        # Skip symlinks
        if path.is_symlink():
            return False

        # Check extension
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return False

        # Try to parse and validate filename
        parsed = self._parse_and_validate(path.name)
        return parsed is not None

    def process(self, file_path: str, config: dict[str, Any]) -> bool:
        """Process a file: parse filename, validate, write EXIF/XMP metadata, and move to processed folder.

        Args:
            file_path: Path to the file to process.
            config: Plugin-specific configuration parameters.

        Returns:
            True if processing successful, False otherwise.
        """
        path = Path(file_path)
        self.logger.info(f"Processing file: {path}")

        # Parse and validate filename
        parsed = self._parse_and_validate(path.name)
        if not parsed:
            self.logger.error(f"Failed to parse or validate filename: {path.name}")
            return False

        # Write EXIF/XMP metadata
        if not self._write_metadata(path, parsed, config):
            return False

        # Move to processed folder
        if not self._move_to_processed(path, parsed):
            return False

        self.logger.info(f"Successfully processed: {path.name}")
        return True

    def _parse_and_validate(self, filename: str) -> Optional[ParsedFilename]:
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
        # For now just date description as per requirements
        
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
            cmd = ["exiftool", "-overwrite_original"]
            
            # 1. Identifiers (XMP)
            file_uuid = str(uuid.uuid4())
            cmd.extend([
                f"-XMP-dc:Identifier={file_uuid}",
                f"-XMP-xmp:Identifier={file_uuid}"
            ])

            # 2. Description & Title
            description = self._generate_description(parsed)
            cmd.extend([
                f"-XMP-dc:Description={description}",
                f"-XMP-dc:Title={file_path.stem}"
            ])

            # 3. Dates
            if parsed.modifier == 'E':
                # Exact date
                dt_str = f"{parsed.year:04d}:{parsed.month:02d}:{parsed.day:02d} {parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d}"
                cmd.extend([
                    f"-Exif:DateTimeOriginal={dt_str}",
                    f"-XMP-photoshop:DateCreated={dt_str.replace(':', '-', 2).replace(' ', 'T')}" # ISO format
                ])
            else:
                # Partial date
                # Clear DateTimeOriginal to be safe (ensure it's empty)
                cmd.append("-Exif:DateTimeOriginal=")
                
                # XMP DateCreated (partial)
                if parsed.year > 0:
                    # Exiftool handles partial dates in XMP automatically
                    date_val = f"{parsed.year:04d}"
                    if parsed.month > 0:
                        date_val += f"-{parsed.month:02d}"
                        if parsed.day > 0:
                            date_val += f"-{parsed.day:02d}"
                    
                    cmd.append(f"-XMP-photoshop:DateCreated={date_val}")

            # 4. Configurable fields
            if config.get('creator'):
                cmd.append(f"-XMP-dc:Creator={config['creator']}")
            if config.get('credit'):
                cmd.append(f"-XMP-photoshop:Credit={config['credit']}")
            if config.get('rights'):
                cmd.append(f"-XMP-dc:Rights={config['rights']}")
            if config.get('usage_terms'):
                cmd.append(f"-XMP-xmpRights:UsageTerms={config['usage_terms']}")
            if config.get('source'):
                cmd.append(f"-XMP-dc:Source={config['source']}")

            # Target file
            cmd.append(str(file_path))

            self.logger.info(f"Running exiftool on {file_path.name}...")
            
            # Run command
            # Use shell=False for security, but ensure exiftool is in PATH
            try:
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    encoding='utf-8',
                    check=False
                )
            except FileNotFoundError:
                self.logger.error("Exiftool not found. Please install exiftool and add it to PATH.")
                return False
            
            if result.returncode != 0:
                self.logger.error(f"Exiftool failed: {result.stderr}")
                return False
                
            self.logger.info("  Metadata written successfully.")
            return True

        except Exception as e:
            self.logger.error(f"Failed to write metadata to {file_path}: {e}")
            return False

    def _move_to_processed(self, file_path: Path, parsed: Optional[ParsedFilename] = None) -> bool:
        """Move file to processed subfolder, preserving directory structure.
        
        If parsed data is provided, the filename will be normalized (e.g. adding leading zeros).

        Args:
            file_path: Path to the file.
            parsed: Parsed filename data (optional).

        Returns:
            True if move successful, False otherwise.
        """
        try:
            # Determine the watched folder root
            # We need to find the base watched folder to create processed/ structure
            # For now, create processed/ in the same directory as the file
            file_dir = file_path.parent
            processed_dir = file_dir / "processed"

            # Create processed directory if it doesn't exist
            processed_dir.mkdir(parents=True, exist_ok=True)

            # Determine destination filename
            dest_filename = file_path.name
            if parsed:
                # Reconstruct filename with normalized components (leading zeros)
                # Ensure sequence is normalized to 4 digits
                dest_filename = (
                    f"{parsed.year:04d}.{parsed.month:02d}.{parsed.day:02d}."
                    f"{parsed.hour:02d}.{parsed.minute:02d}.{parsed.second:02d}."
                    f"{parsed.modifier}.{parsed.group}.{parsed.subgroup}.{int(parsed.sequence):04d}."
                    f"{parsed.side}.{parsed.suffix}.{parsed.extension}"
                )

            # Destination path
            dest_path = processed_dir / dest_filename

            # Check if destination already exists
            if dest_path.exists():
                self.logger.error(
                    f"Destination file already exists: {dest_path}. "
                    f"Leaving source file in place."
                )
                return False

            # Move file
            shutil.move(str(file_path), str(dest_path))
            self.logger.info(f"  Moved to: {dest_path}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to move file {file_path} to processed/: {e}")
            return False
