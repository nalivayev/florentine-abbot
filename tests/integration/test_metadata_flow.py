from pathlib import Path
import uuid

from common.archive_metadata import ArchiveMetadata
from common.naming import ParsedFilename
from common.logger import Logger


class StoreExifer:
    """Exifer double that keeps an in-memory store of tags per file.

    - read() returns requested tags from the store (or all known for the file).
    - write() updates the store for the file.
    This simulates the organizer/maker cycle without invoking exiftool.
    """

    def __init__(self) -> None:
        self.store: dict[Path, dict[str, str]] = {}

    def read(self, file_path: Path, tag_names: list[str]) -> dict[str, str]:
        tags = self.store.get(file_path, {})
        if not tag_names:
            return dict(tags)
        # Return only requested keys if known
        return {k: v for k, v in tags.items() if k in tag_names or k in tags}

    def write(self, file_path: Path, tags: dict[str, str]) -> None:
        existing = self.store.setdefault(file_path, {})
        existing.update({k: v for k, v in tags.items() if v is not None})


def _is_uuid(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except Exception:
        return False


def test_organizer_to_maker_metadata_consistency(tmp_path: Path) -> None:
    # Arrange: files and initial CreateDate (for Digitized)
    master = tmp_path / "1950.06.15.12.00.00.E.FAM.POR.0001.A.tiff"
    prv = tmp_path / "1950.06.15.12.00.00.E.FAM.POR.0001.A.PRV.jpg"
    master.write_bytes(b"m")
    prv.write_bytes(b"p")

    exifer = StoreExifer()
    # Seed CreateDate so write_master derives DateTimeDigitized
    exifer.store[master] = {"ExifIFD:CreateDate": "2026:01:15 10:00:00"}

    am = ArchiveMetadata(exifer=exifer)
    logger = Logger("test_metadata_flow", console=False)

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

    config = {
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

    # Act: organizer writes master tags
    am.write_master_tags(
        file_path=master,
        parsed=parsed,
        config=config,
        logger=logger,
    )

    # Then maker writes derivative based on master
    am.write_derivative_tags(master_path=master, prv_path=prv, logger=logger)

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

    # Title differs (based on filename stem) — expected
    assert master_tags["XMP-dc:Title"] != prv_tags["XMP-dc:Title"]
