import os
import shutil
import tempfile
import json
import subprocess
import pytest
from pathlib import Path
from PIL import Image
from filename_metadata_extractor.plugin import FilenameMetadataExtractor

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
        
        plugin = FilenameMetadataExtractor()
        
        # 2. Execute
        result = plugin.process(str(file_path), {})
        
        # 3. Verify
        assert result is True
        
        # Check file moved to processed/
        processed_dir = temp_dir / "processed"
        processed_file_path = processed_dir / filename
        
        assert processed_dir.exists()
        assert processed_file_path.exists()
        assert not file_path.exists() # Original should be gone
        
        # Check Metadata
        meta = self.get_exiftool_json(processed_file_path)
        
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
        
        plugin = FilenameMetadataExtractor()
        
        # Execute
        result = plugin.process(str(file_path), {})
        
        assert result is True
        
        # Verify normalized filename in processed folder
        processed_file_path = temp_dir / "processed" / expected_filename
        assert processed_file_path.exists()

    def test_process_circa_date(self, temp_dir):
        # Test processing of Circa date (no time in EXIF)
        filename = "1950.00.00.00.00.00.C.FAM.POR.0002.A.WEB.jpg"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        plugin = FilenameMetadataExtractor()
        
        result = plugin.process(str(file_path), {})
        assert result is True
        
        processed_file_path = temp_dir / "processed" / filename
        assert processed_file_path.exists()
        
        meta = self.get_exiftool_json(processed_file_path)
        
        # Should NOT have DateTimeOriginal for Circa dates
        assert "ExifIFD:DateTimeOriginal" not in meta and "EXIF:DateTimeOriginal" not in meta
        
        # Should have partial date in XMP
        assert "XMP:DateCreated" in meta or "XMP-photoshop:DateCreated" in meta
        date_created = meta.get("XMP:DateCreated") or meta.get("XMP-photoshop:DateCreated")
        assert str(date_created) == "1950"
