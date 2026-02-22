"""
File system monitor using watchdog.

:class:`FileWatcher` is a thin wrapper around :class:`FileOrganizer` that
reacts to file-system events instead of scanning a directory once.  All
per-file logic (validation, copy, metadata, cleanup) is delegated to
:meth:`FileOrganizer.process_single_file`.
"""

import signal
import time
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent, FileSystemMovedEvent

from common.logger import Logger
from file_organizer.config import Config
from file_organizer.organizer import FileOrganizer


class FileWatcher(FileSystemEventHandler):
    """
    Watch an input folder for new files using watchdog.

    Watches a directory for new files and automatically processes them
    using :class:`FileOrganizer`.  Supports config reloading via SIGHUP.
    """

    def __init__(self, logger: Logger, path: str, config: Config, output_path: Path, copy_mode: bool = False, no_metadata: bool = False) -> None:
        """
        Initialize the monitor.

        Args:
            logger: Logger instance for this monitor.
            path: Directory path to monitor (input / inbox).
            config: Config instance for file processing.
            output_path: Destination archive root.
            copy_mode: If True, copy files instead of moving them.
            no_metadata: If True, skip writing EXIF/XMP metadata.

        Raises:
            ValueError: If *path* and *output_path* overlap (equal or
                one is a subdirectory of the other).
        """
        super().__init__()
        self._path = Path(path).resolve()
        self._config = config
        self._logger = logger
        self._copy_mode = copy_mode
        self._no_metadata = no_metadata
        self._output_path: Path = Path(output_path).resolve()

        # Validate early — reuse the same check as batch mode.
        FileOrganizer._validate_no_overlap(self._path, self._output_path)

        self._organizer = FileOrganizer(logger)
        self._observer = Observer()
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """
        Setup signal handlers for config reload.
        """
        def reload_config(signum, frame):
            self._logger.info("Received SIGHUP, reloading configuration...")
            if self._config.reload():
                self._logger.info("Configuration reloaded successfully")
            else:
                self._logger.info("Configuration unchanged")

        # SIGHUP for config reload (Unix only)
        try:
            sighup = getattr(signal, 'SIGHUP', None)
            if sighup:
                signal.signal(sighup, reload_config)
        except (AttributeError, OSError):
            # Windows doesn't have SIGHUP
            self._logger.debug("SIGHUP not available on this platform")

    # ── watchdog event handlers ────────────────────────────────────────

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if event.is_directory:
            return
        self._process_file(Path(event.src_path))

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file movement events."""
        if event.is_directory:
            return
        if isinstance(event, FileSystemMovedEvent):
            self._process_file(Path(event.dest_path))

    # ── per-file processing ────────────────────────────────────────────

    def _process_file(self, file_path: Path) -> None:
        """Filter and delegate a single file to :class:`FileOrganizer`.

        Steps:
        1. Check the file still exists (it may vanish between event and
           handler).
        2. Apply the same extension / symlink / output-tree filter that
           batch mode uses.
        3. Wait briefly for the file write to complete (simple heuristic).
        4. Delegate to :meth:`FileOrganizer.process_single_file`.
        """
        if not file_path.exists():
            return

        if not self._organizer.should_process(file_path, output_path=self._output_path):
            return

        # Small delay to let the OS finish writing the file.
        time.sleep(1)

        try:
            self._organizer.process_single_file(
                file_path,
                output_path=self._output_path,
                copy_mode=self._copy_mode,
                no_metadata=self._no_metadata,
            )
        except Exception as e:
            self._logger.error(f"Error processing {file_path}: {e}")

    # ── lifecycle ──────────────────────────────────────────────────────

    def start(self) -> None:
        """
        Start monitoring.

        Begins watching the configured directory for file changes.
        Runs until interrupted by KeyboardInterrupt.
        """
        if not self._path.exists():
            self._logger.error(f"Path does not exist: {self._path}")
            return

        self._observer.schedule(self, str(self._path), recursive=False)
        self._observer.start()
        self._logger.info("Started monitoring %s -> %s", self._path, self._output_path)
        self._logger.info("Send SIGHUP to reload configuration (Unix) or restart the process (Windows)")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """
        Stop monitoring and clean up resources.
        """
        self._observer.stop()
        self._observer.join()
        self._logger.info("Stopped monitoring")
