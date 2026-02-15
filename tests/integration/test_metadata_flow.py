from pathlib import Path
import uuid
from typing import Any

from common.constants import (
    DATE_TAGS,
    IDENTIFIER_TAGS,
    TAG_XMP_DC_IDENTIFIER,
    TAG_XMP_XMP_IDENTIFIER,
    TAG_XMP_DC_RELATION,
    TAG_EXIF_DATETIME_ORIGINAL,
    TAG_XMP_PHOTOSHOP_DATE_CREATED,
    TAG_XMP_EXIF_DATETIME_DIGITIZED,
    TAG_EXIFIFD_CREATE_DATE,
    TAG_EXIFIFD_DATETIME_DIGITIZED,
)
from common.naming import ParsedFilename
from common.logger import Logger

from tests.common.store_exifer import StoreExifer
from tests.common.fake_archive_metadata import FakeArchiveMetadata


def _is_uuid(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except Exception:
        return False


def _simulate_file_processor_write(
    exifer: StoreExifer,
    metadata: FakeArchiveMetadata,
    file_path: Path,
    parsed: ParsedFilename,
) -> None:
    """Simulate FileProcessor._write_metadata() logic."""
    tags: dict[str, Any] = {}

    # Generate UUIDs for identifiers
    tags[TAG_XMP_DC_IDENTIFIER] = str(uuid.uuid4())
    tags[TAG_XMP_XMP_IDENTIFIER] = str(uuid.uuid4())

    # Read existing dates for fallback
    existing = exifer.read(file_path, [TAG_EXIFIFD_CREATE_DATE, TAG_EXIFIFD_DATETIME_DIGITIZED])
    digitized = existing.get(TAG_EXIFIFD_DATETIME_DIGITIZED) or existing.get(TAG_EXIFIFD_CREATE_DATE)
    if digitized:
        tags[TAG_XMP_EXIF_DATETIME_DIGITIZED] = digitized

    # Format dates from parsed filename
    date_str = f"{parsed.year}:{parsed.month:02d}:{parsed.day:02d} {parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d}"
    tags[TAG_EXIF_DATETIME_ORIGINAL] = date_str
    tags[TAG_XMP_PHOTOSHOP_DATE_CREATED] = date_str

    # Add configurable metadata
    tags.update(metadata.get_metadata_values())

    exifer.write(file_path, tags)


def _simulate_preview_maker_write(
    exifer: StoreExifer,
    metadata: FakeArchiveMetadata,
    master_path: Path,
    prv_path: Path,
) -> None:
    """Simulate PreviewMaker._convert_to_prv() metadata logic."""
    # Read from master
    configurable_tags = metadata.get_configurable_tags()
    tags_to_read = list(IDENTIFIER_TAGS) + configurable_tags + list(DATE_TAGS)
    master_tags = exifer.read(master_path, tags_to_read)

    prv_tags: dict[str, Any] = {}

    # Generate new UUID for PRV
    prv_tags[TAG_XMP_DC_IDENTIFIER] = str(uuid.uuid4())
    prv_tags[TAG_XMP_XMP_IDENTIFIER] = str(uuid.uuid4())

    # Create relation to master
    master_id = master_tags.get(TAG_XMP_DC_IDENTIFIER) or master_tags.get(TAG_XMP_XMP_IDENTIFIER)
    if master_id:
        prv_tags[TAG_XMP_DC_RELATION] = master_id

    # Copy dates from master
    for tag in DATE_TAGS:
        if tag in master_tags:
            prv_tags[tag] = master_tags[tag]

    # Copy configurable tags from master
    for tag in configurable_tags:
        if tag in master_tags:
            prv_tags[tag] = master_tags[tag]

    exifer.write(prv_path, prv_tags)


class TestMetadataFlow:
    """Test metadata consistency across organizer and preview maker."""

    def test_organizer_to_maker_metadata_consistency(self, tmp_path: Path) -> None:
        # Arrange: files and initial CreateDate (for Digitized)
        master = tmp_path / "1950.06.15.12.00.00.E.FAM.POR.0001.A.tiff"
        prv = tmp_path / "1950.06.15.12.00.00.E.FAM.POR.0001.A.PRV.jpg"
        master.write_bytes(b"m")
        prv.write_bytes(b"p")

        exifer = StoreExifer()
        # Seed CreateDate so write derives DateTimeDigitized
        exifer.store[master] = {"ExifIFD:CreateDate": "2026:01:15 10:00:00"}

        metadata_config = {
            "languages": {
                "en-US": {
                    "default": True,
                    "creator": ["Alice", "Bob"],
                    "credit": "Family Archive",
                    "rights": "CC BY-NC",
                    "terms": "Personal use",
                    "source": "Album 1",
                    "description": "Family portrait",
                }
            }
        }
        metadata_tags = {
            "description": "XMP-dc:Description",
            "creator": "XMP-dc:Creator",
            "credit": "XMP-photoshop:Credit",
            "rights": "XMP-dc:Rights",
            "terms": "XMP-xmpRights:UsageTerms",
            "source": "XMP-dc:Source",
        }

        logger = Logger("test_metadata_flow", console=False)
        am = FakeArchiveMetadata(
            metadata_config=metadata_config,
            metadata_tags=metadata_tags,
            logger=logger,
        )

        parsed = ParsedFilename(
            year=1950,
            month=6,
            day=15,
            hour=12,
            minute=0,
            second=0,
            modifier="E",
            group="FAM",
            subgroup="POR",
            sequence="0001",
            side="A",
            suffix="tiff",
            extension="tiff",
        )

        # Act: simulate FileProcessor writing master tags
        _simulate_file_processor_write(exifer, am, master, parsed)

        # Then simulate PreviewMaker writing derivative based on master
        _simulate_preview_maker_write(exifer, am, master, prv)

        # Assert: compare contextual/date tags equality
        master_tags = exifer.store.get(master, {})
        prv_tags = exifer.store.get(prv, {})

        # Tags that should be identical between master and PRV
        same_keys = [
            "XMP-dc:Description",
            "XMP-dc:Creator",
            "XMP-photoshop:Credit",
            "XMP-dc:Rights",
            "XMP-xmpRights:UsageTerms",
            "XMP-dc:Source",
            "Exif:DateTimeOriginal",
            "XMP-photoshop:DateCreated",
            "XMP-exif:DateTimeDigitized",
        ]

        for key in same_keys:
            assert master_tags.get(key) == prv_tags.get(key), f"Mismatch in tag {key}"

        # PRV has its own identifiers different from master
        assert _is_uuid(master_tags["XMP-dc:Identifier"]) and _is_uuid(master_tags["XMP-xmp:Identifier"])
        assert _is_uuid(prv_tags["XMP-dc:Identifier"]) and _is_uuid(prv_tags["XMP-xmp:Identifier"])
        assert master_tags["XMP-dc:Identifier"] != prv_tags["XMP-dc:Identifier"]
        assert master_tags["XMP-xmp:Identifier"] != prv_tags["XMP-xmp:Identifier"]

        # PRV links back to master
        assert prv_tags["XMP-dc:Relation"] == master_tags["XMP-dc:Identifier"] or \
           prv_tags["XMP-dc:Relation"] == master_tags["XMP-xmp:Identifier"]