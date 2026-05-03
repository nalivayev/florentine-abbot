"""Tests for ScansImporter."""

from pathlib import Path

from PIL import Image

from common.constants import ARCHIVE_DB_FILENAME, ARCHIVE_SYSTEM_DIR
from common.constants import TAG_EXIF_DATETIME_ORIGINAL, TAG_XMP_DC_DESCRIPTION, TAG_XMP_DC_IDENTIFIER, TAG_XMP_DC_RIGHTS, TAG_XMP_DC_SOURCE, TAG_XMP_PHOTOSHOP_CREDIT, TAG_XMP_PHOTOSHOP_DATE_CREATED, TAG_XMP_XMP_IDENTIFIER, TAG_XMP_XMPRIGHTS_MARKED, TAG_XMP_XMPRIGHTS_USAGE_TERMS
from common.database import ArchiveDatabase, FILE_STATUS_NEW
from common.exifer import Exifer
from common.provider import list_providers
from common.tagger import Tagger
from common.tags import HistoryTag
from common.constants import TAG_XMP_XMPMM_HISTORY
from content_importer.scan_importer import ScanImporter
from tests.common.test_utils import create_test_image


VALID_NAME_1 = "2024.03.15.10.30.00.E.FAM.POR.0001.A.MSR.tif"
VALID_NAME_2 = "2024.03.15.10.30.01.E.FAM.POR.0002.A.MSR.tif"
VALID_NAME_CIRCA = "1950.00.00.00.00.00.C.FAM.POR.0003.A.MSR.tif"
INVALID_NAME = "random_scan.tif"


