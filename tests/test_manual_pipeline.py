"""Manual end-to-end test of the full pipeline.

This test is marked as 'manual' and excluded from regular test runs.
Run explicitly with: pytest tests/test_manual_pipeline.py -v

Unlike test_pipeline.py (which is automated and checks assertions only),
this test prints detailed human-readable output and preserves temp files
for manual inspection with exiftool.
"""

import pytest
from pathlib import Path

from file_organizer.organizer import FileOrganizer
from preview_maker.maker import PreviewMaker
from common.logger import Logger
from common.exifer import Exifer
from common.historian import XMPHistorian
from common.constants import (
    TAG_IFD0_MAKE,
    TAG_IFD0_MODEL,
    TAG_XMP_TIFF_MAKE,
    TAG_XMP_TIFF_MODEL,
    TAG_XMP_XMPMM_DOCUMENT_ID,
    TAG_XMP_XMPMM_INSTANCE_ID,
    TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID,
    TAG_XMP_XMPMM_DERIVED_FROM_INSTANCE_ID,
    TAG_XMP_DC_IDENTIFIER,
    TAG_XMP_DC_RELATION,
    TAG_XMP_DC_FORMAT,
    TAG_XMP_EXIF_DATETIME_DIGITIZED,
    XMP_ACTION_CREATED,
    XMP_ACTION_EDITED,
    XMP_ACTION_CONVERTED,
)
from tests.common.test_utils import create_test_image


SCANNER_MAKE = "Epson"
SCANNER_MODEL = "Perfection V600"
FILENAME_STEM = "1925.04.00.00.00.00.C.001.001.0001.A"


def _find_file(root: Path, pattern: str) -> Path:
    """Find a single file matching *pattern* under *root*."""
    found = list(root.rglob(pattern))
    assert found, f"No file matching '{pattern}' found under {root}"
    return found[0]


