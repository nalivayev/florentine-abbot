from pathlib import Path
from typing import Any

from common.exifer import Exifer


class FakeExifer(Exifer):
    """Test double for Exifer to avoid external exiftool dependency."""

    def __init__(self, read_map: dict[Path, dict[str, Any]] | None = None) -> None:
        # Bypass Exifer.__init__ (no real exiftool needed in tests)
        # and only keep the minimal state we care about.
        self.executable = "exiftool"
        self.read_map = read_map or {}
        self.writes: list[tuple[Path, dict[str, Any]]] = []

    def read(self, file_path: Path, tag_names: list[str]) -> dict[str, Any]:
        # Return only requested keys if present in map
        existing = self.read_map.get(file_path, {})
        return {k: v for k, v in existing.items() if k in tag_names or k in existing}

    def write(
        self,
        file_path: Path,
        tags: dict[str, Any],
        overwrite_original: bool = True,
        timeout: int | None = None,
    ) -> None:
        # Record writes for assertions
        self.writes.append((file_path, dict(tags)))
