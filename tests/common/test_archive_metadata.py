import uuid
from pathlib import Path
from typing import Any

from common.archive_metadata import ArchiveMetadata
from common.naming import ParsedFilename
from common.logger import Logger
from common.exifer import Exifer

from tests.common.fake_exifer import FakeExifer


def _assert_uuid(value: str) -> None:
    # Validate UUID format
    uuid.UUID(value)


def test_write_master_exact_date_sets_original_and_created(tmp_path: Path) -> None:
    # Arrange
    file_path = tmp_path / "2024.06.15.14.30.22.E.FAM.VAC.0001.A.ARW"
    file_path.write_bytes(b"x")  # ensure .stat() works

    # exifer returns CreateDate to be copied into DateTimeDigitized if missing
    create_date = "2025:01:15 12:00:00"
    exifer = FakeExifer(
        read_map={
            file_path: {
                "ExifIFD:CreateDate": create_date,
            }
        }
    )
    am = ArchiveMetadata(exifer=exifer)
    logger = Logger("test_archive_metadata", console=False)

    parsed = ParsedFilename(
        year=2024,
        month=6,
        day=15,
        hour=14,
        minute=30,
        second=22,
        modifier="E",
        group="FAM",
        subgroup="VAC",
        sequence="0001",
        side="A",
        suffix="ARW",
        extension="arw",
    )
    config = {
        "languages": {
            "en-US": {
                "default": True,
                "creator": "John Doe",
                "rights": "\u00A9 2026",
                "source": "Family Album",
                "description": "Trip to Baikal \u0014 best shot",
            },
            "ru-RU": {
                "default": False,
                "creator": "Джон До",
                "rights": "\u00A9 2026 (RU)",
                "source": "Семейный альбом",
                "description": "Поездка на Байкал — лучший кадр",
            },
        },
    }

    # Act
    am.write_master_tags(
        file_path=file_path,
        parsed=parsed,
        config=config,
        logger=logger,
    )

    # Assert
    assert exifer.writes, "Expected metadata write to occur"
    written_path, tags = exifer.writes[-1]
    assert written_path == file_path

    # Identifiers
    assert "XMP-dc:Identifier" in tags
    assert "XMP-xmp:Identifier" in tags
    _assert_uuid(tags["XMP-dc:Identifier"])  # uuid format

    # Description & Title (default language value)
    assert tags["XMP-dc:Description"] == config["languages"]["en-US"]["description"]
    # Language-specific variants also written for each language
    assert tags["XMP-dc:Description-en-US"] == config["languages"]["en-US"]["description"]
    assert tags["XMP-dc:Description-ru-RU"] == config["languages"]["ru-RU"]["description"]
    assert tags["XMP-dc:Title"] == file_path.stem

    # Dates
    assert tags["Exif:DateTimeOriginal"] == "2024:06:15 14:30:22"
    # XMP-photoshop:DateCreated uses ISO with T separator
    assert tags["XMP-photoshop:DateCreated"] == "2024-06-15T14:30:22"
    # DateTimeDigitized derived from CreateDate fallback
    assert tags.get("XMP-exif:DateTimeDigitized") == create_date

    # Configurable fields (taken from default language block)
    assert tags["XMP-dc:Creator"] == ["John Doe"]
    assert tags["XMP-dc:Rights"] == "\u00A9 2026"
    assert tags["XMP-dc:Rights-en-US"] == "\u00A9 2026"
    assert tags["XMP-dc:Rights-ru-RU"] == "\u00A9 2026 (RU)"
    assert tags["XMP-dc:Source"] == "Family Album"
    assert tags["XMP-dc:Source-en-US"] == "Family Album"
    assert tags["XMP-dc:Source-ru-RU"] == "Семейный альбом"

    # Description & Title (default language value)
    assert tags["XMP-dc:Description"] == config["languages"]["en-US"]["description"]
    # Language-specific variant also written
    assert tags["XMP-dc:Description-en-US"] == config["languages"]["en-US"]["description"]
    assert tags["XMP-dc:Title"] == file_path.stem

    # Dates
    assert tags["Exif:DateTimeOriginal"] == "2024:06:15 14:30:22"
    # XMP-photoshop:DateCreated uses ISO with T separator
    assert tags["XMP-photoshop:DateCreated"] == "2024-06-15T14:30:22"
    # DateTimeDigitized derived from CreateDate fallback
    assert tags.get("XMP-exif:DateTimeDigitized") == create_date

    # Configurable fields (taken from default language block)
    assert tags["XMP-dc:Creator"] == ["John Doe"]
    assert tags["XMP-dc:Rights"] == "\u00A9 2026"
    assert tags["XMP-dc:Rights-en-US"] == "\u00A9 2026"
    assert tags["XMP-dc:Source"] == "Family Album"
    assert tags["XMP-dc:Source-en-US"] == "Family Album"


