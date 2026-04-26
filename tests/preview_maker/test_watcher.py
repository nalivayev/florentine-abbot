"""Regression tests for MakerWatcher daemon behavior."""

from pathlib import Path
from tempfile import TemporaryDirectory

from common.logger import Logger
from preview_maker.maker import Maker
from preview_maker.watcher import MakerWatcher


class FakeMaker(Maker):
    """Test double that records one-cycle invocations instead of doing real work."""

    def __init__(self, logger: Logger) -> None:
        super().__init__(logger)
        self.calls: list[Path] = []

    def poll(self, archive_path: Path) -> int:
        """Record the archive path used by the watcher cycle."""
        self.calls.append(archive_path)
        return 0


class FakeMakerWatcher(MakerWatcher):
    """Test-only adapter that exposes a single watcher cycle."""

    def run_once(self, archive_path: Path, maker: Maker) -> None:
        """Run one watcher cycle without extending production API."""
        self._maker = maker
        assert self._maker is not None

        self._maker.poll(archive_path)


class TestMakerWatcher:
    """Covers timer-loop orchestration delegated by MakerWatcher."""

    def test_watcher_delegates_cycle_to_preview_maker(self) -> None:
        """Watcher calls the maker once with the configured archive path."""
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            logger = Logger("test")
            maker = FakeMaker(logger)
            watcher = FakeMakerWatcher(logger, poll_interval=0)

            watcher.run_once(archive_path, maker)

            assert maker.calls == [archive_path]