class TestScansImporter:

    def setup_method(self) -> None:
        self.database: ArchiveDatabase | None = None
        self.importer = ScanImporter()

    def teardown_method(self) -> None:
        if self.database is not None:
            self.database.close_conn()

    def test_valid_files_are_imported(self, tmp_path: Path, require_exiftool: None) -> None:
        """Valid files end up in the archive under the expected date folder."""
        source = tmp_path / "inbox"
        archive = tmp_path / "archive"
        source.mkdir()
        archive.mkdir()

        create_test_image(source / VALID_NAME_1, add_ids=True)
        create_test_image(source / VALID_NAME_2, add_ids=True)

        report = self.importer.run(source, archive, copy_mode=True)

        assert report.total == 2
        assert report.valid == 2
        assert report.succeeded == 2
        assert report.failed == 0

        # Both files land somewhere inside the archive
        placed = list(archive.rglob("*.tif"))
        assert len(placed) == 2

    def test_invalid_files_are_skipped(self, tmp_path: Path, require_exiftool: None) -> None:
        """Files that fail validation are counted as failed, not placed."""
        source = tmp_path / "inbox"
        archive = tmp_path / "archive"
        source.mkdir()
        archive.mkdir()

        create_test_image(source / VALID_NAME_1, add_ids=True)

        # No XMP IDs — should fail validation
        bad = source / VALID_NAME_2
        Image.new("RGB", (10, 10)).save(bad, format="TIFF")

        report = self.importer.run(source, archive, copy_mode=True)

        assert report.total == 2
        assert report.valid == 1
        assert report.succeeded == 1
        assert report.failed == 1

    def test_copy_mode_keeps_source(self, tmp_path: Path, require_exiftool: None) -> None:
        source = tmp_path / "inbox"
        archive = tmp_path / "archive"
        source.mkdir()
        archive.mkdir()

        src_file = source / VALID_NAME_1
        create_test_image(src_file, add_ids=True)

        self.importer.run(source, archive, copy_mode=True)

        assert src_file.exists()

    def test_move_mode_deletes_source(self, tmp_path: Path, require_exiftool: None) -> None:
        source = tmp_path / "inbox"
        archive = tmp_path / "archive"
        source.mkdir()
        archive.mkdir()

        src_file = source / VALID_NAME_1
        create_test_image(src_file, add_ids=True)

        self.importer.run(source, archive, copy_mode=False)

        assert not src_file.exists()

    def test_empty_folder_returns_zero_total(self, tmp_path: Path) -> None:
        source = tmp_path / "empty"
        archive = tmp_path / "archive"
        source.mkdir()
        archive.mkdir()

        report = self.importer.run(source, archive)

        assert report.total == 0
        assert report.succeeded == 0
        assert report.failed == 0

    def test_wrongly_named_files_counted_as_failed(self, tmp_path: Path) -> None:
        """Files with names that don't match scheme don't need exiftool."""
        source = tmp_path / "inbox"
        archive = tmp_path / "archive"
        source.mkdir()
        archive.mkdir()

        (source / INVALID_NAME).write_bytes(b"\x00" * 100)

        report = self.importer.run(source, archive)

        assert report.total == 1
        assert report.valid == 0
        assert report.failed == 1

    def test_import_adds_history_entry(self, tmp_path: Path, require_exiftool: None) -> None:
        """Each imported file gets a new XMP History entry from content-importer."""
        source = tmp_path / "inbox"
        archive = tmp_path / "archive"
        source.mkdir()
        archive.mkdir()

        create_test_image(source / VALID_NAME_1, add_ids=True)

        self.importer.run(source, archive, copy_mode=True)

        placed = next(archive.rglob("*.tif"))
        exifer = Exifer()
        tagger = Tagger(placed, exifer=exifer)
        tagger.begin()
        tagger.read(HistoryTag())
        result = tagger.end() or {}

        history = result.get(TAG_XMP_XMPMM_HISTORY, [])
        agents = [e.get("softwareAgent", "") for e in history]
        assert any("content-importer" in a for a in agents), (
            f"Expected a 'content-importer' history entry, got: {agents}"
        )

    def test_import_writes_archive_identifiers_and_exact_dates(self, tmp_path: Path, require_exiftool: None) -> None:
        """Imported exact-date scans become archive masters with identifier/date metadata."""
        source = tmp_path / "inbox"
        archive = tmp_path / "archive"
        source.mkdir()
        archive.mkdir()

        create_test_image(source / VALID_NAME_1, add_ids=True)

        self.importer.run(source, archive, copy_mode=True)

        placed = next(archive.rglob("*.tif"))
        meta = Exifer().read(placed, [])

        archive_identifier = meta.get(TAG_XMP_DC_IDENTIFIER) or meta.get(TAG_XMP_XMP_IDENTIFIER)
        assert archive_identifier, "Imported master must have an archive identifier"

        dt_original = meta.get(TAG_EXIF_DATETIME_ORIGINAL) or meta.get("ExifIFD:DateTimeOriginal") or meta.get("EXIF:DateTimeOriginal")
        assert dt_original == "2024:03:15 10:30:00"

        date_created = meta.get(TAG_XMP_PHOTOSHOP_DATE_CREATED) or meta.get("XMP:DateCreated")
        assert date_created is not None
        assert "2024-03-15T10:30:00" in str(date_created) or "2024:03:15 10:30:00" in str(date_created)

    def test_import_writes_partial_dates_without_exif_datetimeoriginal(self, tmp_path: Path, require_exiftool: None) -> None:
        """Imported circa scans keep partial dates in XMP and clear EXIF original date."""
        source = tmp_path / "inbox"
        archive = tmp_path / "archive"
        source.mkdir()
        archive.mkdir()

        create_test_image(source / VALID_NAME_CIRCA, add_ids=True)

        self.importer.run(source, archive, copy_mode=True)

        placed = next(archive.rglob("*.tif"))
        meta = Exifer().read(placed, [])

        dt_original = meta.get(TAG_EXIF_DATETIME_ORIGINAL) or meta.get("ExifIFD:DateTimeOriginal") or meta.get("EXIF:DateTimeOriginal")
        assert not dt_original

        date_created = meta.get(TAG_XMP_PHOTOSHOP_DATE_CREATED) or meta.get("XMP:DateCreated")
        assert date_created is not None
        assert str(date_created).startswith("1950")

    def test_import_registers_copied_file_in_db(self, tmp_path: Path, require_exiftool: None) -> None:
        """Imported files are registered in the archive DB when it is active."""
        source = tmp_path / "inbox"
        archive = tmp_path / "archive"
        source.mkdir()
        archive.mkdir()

        create_test_image(source / VALID_NAME_1, add_ids=True)

        self.database = ArchiveDatabase(archive)
        self.database.get_conn()

        report = self.importer.run(source, archive, copy_mode=True)

        assert report.succeeded == 1

        conn = self.database.get_conn()
        row = conn.execute(
            "SELECT path, status FROM files ORDER BY id LIMIT 1"
        ).fetchone()
        task_rows = conn.execute(
            "SELECT daemon, status FROM daemon_tasks ORDER BY daemon"
        ).fetchall()

        assert row is not None
        assert row["path"].endswith(".tif")
        assert row["status"] == FILE_STATUS_NEW
        assert [task_row["daemon"] for task_row in task_rows] == [
            provider.daemon_name for provider in list_providers()
        ]
        assert all(task_row["status"] == "pending" for task_row in task_rows)

    def test_import_projects_metadata_into_db(self, tmp_path: Path, require_exiftool: None) -> None:
        """Importer stores a semantic metadata projection in the archive DB."""
        source = tmp_path / "inbox"
        archive = tmp_path / "archive"
        source.mkdir()
        archive.mkdir()

        create_test_image(source / VALID_NAME_1, add_ids=True)

        metadata_config = {
            "languages": {
                "ru-RU": {
                    "default": True,
                    "description": "Русское описание",
                    "creator": ["Иван Иванов", "Мария Иванова"],
                    "source": "Альбом 2",
                    "credit": "Семейный архив",
                },
                "en-US": {
                    "description": "English description",
                    "creator": ["John Smith"],
                    "source": "Album 2",
                    "credit": "Family archive",
                },
            },
        }

        self.database = ArchiveDatabase(archive)
        self.database.get_conn()

        report = self.importer.run(
            source,
            archive,
            copy_mode=True,
            metadata_config=metadata_config,
        )

        assert report.succeeded == 1

        conn = self.database.get_conn()
        metadata_row = conn.execute(
            "SELECT photo_year, photo_month, photo_day, photo_time, date_accuracy, description, source, credit FROM file_metadata"
        ).fetchone()
        creator_rows = conn.execute(
            "SELECT position, name FROM file_creators ORDER BY position"
        ).fetchall()
        history_row = conn.execute(
            "SELECT action, software, changed, instance_id FROM file_history ORDER BY recorded_at, id LIMIT 1"
        ).fetchone()

        assert metadata_row is not None
        assert metadata_row["photo_year"] == 2024
        assert metadata_row["photo_month"] == 3
        assert metadata_row["photo_day"] == 15
        assert metadata_row["photo_time"] == "10:30:00"
        assert metadata_row["date_accuracy"] == "exact"
        assert metadata_row["description"] == "Русское описание"
        assert metadata_row["source"] == "Альбом 2"
        assert metadata_row["credit"] == "Семейный архив"

        assert [row["position"] for row in creator_rows] == [1, 2]
        assert [row["name"] for row in creator_rows] == ["Иван Иванов", "Мария Иванова"]

        assert history_row is not None
        assert history_row["action"] == "managed"
        assert "content-importer" in history_row["software"]
        assert history_row["changed"] == "metadata"
        assert history_row["instance_id"]

    def test_import_projects_partial_dates_into_db(self, tmp_path: Path, require_exiftool: None) -> None:
        """Importer stores partial photo dates with the correct accuracy label."""
        source = tmp_path / "inbox"
        archive = tmp_path / "archive"
        source.mkdir()
        archive.mkdir()

        create_test_image(source / VALID_NAME_CIRCA, add_ids=True)

        self.database = ArchiveDatabase(archive)
        self.database.get_conn()

        report = self.importer.run(source, archive, copy_mode=True)

        assert report.succeeded == 1

        conn = self.database.get_conn()
        metadata_row = conn.execute(
            "SELECT photo_year, photo_month, photo_day, photo_time, date_accuracy FROM file_metadata"
        ).fetchone()

        assert metadata_row is not None
        assert metadata_row["photo_year"] == 1950
        assert metadata_row["photo_month"] is None
        assert metadata_row["photo_day"] is None
        assert metadata_row["photo_time"] is None
        assert metadata_row["date_accuracy"] == "circa"

    def test_import_writes_configured_metadata_fields(self, tmp_path: Path, require_exiftool: None) -> None:
        """Importer writes semantic metadata fields from the reusable metadata config."""
        source = tmp_path / "inbox"
        archive = tmp_path / "archive"
        source.mkdir()
        archive.mkdir()

        create_test_image(source / VALID_NAME_1, add_ids=True)

        metadata_config = {
            "languages": {
                "ru-RU": {
                    "default": True,
                    "description": "Русское описание",
                    "creator": ["Иван Иванов", "Петр Петров"],
                    "rights": "Все права защищены",
                    "source": "Коробка 7",
                    "credit": "Семейный архив",
                    "terms": "Только для личного использования",
                    "marked": "True",
                },
                "en-US": {
                    "description": "English description",
                    "creator": ["Ivan Ivanov"],
                    "rights": "All rights reserved",
                    "source": "Box 7",
                    "credit": "Family Archive",
                    "terms": "Personal use only",
                    "marked": "",
                },
            },
        }

        self.importer.run(source, archive, copy_mode=True, metadata_config=metadata_config)

        placed = next(archive.rglob("*.tif"))
        meta = Exifer().read(placed, [])

        description = meta.get(TAG_XMP_DC_DESCRIPTION) or meta.get("XMP:Description")
        rights = meta.get(TAG_XMP_DC_RIGHTS) or meta.get("XMP:Rights")
        source_value = meta.get(TAG_XMP_DC_SOURCE) or meta.get("XMP:Source")
        credit = meta.get(TAG_XMP_PHOTOSHOP_CREDIT) or meta.get("XMP:Credit")
        terms = meta.get(TAG_XMP_XMPRIGHTS_USAGE_TERMS) or meta.get("XMP:UsageTerms")
        marked = meta.get(TAG_XMP_XMPRIGHTS_MARKED) or meta.get("XMP:Marked")

        assert description is not None
        assert "Русское описание" in str(description)
        assert meta.get(f"{TAG_XMP_DC_DESCRIPTION}-en-US") == "English description"
        assert rights == "Все права защищены"
        assert meta.get(f"{TAG_XMP_DC_RIGHTS}-en-US") == "All rights reserved"
        assert source_value == "Коробка 7"
        assert credit == "Семейный архив"
        assert terms == "Только для личного использования"
        assert meta.get(f"{TAG_XMP_XMPRIGHTS_USAGE_TERMS}-en-US") == "Personal use only"
        assert str(marked).lower() in ("true", "1")
        assert meta.get(f"{TAG_XMP_DC_SOURCE}-en-US") is None
        assert meta.get(f"{TAG_XMP_PHOTOSHOP_CREDIT}-en-US") is None

    def test_import_does_not_create_db_when_archive_db_is_absent(self, tmp_path: Path, require_exiftool: None) -> None:
        """Importer keeps the old behavior: no active DB means no DB registration."""
        source = tmp_path / "inbox"
        archive = tmp_path / "archive"
        source.mkdir()
        archive.mkdir()

        create_test_image(source / VALID_NAME_1, add_ids=True)

        report = self.importer.run(source, archive, copy_mode=True)

        assert report.succeeded == 1
        assert not (archive / ARCHIVE_SYSTEM_DIR / ARCHIVE_DB_FILENAME).exists()
