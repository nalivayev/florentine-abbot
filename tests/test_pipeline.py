"""Automated end-to-end pipeline test: scan-batcher -> file-organizer -> preview-maker.

Mirrors test_manual_pipeline.py but runs automatically in pytest.
Uses create_test_image() which follows the real scanning workflow
(VueScan tags -> FakeMetadataWorkflow for XMP).
"""

import pytest

from file_organizer.organizer import FileOrganizer
from preview_maker.maker import PreviewMaker
from common.exifer import Exifer
from common.logger import Logger
from common.historian import XMPHistorian
from common.constants import (
    TAG_IFD0_MAKE,
    TAG_IFD0_MODEL,
    TAG_XMP_TIFF_MAKE,
    TAG_XMP_TIFF_MODEL,
    TAG_XMP_DC_IDENTIFIER,
    TAG_XMP_XMP_IDENTIFIER,
    TAG_XMP_DC_RELATION,
    TAG_XMP_DC_FORMAT,
    TAG_XMP_XMPMM_DOCUMENT_ID,
    TAG_XMP_XMPMM_INSTANCE_ID,
    TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID,
    TAG_XMP_XMPMM_DERIVED_FROM_INSTANCE_ID,
    TAG_XMP_EXIF_DATETIME_DIGITIZED,
    XMP_ACTION_CREATED,
    XMP_ACTION_EDITED,
    XMP_ACTION_CONVERTED,
)
from tests.common.test_utils import create_test_image


def _exiftool_available() -> bool:
    """Return True if exiftool is installed and runnable."""
    try:
        Exifer()._run(["-ver"])
        return True
    except (FileNotFoundError, RuntimeError):
        return False


# Skip entire module if exiftool is not available
pytestmark = pytest.mark.skipif(
    not _exiftool_available(),
    reason="ExifTool not found",
)


