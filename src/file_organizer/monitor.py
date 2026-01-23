"""File system monitor using watchdog."""

import signal
import time
from pathlib import Path
from typing import Any

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent, FileSystemMovedEvent

from common.logger import Logger
from file_organizer.config import Config
from file_organizer.processor import FileProcessor


class FileMonitor(FileSystemEventHandler):
    """Monitor for input folders using watchdog.

    Watches a directory for new files and automatically processes them
    using :class:`FileProcessor`. Supports config reloading via SIGHUP.
    """

    def __init__(self, logger: Logger, path: str, config: Config) -> None:
        """Initialize the monitor.
        
        Args:
            logger: Logger instance for this monitor.
            path: Directory path to monitor.
            config: Config instance for file processing.
        """
        super().__init__()
        self.path = Path(path).resolve()
        self.config = config
        self.logger = logger
        self.processor = FileProcessor(logger)
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

    def _get_metadata(self) -> dict[str, Any] | None:
        """Get current metadata configuration.
        
        Returns:
            Dictionary with current XMP field values, or None if not configured.
        """
        return self.config.get_metadata()

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

    def _process_file(self, file_path_str: str) -> None:
        """Process a file if it matches the criteria."""

        file_path = Path(file_path_str)

        # Basic check if file exists (it might have been moved/deleted quickly)
        if not file_path.exists():
            return

        if self.processor.should_process(file_path):
            # Small delay to ensure file write is complete (simple heuristic)
            # For large files, this might not be enough, but it's a start.
            # A more robust solution would check for file stability (size not changing).
            time.sleep(1)

            try:
                # Get fresh metadata from config (in case it was reloaded)
                metadata = self._get_metadata()
                self.processor.process(file_path, metadata)
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
