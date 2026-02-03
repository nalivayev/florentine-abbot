"""File Organizer - Metadata Extraction and Organization Workflow.

This module provides the main :class:`FileOrganizer` workflow class.

Responsibilities are split as follows:

* :class:`file_organizer.processor.FileProcessor` contains per-file logic
    (parsing, validation, EXIF/XMP writing, moving to ``processed/``).
* :class:`FileOrganizer` orchestrates batch and daemon modes around a
    processor instance and configuration.
"""

import shutil
from pathlib import Path
from typing import Any

from common.logger import Logger
from common.router import Router
from common.constants import SUPPORTED_IMAGE_EXTENSIONS
from file_organizer.config import Config
from file_organizer.processor import FileProcessor


class FileOrganizer:
    """High-level batch workflow for organizing files in a folder.

    A :class:`FileProcessor` instance is used internally for actual per-file
    work; this class focuses on configuration and one-shot directory
    traversal. Daemon/monitoring mode is implemented by
    :class:`file_organizer.monitor.ArchiveMonitor` and is wired from the CLI.
    """

    def __init__(self, logger: Logger) -> None:
        """Initialize the organizer.

        Args:
            logger: Logger instance for this organizer.
        """
        self._logger = logger
        self._processor = FileProcessor(logger)
        self._router = Router(logger=logger)

    def __call__(
        self,
        *,
        input_path: Path,
        config_path: str | Path | None = None,
        recursive: bool = False,
        copy_mode: bool = False,
    ) -> int:
        """Run the organizer in batch mode.

        Args:
            input_path: Root folder to process.
            config_path: Optional path to the JSON configuration file.
            recursive: If True, process files in subdirectories recursively.
            copy_mode: If True, copy files instead of moving them.

        Returns:
            The number of successfully processed files.
        """
        return self._run_batch(input_path=input_path, config_path=config_path, recursive=recursive, copy_mode=copy_mode)

    def _load_config(self, config_path: str | Path | None) -> Config:
        """Create a :class:`Config` instance bound to this organizer's logger."""

        return Config(self._logger, config_path)

    def _run_batch(self, *, input_path: Path, config_path: str | Path | None, recursive: bool = False, copy_mode: bool = False) -> int:
        """Process existing files under ``input_path`` once and exit.
        
        Args:
            input_path: Root folder to process.
            config_path: Optional path to the JSON configuration file.
            recursive: If True, process files in subdirectories recursively.
            copy_mode: If True, copy files instead of moving them.
            
        Returns:
            The number of successfully processed files.
        """

        config = self._load_config(config_path)
        
        mode_str = "RECURSIVE" if recursive else "BATCH"
        self._logger.info(f"Starting File Organizer in {mode_str} mode on {input_path}")

        count = 0
        skipped = 0
        
        # Base directory for processed output
        processed_root = input_path / "processed"

        # Choose iterator based on recursive flag
        iterator = input_path.rglob('*') if recursive else input_path.iterdir()

        for file_path in iterator:
            if not file_path.is_file():
                continue

            if not self.should_process(file_path):
                self._logger.warning(f"Skipped file (invalid filename format or unsupported): {file_path.name}")
                skipped += 1
                continue

            # Process metadata
            if self._processor.process(file_path):
                # Get parsed filename for destination calculation
                parsed = self._processor._parse_and_validate(file_path.name)
                
                # Get destination paths using Router directly
                try:
                    dest_path, dest_log_path, log_file_path = self._calculate_destination_paths(
                        file_path, parsed, processed_root
                    )
                except Exception as e:
                     self._logger.error(f"Failed to calculate destination path: {e}")
                     skipped += 1
                     continue
                
                # Check if destination already exists
                if dest_path.exists():
                    self._logger.error(
                        f"Destination file already exists: {dest_path}. "
                        f"Leaving source file in place."
                    )
                    skipped += 1
                    continue
                
                if dest_log_path and dest_log_path.exists():
                    self._logger.error(
                        f"Destination log file already exists: {dest_log_path}. "
                        f"Leaving source files in place."
                    )
                    skipped += 1
                    continue
                
                # Move or copy files
                try:
                    if copy_mode:
                        shutil.copy2(str(file_path), str(dest_path))
                        self._logger.info(f"  Copied to: {dest_path}")
                        
                        if log_file_path and dest_log_path:
                            shutil.copy2(str(log_file_path), str(dest_log_path))
                            self._logger.info(f"  Copied log to: {dest_log_path}")
                    else:
                        shutil.move(str(file_path), str(dest_path))
                        self._logger.info(f"  Moved to: {dest_path}")
                        
                        if log_file_path and dest_log_path:
                            shutil.move(str(log_file_path), str(dest_log_path))
                            self._logger.info(f"  Moved log to: {dest_log_path}")
                    
                    count += 1
                except Exception as e:
                    self._logger.error(f"Failed to {'copy' if copy_mode else 'move'} file: {e}")
                    skipped += 1

        self._logger.info(f"Batch processing complete. Processed {count} files, skipped {skipped} files.")

        return count

    def should_process(self, file_path: Path) -> bool:
        """Check if a file should be processed.
        
        Checks:
        - Not in 'processed' subfolder
        - Not a symlink
        - Has supported image extension
        - Has valid parseable filename
        
        Args:
            file_path: Path to the file to check.

        Returns:
            True if the file should be processed, False otherwise.
        """
        # Skip files in 'processed' subfolder to avoid re-processing
        if 'processed' in file_path.parts:
            self._logger.debug(f"Skipping {file_path}: found 'processed' in path parts")
            return False

        # Skip symlinks
        if file_path.is_symlink():
            self._logger.debug(f"Skipping {file_path}: is symlink")
            return False

        # Check extension
        if file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            self._logger.debug(f"Skipping {file_path}: unsupported extension '{file_path.suffix}'")
            return False

        # Try to parse and validate filename (delegate to processor)
        parsed = self._processor._parse_and_validate(file_path.name)
        if parsed is None:
             self._logger.debug(f"Skipping {file_path}: failed parse/validate")
        return parsed is not None

    def process(self, file_path: Path, config: dict[str, Any] | None) -> bool:
        """Delegate per-file processing to :class:`FileProcessor`.
        
        Args:
            file_path: Path to the file to process.
            config: DEPRECATED - Configuration dict is no longer used.
                   Metadata is now loaded from metadata.json automatically.
        
        Returns:
            True if processing successful, False otherwise.
        """
        # Config parameter is deprecated - metadata is now loaded from metadata.json
        return self._processor.process(file_path)

    def _parse_and_validate(self, filename: str):
        """Expose :meth:`FileProcessor._parse_and_validate` for tests."""

        return self._processor._parse_and_validate(filename)

    def _calculate_destination_paths(
        self,
        file_path: Path,
        parsed: Any,  # ParsedFilename
        processed_root: Path
    ) -> tuple[Path, Path | None, Path | None]:
        """Calculate destination paths for file and optional log file using Router.
        
        Args:
            file_path: Source file path.
            parsed: ParsedFilename object.
            processed_root: Root directory for processed files.
            
        Returns:
            Tuple (dest_path, dest_log_path, source_log_path).
        """
        # Check for associated log file
        source_log_path = file_path.with_suffix('.log')
        if not source_log_path.exists():
            source_log_path = None

        # Get normalized filename from router
        base_name = self._router.get_normalized_filename(parsed)
        dest_filename = f"{base_name}.{parsed.extension}"

        dest_log_filename = None
        if source_log_path:
            dest_log_filename = f"{base_name}.log"

        # Get target folder from router
        processed_dir = self._router.get_target_folder(parsed, processed_root)

        # Create processed directory if it doesn't exist
        processed_dir.mkdir(parents=True, exist_ok=True)

        # Destination paths
        dest_path = processed_dir / dest_filename
        dest_log_path = processed_dir / dest_log_filename if dest_log_filename else None

        return dest_path, dest_log_path, source_log_path
