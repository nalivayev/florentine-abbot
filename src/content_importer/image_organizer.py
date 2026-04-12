"""
ImageOrganizer — atomic copy/move of image files with metadata writing.

Accepts a pre-built mapping of (source, dest, tags) triples and performs
atomic placement. Has no knowledge of naming schemes, routing rules, or
what the tags mean — all of that is the caller's responsibility.
"""

import shutil
import stat
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from common.exifer import Exifer
from common.logger import Logger
from common.tags import Tag
from common.tagger import Tagger


@dataclass
class FileResult:
    source: Path
    dest: Path | None = None
    success: bool = False
    copied_at: datetime | None = None
    error: str | None = None


@dataclass
class OrganizerReport:
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    results: list[FileResult] = field(default_factory=list[FileResult])


class ImageOrganizer:
    """Moves or copies image files atomically and writes metadata tags."""

    def __init__(self, logger: Logger | None = None) -> None:
        self._logger = logger
        self._exifer = Exifer()

    def process(
        self,
        mapping: list[tuple[Path, Path, list[Tag]]],
        *,
        copy_mode: bool = True,
        protect: bool = False,
    ) -> OrganizerReport:
        """Process a list of (source, dest, tags) triples.

        For each triple:
          1. Copy source → dest.tmp  (atomic intermediate)
          2. Write tags to dest.tmp  (single exiftool call)
          3. Rename dest.tmp → dest
          4. Optionally make dest read-only
          5. Delete source if move mode

        Args:
            mapping: List of (source_path, dest_path, tags) tuples.
                     Tags are written to the destination file for each entry.
            copy_mode: If True, keep source files. If False, delete after success.
            protect: If True, make destination read-only after placement.

        Returns:
            OrganizerReport with per-file results.
        """
        started_at = datetime.now(timezone.utc)
        results: list[FileResult] = []

        for source, dest, tags in mapping:
            result = self._process_one(source, dest, tags, copy_mode=copy_mode, protect=protect)
            results.append(result)

        finished_at = datetime.now(timezone.utc)
        succeeded = sum(1 for r in results if r.success)

        return OrganizerReport(
            started_at=started_at,
            finished_at=finished_at,
            total=len(results),
            succeeded=succeeded,
            failed=len(results) - succeeded,
            results=results,
        )

    def _process_one(
        self,
        source: Path,
        dest: Path,
        tags: list[Tag],
        *,
        copy_mode: bool,
        protect: bool,
    ) -> FileResult:
        if dest.exists():
            return FileResult(source=source, dest=dest, error=f"Destination already exists: {dest}")

        tmp = dest.with_suffix(dest.suffix + ".tmp")
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Step 1: copy to tmp
        try:
            shutil.copy2(str(source), str(tmp))
        except OSError as e:
            return FileResult(source=source, dest=dest, error=f"Copy failed: {e}")

        # Step 2: write tags to tmp
        if tags:
            try:
                tagger = Tagger(tmp, exifer=self._exifer)
                tagger.begin()
                for tag in tags:
                    tagger.write(tag)
                tagger.end()
            except Exception as e:
                self._cleanup(tmp)
                return FileResult(source=source, dest=dest, error=f"Metadata write failed: {e}")

        # Step 3: atomic rename tmp → dest
        try:
            tmp.rename(dest)
        except OSError as e:
            self._cleanup(tmp)
            return FileResult(source=source, dest=dest, error=f"Rename failed: {e}")

        # Step 4: protect
        if protect:
            try:
                mode = dest.stat().st_mode
                dest.chmod(mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
            except OSError as e:
                if self._logger:
                    self._logger.warning("Failed to set read-only on %s: %s", dest, e)

        # Step 5: delete source if move mode
        if not copy_mode:
            try:
                source.unlink()
            except OSError as e:
                if self._logger:
                    self._logger.warning("Failed to delete source %s: %s", source, e)

        return FileResult(source=source, dest=dest, success=True, copied_at=datetime.now(timezone.utc))

    def _cleanup(self, path: Path) -> None:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass
