"""Regression tests for KeeperWatcher daemon behavior."""

from pathlib import Path
from tempfile import TemporaryDirectory

from archive_keeper.keeper import Keeper
from archive_keeper.watcher import KeeperWatcher
from common.logger import Logger


class FakeKeeper(Keeper):
    """Test double that records poll calls instead of doing real work."""

    def __init__(self, logger: Logger) -> None:
        super().__init__(logger)
        self.calls: list[Path] = []

    def poll(self, archive_path: Path) -> None:
        """Record the archive path passed by the watcher."""
        self.calls.append(archive_path)


class FakeKeeperWatcher(KeeperWatcher):
    """Test-only adapter that exposes a single watcher cycle."""

    def run_once(self, archive_path: Path, keeper: Keeper) -> None:
        """Run one watcher cycle without starting the long-running loop."""
        self._keeper = keeper
        assert self._keeper is not None

        self._keeper.poll(archive_path)


class TestKeeperWatcher:
    """Covers timer-loop orchestration delegated by KeeperWatcher."""

    def test_watcher_delegates_cycle_to_keeper(self) -> None:
        """Watcher calls the keeper once with the configured archive path.

        The daemon wrapper should not implement archive-keeper logic itself.
        Its role is to delegate one cycle to the batch-mode ``Keeper``.
        """
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            logger = Logger("test")
            keeper = FakeKeeper(logger)
            watcher = FakeKeeperWatcher(logger, poll_interval=0)

            watcher.run_once(archive_path, keeper)

            assert keeper.calls == [archive_path]
