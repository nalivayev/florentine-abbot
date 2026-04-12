"""Tests for ScanValidator."""

from pathlib import Path

from PIL import Image

from common.constants import TAG_XMP_XMPMM_DOCUMENT_ID, TAG_XMP_XMPMM_INSTANCE_ID
from content_importer.scan_validator import ScanResult, ScanValidator
from tests.common.test_utils import create_test_image


# Valid archive-scheme filename with all required fields
VALID_NAME = "2024.03.15.10.30.00.E.FAM.POR.0001.A.MSR.tif"


class TestScanValidator:

    def test_valid_file_is_accepted(self, tmp_path: Path, require_exiftool: None) -> None:
        """A properly-named file with XMP IDs passes validation."""
        src = tmp_path / VALID_NAME
        create_test_image(src, add_ids=True)

        validator = ScanValidator()
        result = validator.validate(src)

        assert result.valid is True
        assert result.errors == []
        assert result.dest is not None
        assert result.parsed is not None
        assert isinstance(result, ScanResult)
        assert result.metadata  # DocumentID and InstanceID are present

    def test_valid_file_dest_path_contains_date(
        self, tmp_path: Path, require_exiftool: None
    ) -> None:
        """Destination path is rooted under the date folder from the filename."""
        src = tmp_path / VALID_NAME
        create_test_image(src, add_ids=True)

        result = ScanValidator().validate(src)

        assert result.valid is True
        assert "2024" in str(result.dest)

    def test_wrong_filename_fails(self, tmp_path: Path) -> None:
        """A file whose name doesn't match the scheme fails without touching XMP."""
        src = tmp_path / "random_name.tif"
        src.write_bytes(b"\x00" * 10)

        result = ScanValidator().validate(src)

        assert result.valid is False
        assert result.errors

    def test_invalid_modifier_fails(self, tmp_path: Path, require_exiftool: None) -> None:
        """A filename with an invalid modifier character fails field validation."""
        # 'Z' is not a valid modifier
        bad_name = "2024.03.15.10.30.00.Z.FAM.POR.0001.A.MSR.tif"
        src = tmp_path / bad_name
        create_test_image(src, add_ids=True)

        result = ScanValidator().validate(src)

        assert result.valid is False
        assert any("modifier" in e.lower() for e in result.errors)

    def test_missing_document_id_fails(self, tmp_path: Path, require_exiftool: None) -> None:
        """A file with correct name but no XMP DocumentID/InstanceID fails."""
        src = tmp_path / VALID_NAME
        img = Image.new("RGB", (10, 10), color="blue")
        img.save(src, format="TIFF")

        result = ScanValidator().validate(src)

        assert result.valid is False
        assert any(TAG_XMP_XMPMM_DOCUMENT_ID in e or TAG_XMP_XMPMM_INSTANCE_ID in e for e in result.errors)
