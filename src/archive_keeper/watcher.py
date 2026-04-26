"""Polling-based daemon wrapper for Archive Keeper batch reconciliation."""

import threading

from common.config_utils import get_archive_path
from common.logger import Logger
from archive_keeper.keeper import Keeper

_POLL_INTERVAL = 60  # seconds


class KeeperWatcher:
    """Polls on a timer and delegates each pass to :class:`Keeper`."""

    def __init__(
        self,
        logger: Logger,
        *,
        keeper: Keeper | None = None,
        poll_interval: int = _POLL_INTERVAL,
    ) -> None:
        self._logger = logger
        self._keeper = keeper
        self._poll_interval = poll_interval
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start polling loop. Runs until stop() is called or KeyboardInterrupt."""
        if self._keeper is None:
            self._keeper = Keeper(self._logger)

        archive_path = get_archive_path()
        if archive_path is None or not archive_path.exists():
            self._logger.error("Archive path not configured or does not exist")
            return

        try:
            self._keeper.poll(archive_path)
        except ValueError as exc:
            self._logger.error(str(exc))
            return

        self._logger.info(
            f"Started archive-keeper daemon, polling every {self._poll_interval}s"
        )

        try:
            while not self._stop_event.wait(self._poll_interval):
                assert self._keeper is not None
                self._keeper.poll(archive_path)
        except KeyboardInterrupt:
            pass

        self._logger.info("Stopped archive-keeper daemon")

    def stop(self) -> None:
        """Signal the polling loop to stop. Safe to call from any thread."""
        self._stop_event.set()
