import os
import shutil
import tempfile
import json
import subprocess
import pytest
from pathlib import Path
from PIL import Image
from file_organizer.processor import ArchiveProcessor

class TestIntegration:
    @pytest.fixture
    def temp_dir(self):
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        # Cleanup
        shutil.rmtree(temp_dir)

    def create_dummy_image(self, path: Path):
        # Create a simple 100x100 RGB image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(path)

    def get_exiftool_json(self, file_path: Path):
        """Helper to read metadata using exiftool."""
        cmd = ["exiftool", "-json", "-G", str(file_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)[0]

    def test_process_valid_tiff(self, temp_dir):
        # 1. Setup
        filename = "1950.06.15.12.30.45.E.FAM.POR.0001.A.MSR.tiff"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        processor = ArchiveProcessor()
        
        # 2. Execute
        result = processor.process(file_path, {})
        
        # 3. Verify
        assert result is True
        
        # Check file moved to processed/YYYY.M/YYYY.MM.DD.M/SUFFIX/
        processed_root = temp_dir / "processed"
        # 1950.E / 1950.06.15.E / MSR
        expected_path = processed_root / "1950.E" / "1950.06.15.E" / "MSR" / filename
        
        assert expected_path.exists()
        assert not file_path.exists() # Original should be gone
        
        # Check Metadata
        meta = self.get_exiftool_json(expected_path)
        
        # Check XMP Identifier
        assert "XMP:Identifier" in meta or "XMP-dc:Identifier" in meta or "XMP-xmp:Identifier" in meta
        
        # Check Date (Exact date E)
        assert "ExifIFD:DateTimeOriginal" in meta or "EXIF:DateTimeOriginal" in meta
        dt_orig = meta.get("ExifIFD:DateTimeOriginal") or meta.get("EXIF:DateTimeOriginal")
        assert dt_orig == "1950:06:15 12:30:45"
        
        assert "XMP:DateCreated" in meta or "XMP-photoshop:DateCreated" in meta
        date_created = meta.get("XMP:DateCreated") or meta.get("XMP-photoshop:DateCreated")
        assert date_created == "1950:06:15 12:30:45" or date_created == "1950-06-15T12:30:45"

    def test_process_normalization(self, temp_dir):
        # Test that filename is normalized (sequence 1 -> 0001)
        # Input: 1 digit sequence
        filename = "1950.06.15.12.30.45.E.FAM.POR.1.A.MSR.tiff"
        expected_filename = "1950.06.15.12.30.45.E.FAM.POR.0001.A.MSR.tiff"
        
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        processor = ArchiveProcessor()
        
        # Execute
        result = processor.process(file_path, {})
        
        assert result is True
        
        # Verify normalized filename in processed folder
        # 1950.E / 1950.06.15.E / MSR
        expected_path = temp_dir / "processed" / "1950.E" / "1950.06.15.E" / "MSR" / expected_filename
        assert expected_path.exists()

    def test_process_circa_date(self, temp_dir):
        # Test processing of Circa date (no time in EXIF)
        filename = "1950.00.00.00.00.00.C.FAM.POR.0002.A.WEB.jpg"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        processor = ArchiveProcessor()
        
        result = processor.process(file_path, {})
        assert result is True
        
        # 1950.C / 1950.00.00.C / WEB
        expected_path = temp_dir / "processed" / "1950.C" / "1950.00.00.C" / "WEB" / filename
        assert expected_path.exists()
        
        meta = self.get_exiftool_json(expected_path)
        
        # Should NOT have DateTimeOriginal for Circa dates
        assert "ExifIFD:DateTimeOriginal" not in meta and "EXIF:DateTimeOriginal" not in meta
        
        # Should have partial date in XMP
        assert "XMP:DateCreated" in meta or "XMP-photoshop:DateCreated" in meta
        date_created = meta.get("XMP:DateCreated") or meta.get("XMP-photoshop:DateCreated")
        assert str(date_created) == "1950"