def test_write_master_partial_date_sets_xmp_created_only(tmp_path: Path) -> None:
    # Arrange
    file_path = tmp_path / "1950.00.00.00.00.00.C.FAM.POR.0001.A.tiff"
    file_path.write_bytes(b"x")

    exifer = FakeExifer(read_map={file_path: {}})
    am = ArchiveMetadata(exifer=exifer)
    logger = Logger("test_archive_metadata", console=False)

    parsed = ParsedFilename(
        year=1950,
        month=0,
        day=0,
        hour=0,
        minute=0,
        second=0,
        modifier="C",
        group="FAM",
        subgroup="POR",
        sequence="0001",
        side="A",
        suffix="tiff",
        extension="tiff",
    )

    # Act
    am.write_master_tags(
        file_path=file_path,
        parsed=parsed,
        config={
            "languages": {
                "en-US": {"default": True, "description": "Circa 1950 portrait"}
            }
        },
        logger=logger,
    )

    # Assert
    _, tags = exifer.writes[-1]
    # EXIF DateTimeOriginal cleared
    assert tags["Exif:DateTimeOriginal"] == ""
    # XMP DateCreated contains partial date (YYYY only)
    assert tags["XMP-photoshop:DateCreated"] == "1950"


def test_write_derivative_inherits_context_and_links_to_master(tmp_path: Path) -> None:
    # Arrange
    master = tmp_path / "1950.06.15.12.00.00.E.FAM.POR.0001.A.tiff"
    prv = tmp_path / "1950.06.15.12.00.00.E.FAM.POR.0001.A.PRV.jpg"
    master.write_bytes(b"m")
    prv.write_bytes(b"p")

    master_id = "0f57e2c7-5c31-4b1b-8b6a-4d8a0d3ba111"
    exifer = FakeExifer(
        read_map={
            master: {
                "XMP-dc:Identifier": master_id,
                "XMP-dc:Description": "Family portrait",
                "XMP-dc:Creator": ["Alice", "Bob"],
                "XMP-photoshop:Credit": "Family Archive",
                "XMP-dc:Rights": "CC BY-NC",
                "XMP-xmpRights:UsageTerms": "Personal use",
                "XMP-dc:Source": "Album 1",
                "Exif:DateTimeOriginal": "1950:06:15 12:00:00",
                "XMP-photoshop:DateCreated": "1950-06-15T12:00:00",
                # Simulate fallback only present in ExifIFD
                "ExifIFD:DateTimeDigitized": "2026:01:15 10:00:00",
            }
        }
    )

    am = ArchiveMetadata(exifer=exifer)

    # Act
    am.write_derivative_tags(master_path=master, prv_path=prv)

    # Assert
    assert exifer.writes, "Expected metadata write for PRV"
    written_path, tags = exifer.writes[-1]
    assert written_path == prv

    # PRV gets its own identifiers
    _assert_uuid(tags["XMP-dc:Identifier"])  # uuid format
    _assert_uuid(tags["XMP-xmp:Identifier"])  # uuid format

    # Relation points to master identifier
    assert tags["XMP-dc:Relation"] == master_id

    # Title based on PRV stem
    assert tags["XMP-dc:Title"] == prv.stem

    # Inherited context
    assert tags["XMP-dc:Description"] == "Family portrait"
    assert tags["XMP-dc:Creator"] == ["Alice", "Bob"]
    assert tags["XMP-photoshop:Credit"] == "Family Archive"
    assert tags["XMP-dc:Rights"] == "CC BY-NC"
    assert tags["XMP-xmpRights:UsageTerms"] == "Personal use"
    assert tags["XMP-dc:Source"] == "Album 1"

    # Dates inherited; DateTimeDigitized uses fallback from ExifIFD
    assert tags["Exif:DateTimeOriginal"] == "1950:06:15 12:00:00"
    assert tags["XMP-photoshop:DateCreated"] == "1950-06-15T12:00:00"
    assert tags["XMP-exif:DateTimeDigitized"] == "2026:01:15 10:00:00"


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


class TestMetadataFlow:
    """Test metadata consistency across organizer and preview maker."""

    def test_organizer_to_maker_metadata_consistency(self, tmp_path: Path) -> None:
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
        def is_uuid(v: str) -> bool:
            try:
                uuid.UUID(v)
                return True
            except (ValueError, TypeError):
                return False

        assert is_uuid(master_tags["XMP-dc:Identifier"]) and is_uuid(master_tags["XMP-xmp:Identifier"])
        assert is_uuid(prv_tags["XMP-dc:Identifier"]) and is_uuid(prv_tags["XMP-xmp:Identifier"])
        assert master_tags["XMP-dc:Identifier"] != prv_tags["XMP-dc:Identifier"]
        assert master_tags["XMP-xmp:Identifier"] != prv_tags["XMP-xmp:Identifier"]

        # PRV links back to master
        assert prv_tags["XMP-dc:Relation"] == master_tags["XMP-dc:Identifier"] or \
               prv_tags["XMP-dc:Relation"] == master_tags["XMP-xmp:Identifier"]

        # Title differs (based on filename stem) — expected
        assert master_tags["XMP-dc:Title"] != prv_tags["XMP-dc:Title"]
