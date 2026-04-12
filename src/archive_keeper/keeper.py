"""
Archive Keeper — core logic for archive integrity checks.

Responsible for:
- Calculating file checksums (SHA-256)
- Detecting missing files (in DB but not on disk)
- Verifying checksums of existing files

Has no knowledge of polling, database connections, or scheduling.
All of that is the caller's responsibility.
"""

import hashlib
from pathlib import Path

from common.logger import Logger

# 64 MB chunks — efficient for large files (2 GB+ TIFFs)
_CHUNK_SIZE = 64 * 1024 * 1024
# Log progress for files larger than 100 MB
_PROGRESS_THRESHOLD = 100 * 1024 * 1024


class ArchiveKeeper:
    """Core logic for archive integrity checks."""

    def __init__(self, logger: Logger, chunk_size: int = _CHUNK_SIZE) -> None:
        self._logger = logger
        self._chunk_size = chunk_size

    def calculate(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file.

        Logs progress for large files.

        Args:
            file_path: Path to the file.

        Returns:
            Hex SHA-256 digest string.
        """
        file_size = file_path.stat().st_size
        sha256 = hashlib.sha256()
        log_progress = file_size > _PROGRESS_THRESHOLD

        if log_progress:
            self._logger.info(
                f"Hashing large file ({file_size / (1024 ** 3):.2f} GB): {file_path.name}"
            )

        bytes_read = 0
        last_logged = 0

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(self._chunk_size), b""):
                sha256.update(chunk)
                if log_progress:
                    bytes_read += len(chunk)
                    percent = int(bytes_read / file_size * 100)
                    if percent >= last_logged + 25:
                        self._logger.info(f"  {percent}% ({bytes_read / (1024 ** 3):.2f} GB)")
                        last_logged = percent

        if log_progress:
            self._logger.info(f"  Done: {file_path.name}")

        return sha256.hexdigest()
