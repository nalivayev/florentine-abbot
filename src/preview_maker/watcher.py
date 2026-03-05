"""
File system watcher for Preview Maker using watchdog.

:class:`PreviewWatcher` is a thin wrapper around :class:`PreviewMaker` that
reacts to file-system events instead of scanning a directory once.  All
per-file logic (filtering, conversion, metadata) is delegated to
:meth:`PreviewMaker.should_process` and :meth:`PreviewMaker.process_single_file`.
"""

import threading
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent, FileSystemMovedEvent

from common.logger import Logger
from common.utils import wait_for_stable
from preview_maker.maker import PreviewMaker

class PreviewWatcher(FileSystemEventHandler):
    """
    Watch an archive tree for new source files and generate previews.

    Monitors the archive root recursively for files matching the configured
    ``source_priority`` patterns and automatically generates preview JPEGs
    using :class:`PreviewMaker`.
    """

    def __init__(
        self,
        logger: Logger,
        path: str,
        *,
        config_path: str | Path | None = None,
        max_size: int = 2000,
        quality: int = 80,
        no_metadata: bool = False,
    ) -> None:
        """
        Initialize the watcher.

        Args:
            logger: Logger instance.
            path: Archive root to watch (recursively).
            config_path: Optional path to preview-maker config JSON.
            max_size: Maximum long edge in pixels for preview.
            quality: JPEG quality (1-100).
            no_metadata: If True, skip writing EXIF/XMP metadata.
        """
        super().__init__()
        self._path = Path(path).resolve()
        self._logger = logger
        self._max_size = max_size
        self._quality = quality
        self._maker = PreviewMaker(logger, config_path, no_metadata=no_metadata)
        self._observer = Observer()
        self._stop_event = threading.Event()

    # ── watchdog event handlers ────────────────────────────────────────

    def on_created(self, event: FileSystemEvent) -> None:
        """
        Handle file creation events.
        """
        if event.is_directory:
            return
        self._process_file(Path(str(event.src_path)), wait=True)

    def on_moved(self, event: FileSystemEvent) -> None:
        """
        Handle file movement events.
        """
        if event.is_directory:
            return
        if isinstance(event, FileSystemMovedEvent):
            self._process_file(Path(str(event.dest_path)), wait=False)

    # ── per-file processing ────────────────────────────────────────────

    def _process_file(self, file_path: Path, wait: bool = True) -> None:
        """
        Filter and delegate a single file to :class:`PreviewMaker`.

        Steps:
        1. Check the file still exists.
        2. Apply the same extension / suffix filter that batch mode uses.
        3. For on_created events: wait until the file size stabilises
           (handles OS copy and cross-filesystem moves).
        4. Delegate to :meth:`PreviewMaker.process_single_file`.
        """
        if not file_path.exists():
            return

        if not self._maker.should_process(file_path):
            return

        try:
            if wait:
                wait_for_stable(file_path)
            self._maker.process_single_file(
                file_path,
                archive_path=self._path,
                max_size=self._max_size,
                quality=self._quality,
            )
        except Exception as e:
            self._logger.error(f"Error processing {file_path}: {e}")

    # ── lifecycle ──────────────────────────────────────────────────────

    def start(self) -> None:
        """
        Start watching.

        Watches the archive root recursively for new source files.
        Runs until interrupted by KeyboardInterrupt.
        """
        if not self._path.exists():
            self._logger.error(f"Path does not exist: {self._path}")
            return

        self._observer.schedule(self, str(self._path), recursive=True)
        self._observer.start()
        self._logger.info(f"Started watching for new sources in {self._path}")

        try:
            self._stop_event.wait()
        except KeyboardInterrupt:
            pass
        self._observer.stop()
        self._observer.join()
        self._logger.info("Stopped watching")

    def stop(self) -> None:
        """
        Signal watching to stop. Safe to call from any thread.
        """
        self._stop_event.set()
