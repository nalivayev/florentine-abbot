"""
File Organizer - Metadata Extraction and Organization Workflow.

This module provides the main :class:`FileOrganizer` workflow class.

Responsibilities are split as follows:

* :class:`file_organizer.processor.FileProcessor` contains per-file logic
    (parsing, validation, EXIF/XMP writing).
* :class:`FileOrganizer` orchestrates batch mode around a processor instance
    and configuration.
* :class:`file_organizer.watcher.FileWatcher` implements daemon/watch mode.
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
    """
    High-level batch workflow for organizing files in a folder.

    A :class:`FileProcessor` instance is used internally for actual per-file
    work; this class focuses on configuration and one-shot directory
    traversal.

    When *output_path* is provided, files are organized under that directory
    (the archive root).  When omitted, falls back to ``input_path/processed/``
    for backward compatibility.
    """

    @staticmethod
    def _validate_no_overlap(input_path: Path, output_path: Path) -> None:
        """
        Raise :class:`ValueError` if the two paths overlap.

        Overlap means the paths are equal, or one is an ancestor of the
        other.  Both paths are resolved before comparison.
        """
        resolved_in = input_path.resolve()
        resolved_out = output_path.resolve()
        if resolved_in == resolved_out:
            raise ValueError(
                f"Input and output paths must not overlap, "
                f"both resolve to: {resolved_in}"
            )
        if resolved_out.is_relative_to(resolved_in):
            raise ValueError(
                f"Output path ({resolved_out}) is inside input path "
                f"({resolved_in}); they must not overlap"
            )
        if resolved_in.is_relative_to(resolved_out):
            raise ValueError(
                f"Input path ({resolved_in}) is inside output path "
                f"({resolved_out}); they must not overlap"
            )

    def __init__(self, logger: Logger) -> None:
        """
        Initialize the organizer.

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
        output_path: Path,
        config_path: str | Path | None = None,
        recursive: bool = False,
        copy_mode: bool = False,
    ) -> int:
        """
        Run the organizer in batch mode.

        Args:
            input_path: Root folder to process.
            output_path: Destination archive root.
            config_path: Optional path to the JSON configuration file.
            recursive: If True, process files in subdirectories recursively.
            copy_mode: If True, copy files instead of moving them.

        Returns:
            The number of successfully processed files.

        Raises:
            ValueError: If *input_path* and *output_path* overlap (equal
                or one is a subdirectory of the other).
        """
        return self._run_batch(
            input_path=input_path,
            output_path=output_path,
            config_path=config_path,
            recursive=recursive,
            copy_mode=copy_mode,
        )

    def _load_config(self, config_path: str | Path | None) -> Config:
        """
        Create a :class:`Config` instance bound to this organizer's logger.
        """

        return Config(self._logger, config_path)

    def _run_batch(
        self,
        *,
        input_path: Path,
        output_path: Path,
        config_path: str | Path | None = None,
        recursive: bool = False,
        copy_mode: bool = False,
    ) -> int:
        """
        Process existing files under ``input_path`` once and exit.

        Args:
            input_path: Root folder to process.
            output_path: Destination archive root.
            config_path: Optional path to the JSON configuration file.
            recursive: If True, process files in subdirectories recursively.
            copy_mode: If True, copy files instead of moving them.

        Returns:
            The number of successfully processed files.

        Raises:
            ValueError: If *input_path* and *output_path* overlap (equal
                or one is a subdirectory of the other).
        """

        config = self._load_config(config_path)

        resolved_input = Path(input_path).resolve()
        resolved_output = Path(output_path).resolve()

        # Guard: input and output must not overlap.
        self._validate_no_overlap(resolved_input, resolved_output)

        mode_str = "RECURSIVE" if recursive else "BATCH"
        self._logger.info(
            "Starting File Organizer in %s mode: %s -> %s",
            mode_str, input_path, resolved_output,
        )

        count = 0
        skipped = 0

        # Choose iterator based on recursive flag
        iterator = input_path.rglob('*') if recursive else input_path.iterdir()

        for file_path in iterator:
            if not file_path.is_file():
                continue

            if not self.should_process(file_path, output_path=resolved_output):
                self._logger.warning(f"Skipped file (invalid filename format or unsupported): {file_path.name}")
                skipped += 1
                continue

            if self.process_single_file(file_path, output_path=resolved_output, copy_mode=copy_mode):
                count += 1
            else:
                skipped += 1

        self._logger.info(f"Batch processing complete. Processed {count} files, skipped {skipped} files.")

        return count

    def process_single_file(
        self,
        file_path: Path,
        *,
        output_path: Path,
        copy_mode: bool = False,
    ) -> bool:
        """
        Process a single file: validate, copy, write metadata, clean up.

        This is the core per-file logic used by both batch mode and watch
        mode.  The caller is responsible for filtering (see
        :meth:`should_process`) and for ensuring *output_path* does not
        overlap with the source directory.

        Args:
            file_path: Source image file.
            output_path: Resolved archive root.
            copy_mode: If True keep the source file; otherwise delete it.

        Returns:
            True on success, False on any error.
        """
        # Validate source file (DocumentID/InstanceID, parse, validate)
        parsed = self._processor.validate(file_path)
        if not parsed:
            return False

        # Get destination paths using Router
        try:
            dest_path, dest_log_path, log_file_path = self._calculate_destination_paths(
                file_path, parsed, output_path
            )
        except Exception as e:
            self._logger.error(f"Failed to calculate destination path: {e}")
            return False

        # Check if destination already exists
        if dest_path.exists():
            self._logger.error(
                f"Destination file already exists: {dest_path}. "
                f"Leaving source file in place."
            )
            return False

        if dest_log_path and dest_log_path.exists():
            self._logger.error(
                f"Destination log file already exists: {dest_log_path}. "
                f"Leaving source files in place."
            )
            return False

        # ATOMIC COPY STRATEGY:
        # 1. Copy to temp file (.tmp extension)
        # 2. Process metadata on temp file
        # 3. Rename temp file to final destination (atomic move)

        temp_dest_path = dest_path.with_suffix(dest_path.suffix + ".tmp")

        # Copy files to temp destination
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(file_path), str(temp_dest_path))
            self._logger.info(f"  Copied to temp: {temp_dest_path}")

            if log_file_path and dest_log_path:
                dest_log_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(log_file_path), str(dest_log_path))
                self._logger.info(f"  Copied log to: {dest_log_path}")
        except Exception as e:
            self._logger.error(f"Failed to copy file: {e}")
            if temp_dest_path.exists():
                try:
                    temp_dest_path.unlink()
                except OSError:
                    pass
            return False

        # Write metadata to TEMP destination file
        if not self._processor.process(temp_dest_path, parsed):
            self._logger.warning(f"Metadata write failed, deleting temp file {temp_dest_path}")
            try:
                temp_dest_path.unlink()
                if dest_log_path and dest_log_path.exists():
                    dest_log_path.unlink()
            except Exception as e:
                self._logger.error(f"Failed to cleanup temp file: {e}")
            return False

        # Atomic rename to final name
        try:
            temp_dest_path.rename(dest_path)
            self._logger.info(f"  Atomic rename: {temp_dest_path.name} -> {dest_path.name}")
        except OSError as e:
            self._logger.error(f"Failed to perform atomic rename to {dest_path}: {e}")
            try:
                if temp_dest_path.exists():
                    temp_dest_path.unlink()
                if dest_log_path and dest_log_path.exists():
                    dest_log_path.unlink()
            except OSError:
                pass
            return False

        # If move mode, delete source files
        if not copy_mode:
            try:
                file_path.unlink()
                self._logger.info(f"  Deleted source: {file_path}")

                if log_file_path and log_file_path.exists():
                    log_file_path.unlink()
                    self._logger.info(f"  Deleted source log: {log_file_path}")
            except Exception as e:
                self._logger.warning(f"Failed to delete source file after successful copy: {e}")

        self._logger.info(f"Successfully processed: {temp_dest_path.name}")
        return True

    def should_process(self, file_path: Path, output_path: Path | None = None) -> bool:
        """
        Check if a file should be processed.

        Checks:
        - Not under the output directory (when provided)
        - Not a symlink
        - Has supported image extension

        Note: Filename validation is done separately in validate() method.

        Args:
            file_path: Path to the file to check.
            output_path: Resolved output directory to exclude.

        Returns:
            True if the file should be processed, False otherwise.
        """
        # Skip files that live under the output tree.
        if output_path is not None:
            try:
                file_path.resolve().relative_to(output_path.resolve())
                self._logger.debug("Skipping %s: inside output directory %s", file_path, output_path)
                return False
            except ValueError:
                pass  # not under output_path — OK

        # Skip symlinks
        if file_path.is_symlink():
            self._logger.debug(f"Skipping {file_path}: is symlink")
            return False

        # Check extension
        if file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            self._logger.debug(f"Skipping {file_path}: unsupported extension '{file_path.suffix}'")
            return False

        return True

    def _parse_and_validate(self, filename: str):
        """
        Expose :meth:`FileProcessor._parse_and_validate` for tests.
        """

        return self._processor._parse_and_validate(filename)

    def _calculate_destination_paths(
        self,
        file_path: Path,
        parsed: Any,  # ParsedFilename
        processed_root: Path
    ) -> tuple[Path, Path | None, Path | None]:
        """
        Calculate destination paths for file and optional log file using Router.
        
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
