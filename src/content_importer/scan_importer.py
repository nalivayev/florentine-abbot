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
from typing import Any

from common.constants import SUPPORTED_IMAGE_EXTENSIONS, TAG_EXIF_DATETIME_ORIGINAL, TAG_XMP_DC_IDENTIFIER, TAG_XMP_PHOTOSHOP_DATE_CREATED, TAG_XMP_XMP_IDENTIFIER, TAG_XMP_XMPMM_INSTANCE_ID, XMP_ACTION_MANAGED
from common.metadata import ArchiveMetadata
from common.tags import HistoryTag, KeyValueTag, Tag
from common.version import get_version
from content_importer.classes import Importer, OrganizationReport, ValidationReport, ValidationResult
from content_importer.image_organizer import ImageOrganizer
from content_importer.scan_validator import ScanResult, ScanValidator
from content_importer.store import ImporterStore


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
        metadata_config: dict[str, Any] | None = None,
    ) -> ValidationReport:
        """Validate and import all supported files from *source_path*.

        Args:
            source_path: Folder containing files to import.
            archive_path: Archive root directory (files land under it).
            recursive: If True, descend into subdirectories.
            copy_mode: If True, keep source files; if False, delete after success.
            protect: If True, make destination files read-only.

        Returns:
            ValidationReport with batch summary and per-file results.
        """
        started_at = datetime.now(timezone.utc)

        files = self._collect_files(source_path, recursive=recursive)

        # --- Validate all files first ---
        results: list[ValidationResult] = []
        valid_mapping: list[tuple[Path, Path, list[Tag]]] = []
        db_projection_by_source: dict[Path, dict[str, Any]] = {}

        for file_path in files:
            result = self._validator.validate(file_path, collection_id=collection_id, collection_type=collection_type)
            results.append(result)

            if result.valid and result.dest is not None:
                dest = archive_path / result.dest
                tags, db_projection = self._build_tags(result, metadata_config=metadata_config)
                valid_mapping.append((file_path, dest, tags))
                db_projection_by_source[file_path] = db_projection

        # --- Organise valid files ---
        org_report: OrganizationReport | None = None
        if valid_mapping:
            org_report = self._organizer.organize(
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
        self._register_in_db(
            org_report,
            archive_path,
            collection_id=collection_id,
            db_projection_by_source=db_projection_by_source,
        )

        finished_at = datetime.now(timezone.utc)

        valid_count = sum(1 for r in results if r.valid)
        succeeded = sum(1 for r in results if r.copied)

        return ValidationReport(
            started_at=started_at,
            finished_at=finished_at,
            total=len(results),
            valid=valid_count,
            succeeded=succeeded,
            failed=len(results) - succeeded,
            results=results,
        )

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
        org_report: OrganizationReport | None,
        archive_path: Path,
        *,
        collection_id: int | None = None,
        db_projection_by_source: dict[Path, dict[str, Any]] | None = None,
    ) -> None:
        """Register successfully copied files in the database."""
        if org_report is None:
            return
        projections = db_projection_by_source or {}
        imported_files: list[dict[str, Any]] = []
        for file_result in org_report.results:
            if not file_result.success or file_result.dest is None or file_result.copied_at is None:
                continue
            projection = dict(projections.get(file_result.source, {}))
            projection["dest_path"] = file_result.dest
            projection["imported_at"] = file_result.copied_at.isoformat()
            imported_files.append(projection)
        if not imported_files:
            return

        ImporterStore(archive_path).register_imported_files(
            collection_id=collection_id,
            files=imported_files,
        )

    def _build_tags(
        self,
        result: ScanResult,
        *,
        metadata_config: dict[str, Any] | None = None,
    ) -> tuple[list[Tag], dict[str, Any]]:
        """Build tags to write to each imported file.

        Writes:
        - Archive identifiers used by later derivative builders.
        - Archive date tags derived from the filename.
        - A new InstanceID (UUID) reflecting the post-import state.
        - An XMP History entry describing the import-time metadata update.
        """
        parsed = result.parsed
        if parsed is None:
            raise ValueError(f"Validated scan result is missing parsed filename data: {result.source}")

        archive_identifier = uuid.uuid4().hex
        new_instance_id = uuid.uuid4().hex
        agent = f"content-importer {get_version()}"
        when = datetime.now().astimezone()
        metadata_provider = ArchiveMetadata(metadata=metadata_config)

        tags: list[Tag] = [
            KeyValueTag(TAG_XMP_DC_IDENTIFIER, archive_identifier),
            KeyValueTag(TAG_XMP_XMP_IDENTIFIER, archive_identifier),
        ]

        metadata_values = metadata_provider.get_metadata_values()
        for tag_name, value in metadata_values.items():
            tags.append(KeyValueTag(tag_name, value))

        semantic_values = metadata_provider.get_default_language_values()

        exact_modifier = str(parsed["modifier"]) == "E"
        modifier = str(parsed["modifier"])
        year = int(parsed["year"])
        month = int(parsed["month"])
        day = int(parsed["day"])
        hour = int(parsed["hour"])
        minute = int(parsed["minute"])
        second = int(parsed["second"])

        if exact_modifier:
            dt_str = f"{year:04d}:{month:02d}:{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
            tags.append(KeyValueTag(TAG_EXIF_DATETIME_ORIGINAL, dt_str))
            tags.append(
                KeyValueTag(
                    TAG_XMP_PHOTOSHOP_DATE_CREATED,
                    dt_str.replace(":", "-", 2).replace(" ", "T"),
                )
            )
        else:
            tags.append(KeyValueTag(TAG_EXIF_DATETIME_ORIGINAL, ""))
            if year > 0:
                partial_date = f"{year:04d}"
                if month > 0:
                    partial_date += f"-{month:02d}"
                    if day > 0:
                        partial_date += f"-{day:02d}"
                tags.append(KeyValueTag(TAG_XMP_PHOTOSHOP_DATE_CREATED, partial_date))

        tags.extend([
            KeyValueTag(TAG_XMP_XMPMM_INSTANCE_ID, new_instance_id),
            HistoryTag(
                action=XMP_ACTION_MANAGED,
                when=when,
                software_agent=agent,
                changed="metadata",
                instance_id=new_instance_id,
            ),
        ])

        db_projection: dict[str, Any] = {
            "metadata": {
                "photo_year": year if year > 0 else None,
                "photo_month": month if month > 0 else None,
                "photo_day": day if day > 0 else None,
                "photo_time": f"{hour:02d}:{minute:02d}:{second:02d}" if exact_modifier else None,
                "date_accuracy": self._map_date_accuracy(modifier),
                "description": semantic_values.get("description"),
                "source": semantic_values.get("source"),
                "credit": semantic_values.get("credit"),
            },
            "creators": semantic_values.get("creator", []),
            "history": [
                {
                    "action": XMP_ACTION_MANAGED,
                    "recorded_at": when.isoformat(),
                    "software": agent,
                    "changed": "metadata",
                    "instance_id": new_instance_id,
                }
            ],
        }

        return tags, db_projection

    @staticmethod
    def _map_date_accuracy(modifier: str) -> str:
        return {
            "E": "exact",
            "B": "before",
            "C": "circa",
            "F": "after",
        }.get(modifier, "unknown")
