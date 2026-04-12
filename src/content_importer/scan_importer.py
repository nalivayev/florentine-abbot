"""
ScanImporter — imports scan-batcher output into the archive.

Responsibilities:
1. Enumerate supported image files in the source folder.
2. Validate each file via ScanValidator (filename scheme + XMP identifiers).
3. Build per-file tags: new InstanceID + History entry referencing the previous one.
4. Pass the validated mapping to ImageOrganizer for atomic copy/move.
5. Return a structured report.
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from common.constants import SUPPORTED_IMAGE_EXTENSIONS, TAG_XMP_XMPMM_INSTANCE_ID, XMP_ACTION_MANAGED
from common.db import get_conn, FILE_STATUS_NEW
from common.tags import HistoryTag, KeyValueTag, Tag
from common.version import get_version
from content_importer.classes import Importer, Report, Result
from content_importer.image_organizer import ImageOrganizer, OrganizerReport
from content_importer.scan_validator import ScanResult, ScanValidator


class ScanImporter(Importer):
    """Imports scan-batcher output files into the archive."""

    def __init__(self) -> None:
        self._validator = ScanValidator()
        self._organizer = ImageOrganizer()

    def run(
        self,
        source_path: Path,
        archive_path: Path,
        *,
        collection_id: int | None = None,
        collection_type: str = "scan",
        recursive: bool = False,
        copy_mode: bool = True,
        protect: bool = False,
    ) -> Report:
        """Validate and import all supported files from *source_path*.

        Args:
            source_path: Folder containing files to import.
            archive_path: Archive root directory (files land under it).
            recursive: If True, descend into subdirectories.
            copy_mode: If True, keep source files; if False, delete after success.
            protect: If True, make destination files read-only.

        Returns:
            Report with batch summary and per-file results.
        """
        started_at = datetime.now(timezone.utc)

        files = self._collect_files(source_path, recursive=recursive)

        # --- Validate all files first ---
        results: list[Result] = []
        valid_mapping: list[tuple[Path, Path, list[Tag]]] = []

        for file_path in files:
            result = self._validator.validate(file_path, collection_id=collection_id, collection_type=collection_type)
            results.append(result)

            if result.valid and result.dest is not None:
                dest = archive_path / result.dest
                tags = self._build_tags(result)
                valid_mapping.append((file_path, dest, tags))

        # --- Organise valid files ---
        org_report: OrganizerReport | None = None
        if valid_mapping:
            org_report = self._organizer.process(
                valid_mapping,
                copy_mode=copy_mode,
                protect=protect,
            )
            org_by_source = {r.source: r for r in org_report.results}
            for result in results:
                if result.valid:
                    org_result = org_by_source.get(result.source)
                    if org_result is not None:
                        if org_result.success:
                            result.copied = True
                        else:
                            result.errors.append(org_result.error or "Unknown organizer error")

        # --- Register successfully imported files in the database ---
        self._register_in_db(org_report, archive_path, collection_id=collection_id)

        finished_at = datetime.now(timezone.utc)

        valid_count = sum(1 for r in results if r.valid)
        succeeded = sum(1 for r in results if r.copied)

        return Report(
            started_at=started_at,
            finished_at=finished_at,
            total=len(results),
            valid=valid_count,
            succeeded=succeeded,
            failed=len(results) - succeeded,
            results=results,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _collect_files(self, source_path: Path, *, recursive: bool) -> list[Path]:
        iterator = source_path.rglob("*") if recursive else source_path.iterdir()
        return [
            f for f in iterator
            if f.is_file()
            and not f.is_symlink()
            and f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
        ]

    def _register_in_db(
        self,
        org_report: OrganizerReport | None,
        archive_path: Path,
        *,
        collection_id: int | None = None,
    ) -> None:
        """Register successfully copied files in the database."""
        if org_report is None:
            return
        try:
            conn = get_conn()
        except RuntimeError:
            return  # DB not initialized (e.g. running outside web context)

        for file_result in org_report.results:
            if not file_result.success or file_result.dest is None or file_result.copied_at is None:
                continue
            rel_path = str(file_result.dest.relative_to(archive_path))
            conn.execute(
                "INSERT OR IGNORE INTO files (collection_id, path, status, imported_at) VALUES (?, ?, ?, ?)",
                (collection_id, rel_path, FILE_STATUS_NEW, file_result.copied_at.isoformat()),
            )
        conn.commit()

    def _build_tags(self, result: ScanResult) -> list[Tag]:
        """Build tags to write to each imported file.

        Writes:
        - A new InstanceID (UUID) reflecting the post-import state.
        - An XMP History entry with the previous InstanceID to preserve the chain.
        """
        prev_instance_id = result.metadata.get(TAG_XMP_XMPMM_INSTANCE_ID)
        new_instance_id = f"xmp.iid:{uuid.uuid4()}"
        agent = f"content-importer {get_version()}"
        when = datetime.now(timezone.utc)

        return [
            KeyValueTag(TAG_XMP_XMPMM_INSTANCE_ID, new_instance_id),
            HistoryTag(
                action=XMP_ACTION_MANAGED,
                when=when,
                software_agent=agent,
                instance_id=prev_instance_id,
            ),
        ]