class TestPipeline:
    """End-to-end pipeline test: create_test_image -> file-organizer -> preview-maker.

    Verifies the complete archival workflow produces correct file structure
    and metadata at each stage.  Component-specific tests live under
    tests/file_organizer, tests/preview_maker, etc.
    """

    SCANNER_MAKE = "Epson"
    SCANNER_MODEL = "Perfection V600"
    FILENAME_STEM = "1925.04.00.00.00.00.C.001.001.0001.A"

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.root = tmp_path
        self.logger = Logger("test-pipeline")
        self.exifer = Exifer()
        self.historian = XMPHistorian(exifer=self.exifer)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _create_scan(self):
        """Create a test TIFF that mirrors real scan-batcher output."""
        scan_file = self.root / f"{self.FILENAME_STEM}.RAW.tif"
        create_test_image(
            path=scan_file,
            size=(600, 400),
            color=(240, 235, 230),
            format="TIFF",
            scanner_make=self.SCANNER_MAKE,
            scanner_model=self.SCANNER_MODEL,
        )
        return scan_file

    def _find_file(self, root, pattern):
        """Find a single file matching *pattern* under *root*."""
        found = list(root.rglob(pattern))
        assert found, f"No file matching '{pattern}' found under {root}"
        return found[0]

    # ------------------------------------------------------------------
    # main test
    # ------------------------------------------------------------------

    def test_full_pipeline(self):
        """create_test_image -> FileOrganizer -> PreviewMaker with full metadata checks."""

        # === Step 0: create fake scan ===
        scan_file = self._create_scan()
        assert scan_file.exists()

        # Verify scan-batcher metadata was written
        ids = self.exifer.read(scan_file, [
            TAG_XMP_XMPMM_DOCUMENT_ID,
            TAG_XMP_XMPMM_INSTANCE_ID,
            TAG_IFD0_MAKE,
            TAG_IFD0_MODEL,
            TAG_XMP_TIFF_MAKE,
            TAG_XMP_TIFF_MODEL,
            TAG_XMP_EXIF_DATETIME_DIGITIZED,
        ])
        document_id = ids[TAG_XMP_XMPMM_DOCUMENT_ID]
        assert document_id, "DocumentID must be set by scan-batcher"
        assert ids[TAG_XMP_XMPMM_INSTANCE_ID], "InstanceID must be set by scan-batcher"
        assert ids[TAG_IFD0_MAKE] == self.SCANNER_MAKE
        assert ids[TAG_IFD0_MODEL] == self.SCANNER_MODEL
        assert ids[TAG_XMP_TIFF_MAKE] == self.SCANNER_MAKE
        assert ids[TAG_XMP_TIFF_MODEL] == self.SCANNER_MODEL

        # DateTimeDigitized must have timezone
        digitized = ids.get(TAG_XMP_EXIF_DATETIME_DIGITIZED, "")
        assert "+" in digitized or "-" in digitized, (
            f"DateTimeDigitized must include timezone, got: {digitized}"
        )

        # XMP History: created + edited
        history = self.historian.read_history(scan_file)
        actions = [e.get("action") for e in history]
        assert XMP_ACTION_CREATED in actions
        assert XMP_ACTION_EDITED in actions
        # History When must have timezone
        for entry in history:
            when = entry.get("when", "")
            assert "+" in when or "-" in when, (
                f"History When must include timezone, got: {when}"
            )

        # === Step 1: FileOrganizer ===
        organizer = FileOrganizer(self.logger)
        processed = organizer(
            input_path=self.root,
            recursive=False,
            copy_mode=False,
        )
        assert processed == 1, "FileOrganizer should process 1 file"

        # Find organized master
        processed_root = self.root / "processed"
        master = self._find_file(processed_root, "*.RAW.tif")
        assert "SOURCES" in str(master), "Master must be in SOURCES folder"

        # DocumentID preserved, InstanceID refreshed
        master_ids = self.exifer.read(master, [
            TAG_XMP_XMPMM_DOCUMENT_ID,
            TAG_XMP_XMPMM_INSTANCE_ID,
            TAG_XMP_DC_IDENTIFIER,
            TAG_XMP_XMP_IDENTIFIER,
        ])
        assert master_ids[TAG_XMP_XMPMM_DOCUMENT_ID] == document_id, (
            "DocumentID must be preserved through organizer"
        )
        master_identifier = (
            master_ids.get(TAG_XMP_DC_IDENTIFIER)
            or master_ids.get(TAG_XMP_XMP_IDENTIFIER)
        )
        assert master_identifier, "Master must have dc:Identifier after organizer"

        # History now has 3+ entries (created + edited from batcher, edited from organizer)
        master_history = self.historian.read_history(master)
        assert len(master_history) >= 3, (
            f"Expected >= 3 history entries, got {len(master_history)}"
        )

        # === Step 2: PreviewMaker ===
        maker = PreviewMaker(self.logger)
        prv_count = maker(path=processed_root, overwrite=False, max_size=800, quality=75)
        assert prv_count == 1, "PreviewMaker should generate 1 PRV"

        prv = self._find_file(processed_root, "*.PRV.jpg")
        assert prv.exists()

        prv_tags = self.exifer.read(prv, [
            TAG_XMP_XMPMM_DOCUMENT_ID,
            TAG_XMP_XMPMM_INSTANCE_ID,
            TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID,
            TAG_XMP_XMPMM_DERIVED_FROM_INSTANCE_ID,
            TAG_XMP_DC_IDENTIFIER,
            TAG_XMP_DC_RELATION,
            TAG_XMP_DC_FORMAT,
            TAG_XMP_TIFF_MAKE,
            TAG_XMP_TIFF_MODEL,
            TAG_XMP_EXIF_DATETIME_DIGITIZED,
        ])

        # Same DocumentID (same logical document), different InstanceID
        assert prv_tags[TAG_XMP_XMPMM_DOCUMENT_ID] == document_id
        assert prv_tags[TAG_XMP_XMPMM_INSTANCE_ID] != master_ids[TAG_XMP_XMPMM_INSTANCE_ID]

        # DerivedFrom points to master
        assert prv_tags[TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID] == document_id

        # Relation points to master's dc:Identifier
        assert prv_tags[TAG_XMP_DC_RELATION] == master_identifier

        # Format is JPEG
        assert prv_tags[TAG_XMP_DC_FORMAT] == "image/jpeg"

        # Make/Model propagated
        assert prv_tags[TAG_XMP_TIFF_MAKE] == self.SCANNER_MAKE
        assert prv_tags[TAG_XMP_TIFF_MODEL] == self.SCANNER_MODEL

        # DateTimeDigitized with timezone
        prv_digitized = prv_tags.get(TAG_XMP_EXIF_DATETIME_DIGITIZED, "")
        assert "+" in prv_digitized or "-" in prv_digitized

        # PRV History: converted + edited
        prv_history = self.historian.read_history(prv)
        prv_actions = [e.get("action") for e in prv_history]
        assert XMP_ACTION_CONVERTED in prv_actions
        assert XMP_ACTION_EDITED in prv_actions
