"""File system monitor using watchdog."""

import shutil
import signal
import time
from pathlib import Path
from typing import Any

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent, FileSystemMovedEvent

from common.logger import Logger
from common.router import Router
from common.constants import SUPPORTED_IMAGE_EXTENSIONS
from file_organizer.config import Config
from file_organizer.processor import FileProcessor


class FileMonitor(FileSystemEventHandler):
    """Monitor for input folders using watchdog.

    Watches a directory for new files and automatically processes them
    using :class:`FileProcessor`. Supports config reloading via SIGHUP.
    """

    def __init__(self, logger: Logger, path: str, config: Config, copy_mode: bool = False) -> None:
        """Initialize the monitor.
        
        Args:
            logger: Logger instance for this monitor.
            path: Directory path to monitor.
            config: Config instance for file processing.
            copy_mode: If True, copy files instead of moving them.
        """
        super().__init__()
        self.path = Path(path).resolve()
        self.config = config
        self.logger = logger
        self.copy_mode = copy_mode
        self.processor = FileProcessor(logger)
        self.router = Router()
        self.observer = Observer()
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for config reload."""
        def reload_config(signum, frame):
            self.logger.info("Received SIGHUP, reloading configuration...")
            if self.config.reload():
                self.logger.info("Configuration reloaded successfully")
            else:
                self.logger.info("Configuration unchanged")
        
        # SIGHUP for config reload (Unix only)
        try:
            sighup = getattr(signal, 'SIGHUP', None)
            if sighup:
                signal.signal(sighup, reload_config)
        except (AttributeError, OSError):
            # Windows doesn't have SIGHUP
            self.logger.debug("SIGHUP not available on this platform")



    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""

        if event.is_directory:
            return

        self._process_file(str(event.src_path))

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file movement events."""

        if event.is_directory:
            return

        if isinstance(event, FileSystemMovedEvent):
            self._process_file(str(event.dest_path))

    def _should_process(self, file_path: Path) -> bool:
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
        # Skip files in 'processed' subfolder
        if 'processed' in file_path.parts:
            self.logger.debug(f"Skipping {file_path}: found 'processed' in path parts")
            return False

        # Skip symlinks
        if file_path.is_symlink():
            self.logger.debug(f"Skipping {file_path}: is symlink")
            return False

        # Check extension
        if file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            self.logger.debug(f"Skipping {file_path}: unsupported extension '{file_path.suffix}'")
            return False

        # Try to parse and validate filename
        parsed = self.processor._parse_and_validate(file_path.name)
        if parsed is None:
             self.logger.debug(f"Skipping {file_path}: failed parse/validate")
        return parsed is not None

    def _process_file(self, file_path_str: str) -> None:
        """Process a file if it matches the criteria."""

        file_path = Path(file_path_str)

        # Basic check if file exists (it might have been moved/deleted quickly)
        if not file_path.exists():
            return

        # Check if file should be processed (path filtering, extension, filename validation)
        if not self._should_process(file_path):
            return

        # Small delay to ensure file write is complete (simple heuristic)
        # For large files, this might not be enough, but it's a start.
        # A more robust solution would check for file stability (size not changing).
        time.sleep(1)

        try:
            # Validate source file (DocumentID/InstanceID, parse, validate)
            parsed = self.processor.validate(file_path)
            if not parsed:
                return
            
            # Calculate destination paths
            processed_root = self.path / "processed"
            source_log_path = file_path.with_suffix('.log')
            if not source_log_path.exists():
                source_log_path = None
            log_file_path = source_log_path  # alias for existing code

            # Calculate normalized filename and destination
            base_name = self.router.get_normalized_filename(parsed)
            dest_filename = f"{base_name}.{parsed.extension}"
            
            dest_log_filename = None
            if source_log_path:
                dest_log_filename = f"{base_name}.log"
            
            processed_dir = self.router.get_target_folder(parsed, processed_root)

            processed_dir.mkdir(parents=True, exist_ok=True)
            dest_path = processed_dir / dest_filename
            dest_log_path = processed_dir / dest_log_filename if dest_log_filename else None
            
            # Check if destination already exists
            if dest_path.exists():
                self.logger.error(
                    f"Destination file already exists: {dest_path}. "
                    f"Leaving source file in place."
                )
                return
            
            if dest_log_path and dest_log_path.exists():
                self.logger.error(
                    f"Destination log file already exists: {dest_log_path}. "
                    f"Leaving source files in place."
                )
                return
            
            # Copy files to destination (always copy first)
            shutil.copy2(str(file_path), str(dest_path))
            self.logger.info(f"  Copied to: {dest_path}")
            
            if log_file_path and dest_log_path:
                shutil.copy2(str(log_file_path), str(dest_log_path))
                self.logger.info(f"  Copied log to: {dest_log_path}")
            
            # Write metadata to destination file
            if not self.processor.process(dest_path, parsed):
                # Metadata write failed - rollback by deleting destination
                self.logger.warning(f"Metadata write failed, rolling back copy of {file_path.name}")
                try:
                    dest_path.unlink()
                    if dest_log_path and dest_log_path.exists():
                        dest_log_path.unlink()
                except Exception as e:
                    self.logger.error(f"Failed to rollback copy: {e}")
                return
            
            # Success! If move mode, delete source files
            if not self.copy_mode:
                file_path.unlink()
                self.logger.info(f"  Deleted source: {file_path}")
                
                if log_file_path and log_file_path.exists():
                    log_file_path.unlink()
                    self.logger.info(f"  Deleted source log: {log_file_path}")
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {e}")

    def start(self) -> None:
        """Start monitoring.
        
        Begins watching the configured directory for file changes.
        Runs until interrupted by KeyboardInterrupt.
        """
        if not self.path.exists():
            self.logger.error(f"Path does not exist: {self.path}")
            return

        self.observer.schedule(self, str(self.path), recursive=False)
        self.observer.start()
        self.logger.info(f"Started monitoring {self.path}")
        self.logger.info("Send SIGHUP to reload configuration (Unix) or restart the process (Windows)")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """Stop monitoring and clean up resources."""
        self.observer.stop()
        self.observer.join()
        self.logger.info("Stopped monitoring")
