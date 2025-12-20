"""File system monitor using watchdog."""

import logging
import signal
import time
from pathlib import Path
from typing import Any

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent, FileSystemMovedEvent

from .processor import ArchiveProcessor
from .config import Config

class ArchiveEventHandler(FileSystemEventHandler):
    """Event handler for archive file system events.
    
    Monitors file creation and movement events, processing files that match
    the structured filename pattern.
    """

    def __init__(self, processor: ArchiveProcessor, monitor: 'ArchiveMonitor') -> None:
        """Initialize the event handler.
        
        Args:
            processor: ArchiveProcessor instance for file processing.
            monitor: ArchiveMonitor instance for accessing config.
        """
        self.processor = processor
        self.monitor = monitor
        self.logger = logging.getLogger(__name__)

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events.
        
        Args:
            event: File system event containing file information.
        """
        if event.is_directory:
            return
        
        self._process_file(str(event.src_path))

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file movement events.
        
        Args:
            event: File system event containing file information.
        """
        if event.is_directory:
            return
        
        if isinstance(event, FileSystemMovedEvent):
            self._process_file(str(event.dest_path))

    def _process_file(self, file_path_str: str) -> None:
        """Process a file if it matches the criteria.
        
        Args:
            file_path_str: String path to the file to process.
        """
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
                metadata = self.monitor.get_metadata()
                self.processor.process(file_path, metadata)
            except Exception as e:
                self.logger.error(f"Error processing {file_path}: {e}")

class ArchiveMonitor:
    """Monitor for archive folders.
    
    Uses watchdog to monitor a directory for new files and automatically
    process them when they appear. Supports config reloading via SIGHUP.
    """

    def __init__(self, path: str, config: Config) -> None:
        """Initialize the monitor.
        
        Args:
            path: Directory path to monitor.
            config: Config instance for file processing.
        """
        self.path = Path(path).resolve()
        self.config = config
        self.processor = ArchiveProcessor()
        self.observer = Observer()
        self.logger = logging.getLogger(__name__)
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

    def get_metadata(self) -> dict[str, Any]:
        """Get current metadata configuration.
        
        Returns:
            Dictionary with current XMP field values.
        """
        return self.config.get_metadata()

    def start(self) -> None:
        """Start monitoring.
        
        Begins watching the configured directory for file changes.
        Runs until interrupted by KeyboardInterrupt.
        """
        if not self.path.exists():
            self.logger.error(f"Path does not exist: {self.path}")
            return

        event_handler = ArchiveEventHandler(self.processor, self)
        self.observer.schedule(event_handler, str(self.path), recursive=False)
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
