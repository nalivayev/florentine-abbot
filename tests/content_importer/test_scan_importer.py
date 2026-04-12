"""Tests for ScansImporter."""

from pathlib import Path

from PIL import Image

from common.exifer import Exifer
from common.tagger import Tagger
from common.tags import HistoryTag
from common.constants import TAG_XMP_XMPMM_HISTORY
from content_importer.scan_importer import ScanImporter
from tests.common.test_utils import create_test_image


VALID_NAME_1 = "2024.03.15.10.30.00.E.FAM.POR.0001.A.MSR.tif"
VALID_NAME_2 = "2024.03.15.10.30.01.E.FAM.POR.0002.A.MSR.tif"
INVALID_NAME = "random_scan.tif"


class TestScansImporter:

    def test_valid_files_are_imported(self, tmp_path: Path, require_exiftool: None) -> None:
        """Valid files end up in the archive under the expected date folder."""
        source = tmp_path / "inbox"
        archive = tmp_path / "archive"
        source.mkdir()
        archive.mkdir()

        create_test_image(source / VALID_NAME_1, add_ids=True)
        create_test_image(source / VALID_NAME_2, add_ids=True)

        importer = ScanImporter()
        report = importer.run(source, archive, copy_mode=True)

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

        report = ScanImporter().run(source, archive, copy_mode=True)

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

        ScanImporter().run(source, archive, copy_mode=True)

        assert src_file.exists()

    def test_move_mode_deletes_source(self, tmp_path: Path, require_exiftool: None) -> None:
        source = tmp_path / "inbox"
        archive = tmp_path / "archive"
        source.mkdir()
        archive.mkdir()

        src_file = source / VALID_NAME_1
        create_test_image(src_file, add_ids=True)

        ScanImporter().run(source, archive, copy_mode=False)

        assert not src_file.exists()

    def test_empty_folder_returns_zero_total(self, tmp_path: Path) -> None:
        source = tmp_path / "empty"
        archive = tmp_path / "archive"
        source.mkdir()
        archive.mkdir()

        report = ScanImporter().run(source, archive)

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

        report = ScanImporter().run(source, archive)

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

        ScanImporter().run(source, archive, copy_mode=True)

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
