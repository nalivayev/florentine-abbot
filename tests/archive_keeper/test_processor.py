"""Regression tests for KeeperProcessor file-level behavior."""

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

from archive_keeper.processor import KeeperProcessor
from common.logger import Logger


class TestKeeperProcessor:
    """Covers low-level checksum calculation without DB orchestration."""

    @staticmethod
    def _checksum(file_path: Path) -> str:
        """Return the SHA-256 checksum of a test file."""
        return hashlib.sha256(file_path.read_bytes()).hexdigest()

    def test_process_returns_sha256_for_file(self) -> None:
        """Processor returns the expected SHA-256 digest for a file."""
        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "scan.tif"
            file_path.write_bytes(b"archive keeper processor test")

            processor = KeeperProcessor(Logger("test_keeper_processor"))

            assert processor.process(file_path) == self._checksum(file_path)
