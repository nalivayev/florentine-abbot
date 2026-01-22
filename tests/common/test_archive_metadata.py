import uuid
from pathlib import Path
from typing import Any

from common.archive_metadata import ArchiveMetadata
from common.naming import ParsedFilename
from common.logger import Logger
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
