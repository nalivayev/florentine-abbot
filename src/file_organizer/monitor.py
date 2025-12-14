"""File system monitor using watchdog."""

import logging
import time
from pathlib import Path
from typing import Any

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent, FileSystemMovedEvent

from .processor import ArchiveProcessor

class ArchiveEventHandler(FileSystemEventHandler):
    """Event handler for archive file system events.
    
    Monitors file creation and movement events, processing files that match
    the structured filename pattern.
    """

    def __init__(self, processor: ArchiveProcessor, config: dict[str, Any]) -> None:
        """Initialize the event handler.
        
        Args:
            processor: ArchiveProcessor instance for file processing.
            config: Configuration dictionary for metadata fields.
        """
        self.processor = processor
        self.config = config
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
                self.processor.process(file_path, self.config)
            except Exception as e:
                self.logger.error(f"Error processing {file_path}: {e}")

class ArchiveMonitor:
    """Monitor for archive folders.
    
    Uses watchdog to monitor a directory for new files and automatically
    process them when they appear.
    """

    def __init__(self, path: str, config: dict[str, Any]) -> None:
        """Initialize the monitor.
        
        Args:
            path: Directory path to monitor.
            config: Configuration dictionary for file processing.
        """
        self.path = Path(path).resolve()
        self.config = config
        self.processor = ArchiveProcessor()
        self.observer = Observer()
        self.logger = logging.getLogger(__name__)

    def start(self) -> None:
        """Start monitoring.
        
        Begins watching the configured directory for file changes.
        Runs until interrupted by KeyboardInterrupt.
        """
        if not self.path.exists():
            self.logger.error(f"Path does not exist: {self.path}")
            return

        event_handler = ArchiveEventHandler(self.processor, self.config)
        self.observer.schedule(event_handler, str(self.path), recursive=False)
        self.observer.start()
        self.logger.info(f"Started monitoring {self.path}")

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
