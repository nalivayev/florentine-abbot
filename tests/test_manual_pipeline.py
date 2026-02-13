"""Manual end-to-end test of the full pipeline.

This test is marked as 'manual' and excluded from regular test runs.
Run explicitly with: pytest tests/test_manual_pipeline.py -v
Or: pytest tests/test_manual_pipeline.py::test_full_pipeline -v
"""

import pytest
import tempfile
from pathlib import Path

from file_organizer.organizer import FileOrganizer
from preview_maker.maker import PreviewMaker
from common.logger import Logger
from common.exifer import Exifer
from common.metadata import TAG_IFD0_MAKE, TAG_IFD0_MODEL


@pytest.mark.manual
def test_full_pipeline():
    """Full pipeline test: create file → patch → organize → generate preview.
    
    This test creates a test TIFF file with scanner metadata (IFD0:Make/Model),
    patches it with scan-batcher (which adds DocumentID/InstanceID),
    organizes it with file-organizer (which adds dc:Type),
    and generates a preview with preview-maker.
    """
    # Setup temp directory
    temp_dir = Path(tempfile.mkdtemp(prefix="manual_test_"))
    logger = Logger("test_manual_pipeline", console=True)
    
    try:
        input_file = temp_dir / "1925.04.00.00.00.00.C.001.001.0001.A.RAW.tif"
        
        print(f"\nTest directory: {temp_dir}")
        print("="*60)
        
        # Step 0: Create test TIFF file with scanner metadata
        print("\n[Step 0] Creating test TIFF file with scanner metadata...")
        from tests.common.test_utils import create_test_image
        
        # Create image with scanner metadata (includes DocumentID/InstanceID/XMP History)
        create_test_image(
            path=input_file,
            size=(4000, 3000),
            color=(240, 235, 230),
            format="TIFF",
            scanner_make="Epson",
            scanner_model="Perfection V600",
        )
        print(f"✓ Created test TIFF: {input_file.name}")
        print(f"  Size: {input_file.stat().st_size / (1024*1024):.1f} MB")
        print(f"✓ Embedded scanner metadata: Epson Perfection V600")
        
        # Verify IFD0:Make/Model are present
        exifer = Exifer()
        tags = exifer.read(input_file, [TAG_IFD0_MAKE, TAG_IFD0_MODEL])
        ifd0_make = tags.get(TAG_IFD0_MAKE)
        ifd0_model = tags.get(TAG_IFD0_MODEL)
        if ifd0_make and ifd0_model:
            print(f"✓ Verified scanner metadata: {ifd0_make} {ifd0_model}")
        else:
            print(f"⚠ Warning: Scanner metadata not found (Make: {ifd0_make}, Model: {ifd0_model})")
        print("="*60)
        
        # Step 1: Run FileOrganizer
        print("\n[Step 1] Running FileOrganizer...")
        organizer = FileOrganizer(logger)
        
        processed_count = organizer(
            input_path=input_file.parent,
            recursive=False,
            copy_mode=True,  # Copy instead of move to preserve original
        )
        
        print(f"✓ FileOrganizer processed {processed_count} file(s)")
        assert processed_count == 1, "Expected 1 file to be processed"
        
        # Find organized file (in processed subfolder)
        organized_dir = input_file.parent / "processed"
        assert organized_dir.exists(), f"Organized directory not created: {organized_dir}"
        
        # Expected path: processed/1925/1925.04/SOURCES/1925.04.00.00.00.00.C.001.001.0001.A.RAW.tif
        organized_file = None
        for sources_dir in organized_dir.rglob("SOURCES"):
            for file in sources_dir.glob("*.tif"):
                organized_file = file
                break
            if organized_file:
                break
        
        assert organized_file is not None, f"Could not find organized file in {organized_dir}"
        print(f"✓ Organized file: {organized_file}")
        
        # Verify dc:Type was written by organizer
        tags = exifer.read(organized_file, ["XMP-dc:Type"])
        dc_type = tags.get("XMP-dc:Type")
        if dc_type:
            print(f"✓ Verified XMP-dc:Type: {dc_type}")
        else:
            print(f"⚠ Warning: XMP-dc:Type not found")
        print("="*60)
        
        # Step 2: Run PreviewMaker
        print("\n[Step 2] Running PreviewMaker...")
        maker = PreviewMaker(logger)
        
        # Find the archive base (where year folders are)
        archive_base = organized_dir
        
        prv_count = maker(
            path=archive_base,
            overwrite=False,
            max_size=1200,
            quality=85,
        )
        
        print(f"✓ PreviewMaker generated {prv_count} preview(s)")
        assert prv_count == 1, "Expected 1 preview to be generated"
        
        # Find PRV file
        prv_file = None
        for year_dir in organized_dir.rglob("1925*"):
            for file in year_dir.glob("*.PRV.jpg"):
                prv_file = file
                break
            if prv_file:
                break
        
        assert prv_file is not None, "Could not find PRV file"
        print(f"✓ Preview file: {prv_file}")
        print("="*60)
        
        # Summary
        print("\n✅ PIPELINE COMPLETE!")
        print(f"  Master: {organized_file}")
        print(f"  Preview: {prv_file}")
        print(f"\nTo inspect metadata manually:")
        print(f"  exiftool -a -G1 \"{organized_file}\"")
        print(f"  exiftool -a -G1 \"{prv_file}\"")
        print(f"\nTo check specific tags:")
        print(f"  exiftool -XMP-dc:Type -TIFF:Make -TIFF:Model \"{organized_file}\"")
        print(f"  exiftool -XMP-dc:Type -XMP-dc:Format -XMP-xmpMM:DerivedFromDocumentID \"{prv_file}\"")
        
    finally:
        # Cleanup temp directory
        # if temp_dir.exists():
        #     shutil.rmtree(temp_dir)
        #     print(f"\n✓ Cleaned up temp directory: {temp_dir}")
        print(f"\n📁 Files preserved in: {temp_dir}")

