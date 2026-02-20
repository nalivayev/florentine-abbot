"""
StoreExifer for testing - stores tags in memory.
"""

from pathlib import Path
from typing import Any

from common.exifer import Exifer


class StoreExifer(Exifer):
    """Exifer double that keeps an in-memory store of tags per file.

    - read() returns requested tags from the store (or all known for the file).
    - write() updates the store for the file.
    This simulates the organizer/maker cycle without invoking exiftool.
    """

    def __init__(self) -> None:
        # Avoid starting real exiftool; we only keep an in-memory store.
        self.executable = "exiftool"
        self.store: dict[Path, dict[str, Any]] = {}

    def read(self, file_path: Path, tag_names: list[str]) -> dict[str, Any]:
        tags = self.store.get(file_path, {})
        if not tag_names:
            return dict(tags)
        # Return only requested keys if known
        return {k: v for k, v in tags.items() if k in tag_names or k in tags}

    def write(
        self,
        file_path: Path,
        tags: dict[str, Any],
        overwrite_original: bool = True,
        timeout: int | None = None,
    ) -> None:
        existing = self.store.setdefault(file_path, {})
        existing.update({k: v for k, v in tags.items() if v is not None})
