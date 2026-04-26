"""Polling-based daemon wrapper for Tile Cutter orchestration."""

import threading
from pathlib import Path

from common.config_utils import get_archive_path, get_config_dir
from common.logger import Logger
from common.project_config import ProjectConfig
from tile_cutter.config import Config
from tile_cutter.cutter import Cutter

_POLL_INTERVAL = 30  # seconds


class CutterWatcher:
    """Polls on a timer and delegates each pass to :class:`Cutter`."""

    def __init__(
        self,
        logger: Logger,
        *,
        cutter: Cutter | None = None,
        config_path: str | Path | None = None,
        poll_interval: int = _POLL_INTERVAL,
    ) -> None:
        self._logger = logger
        self._cutter = cutter
        self._config_path = config_path
        self._poll_interval = poll_interval
        self._stop_event = threading.Event()

    def _build_cutter(self) -> Cutter:
        """Create a cutter from file-backed config data for daemon mode."""
        project_data = ProjectConfig.instance(
            logger=self._logger,
            config_path=get_config_dir() / "config.json",
        ).data
        settings = Config(self._logger, self._config_path).to_settings(
            project_data=project_data,
        )
        return Cutter(self._logger, settings=settings)

    def start(self) -> None:
        """Start polling loop. Runs until stop() is called or KeyboardInterrupt."""
        if self._cutter is None:
            self._cutter = self._build_cutter()

        archive_path = get_archive_path()
        if archive_path is None or not archive_path.exists():
            self._logger.error("Archive path not configured or does not exist")
            return

        try:
            self._cutter.poll(archive_path)
        except ValueError as exc:
            self._logger.error(str(exc))
            return

        self._logger.info(
            f"Started tile-cutter daemon, polling every {self._poll_interval}s"
        )

        try:
            while not self._stop_event.wait(self._poll_interval):
                assert self._cutter is not None
                self._cutter.poll(archive_path)
        except KeyboardInterrupt:
            pass

        self._logger.info("Stopped tile-cutter daemon")

    def stop(self) -> None:
        """Signal the polling loop to stop. Safe to call from any thread."""
        self._stop_event.set()
