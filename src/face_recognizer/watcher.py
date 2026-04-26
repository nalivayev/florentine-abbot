"""Polling-based daemon wrapper for Face Recognizer orchestration."""

import threading
from pathlib import Path

from common.config_utils import get_archive_path
from common.logger import Logger
from face_recognizer.config import Config
from face_recognizer.recognizer import Recognizer

_POLL_INTERVAL = 60  # seconds


class RecognizerWatcher:
    """Polls on a timer and delegates each pass to :class:`Recognizer`."""

    def __init__(
        self,
        logger: Logger,
        *,
        engine: Recognizer | None = None,
        config_path: str | Path | None = None,
        poll_interval: int = _POLL_INTERVAL,
        cluster: bool = True,
    ) -> None:
        self._logger = logger
        self._engine = engine
        self._config_path = config_path
        self._poll_interval = poll_interval
        self._cluster = cluster
        self._stop_event = threading.Event()

    def _build_engine(self) -> Recognizer:
        """Create an engine from file-backed config data for daemon mode."""
        settings = Config(self._logger, self._config_path).to_settings()
        return Recognizer(self._logger, settings=settings)

    def start(self) -> None:
        """Start polling loop. Runs until stop() is called or KeyboardInterrupt."""
        if self._engine is None:
            self._engine = self._build_engine()

        archive_path = get_archive_path()
        if archive_path is None or not archive_path.exists():
            self._logger.error("Archive path not configured or does not exist")
            return

        try:
            self._engine.poll(archive_path, cluster=self._cluster)
        except ValueError as exc:
            self._logger.error(str(exc))
            return

        self._logger.info(f"Started face-recognizer daemon, polling every {self._poll_interval}s")

        try:
            while not self._stop_event.wait(self._poll_interval):
                assert self._engine is not None
                self._engine.poll(archive_path, cluster=self._cluster)
        except KeyboardInterrupt:
            pass

        self._logger.info("Stopped face-recognizer daemon")

    def stop(self) -> None:
        """Signal the polling loop to stop. Safe to call from any thread."""
        self._stop_event.set()
