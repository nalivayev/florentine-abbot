"""
Common utilities.
"""

import time
from pathlib import Path

from common.constants import EXIFTOOL_LARGE_FILE_TIMEOUT


def wait_for_stable(
    path: Path,
    interval: float = 1.0,
    stable_for: float = 3.0,
    timeout: float = EXIFTOOL_LARGE_FILE_TIMEOUT,
) -> None:
    """
    Block until *path* stops growing.

    Polls the file size every *interval* seconds.  Returns once the size has
    remained unchanged for *stable_for* seconds.

    Use for on_created events (copy, cross-filesystem move) where the writer
    may still hold the file open.  Not needed for on_moved events, which are
    always atomic renames and arrive complete.

    Args:
        path: File to monitor.
        interval: Polling interval in seconds.
        stable_for: How long (seconds) the size must stay the same.
        timeout: Maximum total wait time in seconds (defaults to
            EXIFTOOL_LARGE_FILE_TIMEOUT to keep large-file handling consistent).

    Raises:
        OSError: If the file cannot be accessed (e.g. it disappeared).
        TimeoutError: If the file has not stabilised within *timeout* seconds.
    """
    deadline = time.monotonic() + timeout
    prev_size: int = -1
    stable_since: float | None = None

    while time.monotonic() < deadline:
        size = path.stat().st_size  # raises OSError if file disappears

        if size != prev_size:
            prev_size = size
            stable_since = time.monotonic()
        elif stable_since is not None and (time.monotonic() - stable_since) >= stable_for:
            return

        time.sleep(interval)

    raise TimeoutError(f"File did not stabilise within {timeout}s: {path}")
