"""File Organizer - Metadata Extraction and Organization Workflow.

This module provides the main :class:`FileOrganizer` workflow class.

Responsibilities are split as follows:

* :class:`file_organizer.processor.FileProcessor` contains per-file logic
    (parsing, validation, EXIF/XMP writing, moving to ``processed/``).
* :class:`FileOrganizer` orchestrates batch and daemon modes around a
    processor instance and configuration.
"""

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

    # ------------------------------------------------------------------
    # High-level batch workflow
    # ------------------------------------------------------------------

    def __call__(
        self,
        *,
        input_path: Path,
        config_path: str | Path | None = None,
        recursive: bool = False,
    ) -> int:
        """Run the organizer in batch mode.

        Args:
            input_path: Root folder to process.
            config_path: Optional path to the JSON configuration file.
            recursive: If True, process files in subdirectories recursively.

        Returns:
            The number of successfully processed files.
        """
        return self._run_batch(input_path=input_path, config_path=config_path, recursive=recursive)

    def _load_config(self, config_path: str | Path | None) -> Config:
        """Create a :class:`Config` instance bound to this organizer's logger."""

        return Config(self._logger, config_path)

    def _run_batch(self, *, input_path: Path, config_path: str | Path | None, recursive: bool = False) -> int:
        """Process existing files under ``input_path`` once and exit.
        
        Args:
            input_path: Root folder to process.
            config_path: Optional path to the JSON configuration file.
            recursive: If True, process files in subdirectories recursively.
            
        Returns:
            The number of successfully processed files.
        """

        config = self._load_config(config_path)
        metadata: dict[str, Any] = config.get_metadata()

        # Create a new processor with root_path set for recursive mode
        processor = FileProcessor(self._logger, root_path=input_path if recursive else None)

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

            if processor.process(file_path, metadata):
                count += 1

        self._logger.info(f"Batch processing complete. Processed {count} files, skipped {skipped} files.")

        return count

    # ------------------------------------------------------------------
    # Per-file processing facade
    # ------------------------------------------------------------------

    def should_process(self, file_path: Path) -> bool:
        """Delegate to the internal :class:`FileProcessor` instance."""

        return self._processor.should_process(file_path)

    def process(self, file_path: Path, config: dict[str, Any]) -> bool:
        """Delegate per-file processing to :class:`FileProcessor`."""

        return self._processor.process(file_path, config)

    def _parse_and_validate(self, filename: str):
        """Expose :meth:`FileProcessor._parse_and_validate` for tests."""

        return self._processor._parse_and_validate(filename)
