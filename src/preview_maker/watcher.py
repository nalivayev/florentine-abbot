"""
File system watcher for Preview Maker using watchdog.

:class:`PreviewWatcher` is a thin wrapper around :class:`PreviewMaker` that
reacts to file-system events instead of scanning a directory once.  All
per-file logic (filtering, conversion, metadata) is delegated to
:meth:`PreviewMaker.should_process` and :meth:`PreviewMaker.process_single_file`.
"""

import time
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent, FileSystemMovedEvent

from common.logger import Logger
from preview_maker.maker import PreviewMaker


class PreviewWatcher(FileSystemEventHandler):
    """Watch an archive tree for new master files and generate PRV previews.

    Monitors the archive root recursively for new RAW/MSR files and
    automatically generates PRV JPEGs using :class:`PreviewMaker`.
    """

    def __init__(
        self,
        logger: Logger,
        path: str,
        *,
        max_size: int = 2000,
        quality: int = 80,
    ) -> None:
        """Initialize the watcher.

        Args:
            logger: Logger instance.
            path: Archive root to watch (recursively).
            max_size: Maximum long edge in pixels for PRV.
            quality: JPEG quality (1-100).
        """
        super().__init__()
        self._path = Path(path).resolve()
        self._logger = logger
        self._max_size = max_size
        self._quality = quality
        self._maker = PreviewMaker(logger)
        self._observer = Observer()

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
        """Filter and delegate a single file to :class:`PreviewMaker`.

        Steps:
        1. Check the file still exists.
        2. Apply the same extension / suffix filter that batch mode uses.
        3. Wait briefly for the file write to complete.
        4. Delegate to :meth:`PreviewMaker.process_single_file`.
        """
        if not file_path.exists():
            return

        if not self._maker.should_process(file_path):
            return

        # Small delay to let the OS finish writing the file.
        time.sleep(1)

        try:
            self._maker.process_single_file(
                file_path,
                archive_path=self._path,
                max_size=self._max_size,
                quality=self._quality,
            )
        except Exception as e:
            self._logger.error("Error processing %s: %s", file_path, e)

    # ── lifecycle ──────────────────────────────────────────────────────

    def start(self) -> None:
        """Start watching.

        Watches the archive root recursively for new master files.
        Runs until interrupted by KeyboardInterrupt.
        """
        if not self._path.exists():
            self._logger.error("Path does not exist: %s", self._path)
            return

        self._observer.schedule(self, str(self._path), recursive=True)
        self._observer.start()
        self._logger.info("Started watching for new masters in %s", self._path)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """Stop watching and clean up resources."""
        self._observer.stop()
        self._observer.join()
        self._logger.info("Stopped watching")
