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
        metadata: dict[str, Any] | None = config.get_metadata()

        # Create a new processor with root_path set for recursive mode
        # metadata_tags and suffix_routing are self-loaded by components if needed
        processor = FileProcessor(
            self._logger,
            root_path=input_path if recursive else None,
        )


        mode_str = "RECURSIVE" if recursive else "BATCH"
        self._logger.info(f"Starting File Organizer in {mode_str} mode on {input_path}")

        count = 0
        skipped = 0

        # Choose iterator based on recursive flag
        iterator = input_path.rglob('*') if recursive else input_path.iterdir()

        for file_path in iterator:
            if not file_path.is_file():
                continue

            if not processor.should_process(file_path):
                self._logger.warning(f"Skipped file (invalid filename format or unsupported): {file_path.name}")
                skipped += 1
                continue

            # Process metadata
            if processor.process(file_path, metadata):
                # Get parsed filename for destination calculation
                parsed = processor._parse_and_validate(file_path.name)
                
                # Get destination paths
                dest_path, dest_log_path, log_file_path = processor.get_destination_paths(file_path, parsed)
                
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
        """Delegate to the internal :class:`FileProcessor` instance."""

        return self._processor.should_process(file_path)

    def process(self, file_path: Path, config: dict[str, Any] | None) -> bool:
        """Delegate per-file processing to :class:`FileProcessor`.
        
        Args:
            file_path: Path to the file to process.
            config: Configuration dict (full organizer config with 'metadata' key,
                   or raw metadata dict), or None to skip metadata fields.
        
        Returns:
            True if processing successful, False otherwise.
        """
        # Accept either a full organizer config (with top-level "metadata"
        # block) or a raw metadata dict. For the former, extract the
        # "metadata" section so that FileProcessor receives only the
        # metadata configuration, mirroring the batch/Config path.
        # If config is None, pass None to processor to skip configurable metadata.
        metadata = config.get("metadata", config) if config is not None else None
        return self._processor.process(file_path, metadata)

    def _parse_and_validate(self, filename: str):
        """Expose :meth:`FileProcessor._parse_and_validate` for tests."""

        return self._processor._parse_and_validate(filename)
