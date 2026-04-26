"""Regression tests for RecognizerWatcher daemon behavior."""

from pathlib import Path
from tempfile import TemporaryDirectory

from common.logger import Logger
from face_recognizer.recognizer import Recognizer
from face_recognizer.watcher import RecognizerWatcher


class FakeRecognizer(Recognizer):
    """Test double that records one-cycle invocations instead of doing real work."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger
        self.calls: list[tuple[Path, bool]] = []

    def poll(self, archive_path: Path, *, cluster: bool = True) -> int:
        self.calls.append((archive_path, cluster))
        return 0


class FakeRecognizerWatcher(RecognizerWatcher):
    """Test-only adapter that exposes a single watcher cycle."""

    def run_once(self, archive_path: Path, engine: Recognizer) -> None:
        self._engine = engine
        assert self._engine is not None

        self._engine.poll(archive_path, cluster=self._cluster)


class TestRecognizerWatcher:
    """Covers timer-loop orchestration delegated by RecognizerWatcher."""

    def test_watcher_delegates_cycle_to_recognizer(self) -> None:
        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir)
            logger = Logger("test")
            engine = FakeRecognizer(logger)
            watcher = FakeRecognizerWatcher(logger, poll_interval=0)

            watcher.run_once(archive_path, engine)

            assert engine.calls == [(archive_path, True)]