@pytest.mark.manual
def test_full_pipeline(tmp_path):
    """Full pipeline: create file -> organize -> generate preview.

    Creates a test TIFF with scanner metadata (IFD0:Make/Model, DocumentID,
    InstanceID, XMP History), organizes it with file-organizer, and generates
    a preview with preview-maker.  Prints detailed output for manual inspection.
    """
    logger = Logger("test_manual_pipeline", console=True)
    exifer = Exifer()
    historian = XMPHistorian(exifer=exifer)

    input_file = tmp_path / f"{FILENAME_STEM}.RAW.tif"

    print(f"\nTest directory: {tmp_path}")
    print("=" * 60)

    # === Step 0: Create test TIFF with scanner metadata ===
    print("\n[Step 0] Creating test TIFF file with scanner metadata...")
    create_test_image(
        path=input_file,
        size=(4000, 3000),
        color=(240, 235, 230),
        format="TIFF",
        scanner_make=SCANNER_MAKE,
        scanner_model=SCANNER_MODEL,
    )
    print(f"[OK] Created test TIFF: {input_file.name}")
    print(f"  Size: {input_file.stat().st_size / (1024 * 1024):.1f} MB")

    # Verify scan-batcher metadata
    tags = exifer.read(input_file, [
        TAG_IFD0_MAKE,
        TAG_IFD0_MODEL,
        TAG_XMP_TIFF_MAKE,
        TAG_XMP_TIFF_MODEL,
        TAG_XMP_XMPMM_DOCUMENT_ID,
        TAG_XMP_XMPMM_INSTANCE_ID,
        TAG_XMP_EXIF_DATETIME_DIGITIZED,
    ])

    document_id = tags[TAG_XMP_XMPMM_DOCUMENT_ID]
    assert document_id, "DocumentID must be set"
    assert tags[TAG_XMP_XMPMM_INSTANCE_ID], "InstanceID must be set"

    print(f"[OK] IFD0:Make/Model: {tags[TAG_IFD0_MAKE]} {tags[TAG_IFD0_MODEL]}")
    print(f"[OK] XMP-tiff:Make/Model: {tags[TAG_XMP_TIFF_MAKE]} {tags[TAG_XMP_TIFF_MODEL]}")
    print(f"[OK] DocumentID: {document_id}")
    print(f"[OK] DateTimeDigitized: {tags[TAG_XMP_EXIF_DATETIME_DIGITIZED]}")

    digitized = tags.get(TAG_XMP_EXIF_DATETIME_DIGITIZED, "")
    assert "+" in digitized or "-" in digitized, f"DateTimeDigitized must have TZ: {digitized}"

    history = historian.read_history(input_file)
    actions = [e.get("action") for e in history]
    assert XMP_ACTION_CREATED in actions
    assert XMP_ACTION_EDITED in actions
    print(f"[OK] XMP History actions: {actions}")
    for entry in history:
        when = entry.get("when", "")
        assert "+" in when or "-" in when, f"History When must have TZ: {when}"
    print("=" * 60)

    # === Step 1: Run FileOrganizer ===
    print("\n[Step 1] Running FileOrganizer...")
    organizer = FileOrganizer(logger)
    processed_count = organizer(
        input_path=tmp_path,
        recursive=False,
        copy_mode=True,  # Preserve original for inspection
    )
    assert processed_count == 1, f"Expected 1, got {processed_count}"
    print(f"[OK] FileOrganizer processed {processed_count} file(s)")

    processed_root = tmp_path / "processed"
    master = _find_file(processed_root, "*.RAW.tif")
    assert "SOURCES" in str(master)
    print(f"[OK] Organized file: {master}")

    master_ids = exifer.read(master, [
        TAG_XMP_XMPMM_DOCUMENT_ID,
        TAG_XMP_XMPMM_INSTANCE_ID,
        TAG_XMP_DC_IDENTIFIER,
    ])
    assert master_ids[TAG_XMP_XMPMM_DOCUMENT_ID] == document_id
    master_identifier = master_ids.get(TAG_XMP_DC_IDENTIFIER)
    assert master_identifier, "Master must have dc:Identifier after organizer"
    print(f"[OK] DocumentID preserved: {master_ids[TAG_XMP_XMPMM_DOCUMENT_ID]}")

    master_history = historian.read_history(master)
    assert len(master_history) >= 3
    print(f"[OK] Master history entries: {len(master_history)}")
    print("=" * 60)

    # === Step 2: Run PreviewMaker ===
    print("\n[Step 2] Running PreviewMaker...")
    maker = PreviewMaker(logger)
    prv_count = maker(
        path=processed_root,
        overwrite=False,
        max_size=1200,
        quality=85,
    )
    assert prv_count == 1
    print(f"[OK] PreviewMaker generated {prv_count} preview(s)")

    prv = _find_file(processed_root, "*.PRV.jpg")
    print(f"[OK] Preview file: {prv}")

    prv_tags = exifer.read(prv, [
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

    assert prv_tags[TAG_XMP_XMPMM_DOCUMENT_ID] == document_id
    assert prv_tags[TAG_XMP_XMPMM_INSTANCE_ID] != master_ids[TAG_XMP_XMPMM_INSTANCE_ID]
    assert prv_tags[TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID] == document_id
    assert prv_tags[TAG_XMP_DC_RELATION] == master_identifier
    assert prv_tags[TAG_XMP_DC_FORMAT] == "image/jpeg"
    assert prv_tags[TAG_XMP_TIFF_MAKE] == SCANNER_MAKE
    assert prv_tags[TAG_XMP_TIFF_MODEL] == SCANNER_MODEL

    prv_digitized = prv_tags.get(TAG_XMP_EXIF_DATETIME_DIGITIZED, "")
    assert "+" in prv_digitized or "-" in prv_digitized

    prv_history = historian.read_history(prv)
    prv_actions = [e.get("action") for e in prv_history]
    assert XMP_ACTION_CONVERTED in prv_actions
    assert XMP_ACTION_EDITED in prv_actions

    print(f"[OK] PRV DocumentID: {prv_tags[TAG_XMP_XMPMM_DOCUMENT_ID]}")
    print(f"[OK] PRV DerivedFrom: {prv_tags[TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID]}")
    print(f"[OK] PRV Relation -> master: {prv_tags[TAG_XMP_DC_RELATION]}")
    print(f"[OK] PRV Make/Model: {prv_tags[TAG_XMP_TIFF_MAKE]} {prv_tags[TAG_XMP_TIFF_MODEL]}")
    print(f"[OK] PRV Format: {prv_tags[TAG_XMP_DC_FORMAT]}")
    print(f"[OK] PRV History: {prv_actions}")
    print("=" * 60)

    # Summary
    print("\nPIPELINE COMPLETE!")
    print(f"  Master:  {master}")
    print(f"  Preview: {prv}")
    print(f"\nTo inspect metadata manually:")
    print(f"  exiftool -a -G1 \"{master}\"")
    print(f"  exiftool -a -G1 \"{prv}\"")
    print(f"\nFiles preserved in: {tmp_path}")

