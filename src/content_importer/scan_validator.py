"""
Validator for files processed by scan-batcher.

Expects:
- File name matching the archive naming scheme (parsed by Formatter)
- XMP DocumentID and InstanceID set by scan-batcher
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from common.constants import TAG_XMP_XMPMM_DOCUMENT_ID, TAG_XMP_XMPMM_INSTANCE_ID
from common.exifer import Exifer
from common.formatter import Formatter
from common.logger import Logger
from common.project_config import ProjectConfig
from common.tagger import Tagger
from common.tags import KeyValueTag
from content_importer.classes import Result, Validator


@dataclass
class ScanResult(Result):
    """Validation result for a scan-batcher output file.

    Extends Result with scan-specific fields: parsed filename components
    and XMP metadata read during validation, so the importer can reuse
    them without a second exiftool call.
    """
    parsed: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])


class ScanValidator(Validator):
    """Validator for scan-batcher output files."""

    def __init__(self, logger: Logger | None = None) -> None:
        cfg = ProjectConfig.instance()
        self._formatter = Formatter(formats=cfg.formats)
        self._exifer = Exifer()

    def validate(self, file_path: Path, collection_id: int | None = None, collection_type: str = "scan") -> ScanResult:
        # 1. Parse filename
        parsed = self._formatter.parse(file_path)
        if parsed is None:
            return ScanResult(
                source=file_path,
                valid=False,
                errors=["File name does not match the archive naming scheme"],
            )

        # 2. Validate filename fields
        errors = self._formatter.validate(parsed)
        if errors:
            return ScanResult(source=file_path, valid=False, errors=errors)

        # 3. Check XMP identifiers
        tagger = Tagger(file_path, exifer=self._exifer)
        tagger.begin()
        tagger.read(KeyValueTag(TAG_XMP_XMPMM_DOCUMENT_ID))
        tagger.read(KeyValueTag(TAG_XMP_XMPMM_INSTANCE_ID))
        existing = tagger.end() or {}

        missing: list[str] = []
        if not existing.get(TAG_XMP_XMPMM_DOCUMENT_ID):
            missing.append(TAG_XMP_XMPMM_DOCUMENT_ID)
        if not existing.get(TAG_XMP_XMPMM_INSTANCE_ID):
            missing.append(TAG_XMP_XMPMM_INSTANCE_ID)
        if missing:
            return ScanResult(
                source=file_path,
                valid=False,
                errors=[f"Missing XMP identifiers: {', '.join(missing)}"],
                parsed=parsed,
            )

        # 4. Compute destination path: {type}/{collection_id:06d}/{date_path}/{filename}.{ext}
        date_path = self._formatter.format_path(parsed)
        base_name = self._formatter.format_filename(parsed)
        dest_filename = f"{base_name}.{parsed['extension']}"
        coll_segment = f"{collection_id:06d}" if collection_id is not None else "000000"
        dest = Path(collection_type) / coll_segment / date_path / dest_filename

        return ScanResult(
            source=file_path,
            valid=True,
            parsed=parsed,
            dest=dest,
            metadata=existing,
        )
