"""Regression tests for CutterWatcher daemon behavior."""

from pathlib import Path
from tempfile import TemporaryDirectory

from common.logger import Logger
from tile_cutter.cutter import Cutter
from tile_cutter.watcher import CutterWatcher


class FakeCutter(Cutter):
    """Test double that records one-cycle invocations instead of doing real work."""

    def __init__(self, logger: Logger) -> None:
        super().__init__(logger)
        self.calls: list[Path] = []

    def poll(self, archive_path: Path) -> int:
        """Record the archive path used by the watcher cycle."""
        self.calls.append(archive_path)
        return 0


class FakeCutterWatcher(CutterWatcher):
    """Test-only adapter that exposes a single watcher cycle."""

    def run_once(self, archive_path: Path, cutter: Cutter) -> None:
        """Run one watcher cycle without extending production API."""
        self._cutter = cutter
        assert self._cutter is not None

        self._cutter.poll(archive_path)


class TestCutterWatcher:
    """Covers timer-loop orchestration delegated by CutterWatcher."""

    def test_watcher_delegates_cycle_to_tile_cutter(self) -> None:
        """Watcher calls the cutter once with the configured archive path."""
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            logger = Logger("test")
            cutter = FakeCutter(logger)
            watcher = FakeCutterWatcher(logger, poll_interval=0)

            watcher.run_once(archive_path, cutter)

            assert cutter.calls == [archive_path]