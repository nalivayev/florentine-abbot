"""
ImageOrganizer — atomic copy/move of image files with metadata writing.

Accepts a pre-built mapping of (source, dest, tags) triples and performs
atomic placement. Has no knowledge of naming schemes, routing rules, or
what the tags mean — all of that is the caller's responsibility.
"""

import shutil
import stat
from datetime import datetime, timezone
from pathlib import Path

from common.exifer import Exifer
from common.logger import Logger
from common.tags import Tag
from common.tagger import Tagger
from content_importer.classes import OrganizationReport, OrganizationResult, Organizer


class ImageOrganizer(Organizer):
    """Moves or copies image files atomically and writes metadata tags."""

    def __init__(self, logger: Logger | None = None) -> None:
        self._logger = logger
        self._exifer = Exifer()

    def organize(
        self,
        mapping: list[tuple[Path, Path, list[Tag]]],
        *,
        copy_mode: bool = True,
        protect: bool = False,
    ) -> OrganizationReport:
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
            OrganizationReport with per-file results.
        """
        started_at = datetime.now(timezone.utc)
        results: list[OrganizationResult] = []

        for source, dest, tags in mapping:
            result = self._process_one(source, dest, tags, copy_mode=copy_mode, protect=protect)
            results.append(result)

        finished_at = datetime.now(timezone.utc)
        succeeded = sum(1 for r in results if r.success)

        return OrganizationReport(
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
    ) -> OrganizationResult:
        if dest.exists():
            return OrganizationResult(source=source, dest=dest, error=f"Destination already exists: {dest}")

        tmp = dest.with_suffix(dest.suffix + ".tmp")
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Step 1: copy to tmp
        try:
            shutil.copy2(str(source), str(tmp))
        except OSError as e:
            return OrganizationResult(source=source, dest=dest, error=f"Copy failed: {e}")

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
                return OrganizationResult(source=source, dest=dest, error=f"Metadata write failed: {e}")

        # Step 3: atomic rename tmp → dest
        try:
            tmp.rename(dest)
        except OSError as e:
            self._cleanup(tmp)
            return OrganizationResult(source=source, dest=dest, error=f"Rename failed: {e}")

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

        return OrganizationResult(source=source, dest=dest, success=True, copied_at=datetime.now(timezone.utc))

    def _cleanup(self, path: Path) -> None:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass
