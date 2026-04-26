"""High-level batch and database-backed orchestration for Tile Cutter."""

from datetime import datetime, timezone
import fnmatch
from pathlib import Path
from typing import Any

from common.database import FILE_STATUS_MODIFIED
from common.logger import Logger
from common.constants import SUPPORTED_IMAGE_EXTENSIONS, ARCHIVE_SYSTEM_DIR
from tile_cutter.constants import TILES_DIR
from common.formatter import Formatter
from tile_cutter.classes import CutterSettings
from tile_cutter.processor import CutterProcessor
from tile_cutter.store import CutterStore


class Cutter:
    """Tile orchestration layer for batch and daemon modes."""

    def __init__(
        self,
        logger: Logger,
        settings: CutterSettings | None = None,
    ) -> None:
        self._logger = logger
        self._settings = settings or CutterSettings.from_data()

        self._formatter = Formatter(logger=logger, formats=self._settings.formats)
        self._processor = CutterProcessor(logger)

    def execute(
        self,
        *,
        path: Path,
        overwrite: bool = False,
    ) -> int:
        """Run batch tile generation under ``path``."""
        if not path.exists():
            raise ValueError(f"Archive path does not exist: {path}")

        return self._generate_tiles_for_sources(path=path, overwrite=overwrite)

    def poll(self, archive_path: Path) -> int:
        """Process DB-backed tile tasks for files pending in the archive."""
        if not archive_path.exists():
            raise ValueError(f"Archive path does not exist: {archive_path}")

        with CutterStore(archive_path) as store:
            rows = store.list_pending_files()

            if not rows:
                return 0

            self._logger.info(f"Found {len(rows)} file(s) to process")

            for row in rows:
                self._process_pending_file(
                    store,
                    file_id=row.file_id,
                    rel_path=row.rel_path,
                    file_status=row.status,
                    archive_path=archive_path,
                )

            return len(rows)

    def _should_process(self, file_path: Path) -> bool:
        """Check whether a file is eligible for tile generation.

        Checks:

        - Not a symlink
        - Has a supported image extension
        - Filename matches one of the configured ``source_priority`` patterns
        - No higher-priority source sibling exists for the same shot

        Args:
            file_path: Path to the candidate file.

        Returns:
            True if the file should be processed, False otherwise.
        """
        if file_path.is_symlink():
            self._logger.debug(f"Skipping {file_path}: is symlink")
            return False

        if file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            self._logger.debug(f"Skipping {file_path}: unsupported extension '{file_path.suffix}'")
            return False

        parsed = self._formatter.parse(file_path)
        if not parsed:
            self._logger.debug(f"Skipping {file_path}: cannot parse filename")
            return False

        my_priority = self._get_match_priority(file_path.name)
        if my_priority is None:
            self._logger.debug(
                f"Skipping {file_path}: does not match any source_priority pattern"
            )
            return False

        # If a higher-priority source exists for the same shot, skip.
        if my_priority > 0:
            for sibling in file_path.parent.iterdir():
                if sibling == file_path or not sibling.is_file():
                    continue
                sib_priority = self._get_match_priority(sibling.name)
                if sib_priority is not None and sib_priority < my_priority:
                    sib_parsed = self._formatter.parse(sibling)
                    if sib_parsed and self._same_shot(parsed, sib_parsed):
                        self._logger.debug(
                            f"Skipping {file_path.name}: higher-priority source exists ({sibling.name})"
                        )
                        return False

        return True

    def _process_single_file(
        self,
        src_path: Path,
        *,
        archive_path: Path,
        overwrite: bool = False,
    ) -> bool:
        """Generate tiles for a single source file.

        Args:
            src_path: Source file matching one of the ``source_priority`` patterns.
            archive_path: Resolved archive root.
            overwrite: If True, regenerate existing tile sets.

        Returns:
            True if tiles were generated, False otherwise.
        """
        parsed = self._formatter.parse(src_path)
        if not parsed:
            raise ValueError(f"Cannot parse filename: {src_path.name}")

        tile_dir = self._build_output_dir(src_path, archive_path=archive_path)
        count, output_dir = self._processor.process(
            src_path,
            output_dir=tile_dir,
            preview_size=self._settings.preview_size,
            tile_size=self._settings.tile_size,
            overwrite=overwrite,
        )

        if count == 0:
            return False

        self._logger.info(f"Saved {count} tile(s) to {output_dir}")
        return True

    def _build_output_dir(self, src_path: Path, *, archive_path: Path) -> Path:
        """Return the tile output directory for *src_path* under *archive_path*."""
        rel = src_path.relative_to(archive_path)
        return archive_path / ARCHIVE_SYSTEM_DIR / TILES_DIR / Path(*rel.parts[:-1]) / src_path.stem

    def _generate_tiles_for_sources(
        self,
        *,
        path: Path,
        overwrite: bool,
    ) -> int:
        """Walk under *path* and generate tile sets for matching source files.

        Skips the ``ARCHIVE_SYSTEM_DIR`` subtree to avoid processing derivative files.
        """
        written = 0

        self._logger.debug(
            f"Starting batch tile generation under {path} "
            f"(overwrite={overwrite}, size={self._settings.preview_size}, "
            f"tile_size={self._settings.tile_size})"
        )

        for src_path in path.rglob("*"):
            if not src_path.is_file():
                continue
            # Skip anything inside ARCHIVE_SYSTEM_DIR/
            if ARCHIVE_SYSTEM_DIR in src_path.parts:
                continue
            if not self._should_process(src_path):
                continue
            try:
                if self._process_single_file(
                    src_path,
                    archive_path=path,
                    overwrite=overwrite,
                ):
                    written += 1
            except Exception as e:
                self._logger.error(f"Error processing {src_path.name}: {e}")

        self._logger.info(f"Finished batch tile generation: {written} tile set(s) written")
        return written

    def _process_pending_file(
        self,
        store: CutterStore,
        *,
        file_id: int,
        rel_path: str,
        file_status: str,
        archive_path: Path,
    ) -> None:
        """Process one DB-backed tile task candidate."""
        def now() -> str:
            return datetime.now(timezone.utc).isoformat()

        store.start_task(file_id, now())

        src_path = archive_path / rel_path

        if not src_path.exists():
            self._logger.warning(f"File not found, skipping: {src_path}")
            store.mark_failed(file_id, "File not found", now())
            return

        try:
            if not self._should_process(src_path):
                store.mark_skipped(file_id, now())
            else:
                self._process_single_file(
                    src_path,
                    archive_path=archive_path,
                    overwrite=file_status == FILE_STATUS_MODIFIED,
                )
                store.mark_done(file_id, now())
        except Exception as e:
            self._logger.error(f"Error processing {src_path.name}: {e}")
            store.mark_failed(file_id, str(e), now())

    def _get_match_priority(self, filename: str) -> int | None:
        """Return the priority index of the first matching source pattern.

        Returns *None* when the filename does not match any pattern.
        """
        for i, pattern in enumerate(self._settings.source_priority):
            if fnmatch.fnmatch(filename.upper(), pattern.upper()):
                return i
        return None

    @staticmethod
    def _same_shot(a: dict[str, Any], b: dict[str, Any]) -> bool:
        """Check whether two parsed filenames represent the same shot."""
        return (
            a["year"]     == b["year"]
            and a["month"]    == b["month"]
            and a["day"]      == b["day"]
            and a["hour"]     == b["hour"]
            and a["minute"]   == b["minute"]
            and a["second"]   == b["second"]
            and a["modifier"] == b["modifier"]
            and a["group"]    == b["group"]
            and a["subgroup"] == b["subgroup"]
            and a["sequence"] == b["sequence"]
            and a["side"]     == b["side"]
        )
