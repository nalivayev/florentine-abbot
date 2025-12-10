import json
import shutil
import subprocess
import tempfile
from pathlib import Path
import pytest
from PIL import Image
from filename_metadata_extractor.plugin import FilenameMetadataExtractor

class TestExiftoolCompliance:
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def create_dummy_image(self, path: Path):
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(path)

    def get_exiftool_json(self, file_path: Path):
        """Helper to read metadata using exiftool."""
        cmd = ["exiftool", "-json", "-G", str(file_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)[0]

    def test_full_metadata_compliance(self, temp_dir):
        """Verify that all required metadata fields are written and visible to exiftool."""
        filename = "1950.06.15.12.30.45.E.FAM.POR.0001.A.MSR.tiff"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        plugin = FilenameMetadataExtractor()
        config = {
            "creator": "John Doe",
            "credit": "The Archive",
            "rights": "Public Domain",
            "usage_terms": "Free to use",
            "source": "Box 42"
        }
        plugin.process(str(file_path), config)
        
        processed_path = temp_dir / "processed" / filename
        assert processed_path.exists()
        
        meta = self.get_exiftool_json(processed_path)
        
        # 1. Check Identifiers
        # Note: Exiftool might flatten keys or use specific groups
        # We look for XMP-dc:Identifier and XMP-xmp:Identifier
        
        # XMP-dc:Identifier
        assert "XMP:Identifier" in meta or "XMP-dc:Identifier" in meta
        
        # 2. Check DateTimeOriginal (ExifIFD)
        # Should be in ExifIFD group or EXIF group
        assert "ExifIFD:DateTimeOriginal" in meta or "EXIF:DateTimeOriginal" in meta
        dt_orig = meta.get("ExifIFD:DateTimeOriginal") or meta.get("EXIF:DateTimeOriginal")
        assert dt_orig == "1950:06:15 12:30:45"
        
        # 3. Check XMP DateCreated
        # Photoshop schema
        assert "XMP:DateCreated" in meta or "XMP-photoshop:DateCreated" in meta
        # Value check might need loose matching for timezone or format
        date_created = meta.get("XMP:DateCreated") or meta.get("XMP-photoshop:DateCreated")
        assert "1950:06:15 12:30:45" in date_created or "1950-06-15" in date_created

        # 4. Check Description
        assert "XMP:Description" in meta or "XMP-dc:Description" in meta
        desc = meta.get("XMP:Description") or meta.get("XMP-dc:Description")
        assert "Exact date: 1950-06-15" in desc

        # 5. Check Configurable Fields
        assert meta.get("XMP:Creator") == "John Doe" or meta.get("XMP-dc:Creator") == "John Doe"
        assert meta.get("XMP:Credit") == "The Archive" or meta.get("XMP-photoshop:Credit") == "The Archive"
        assert meta.get("XMP:Rights") == "Public Domain" or meta.get("XMP-dc:Rights") == "Public Domain"
        assert meta.get("XMP:UsageTerms") == "Free to use" or meta.get("XMP-xmpRights:UsageTerms") == "Free to use"
        assert meta.get("XMP:Source") == "Box 42" or meta.get("XMP-dc:Source") == "Box 42"
        assert meta.get("XMP:Title") == file_path.stem or meta.get("XMP-dc:Title") == file_path.stem

    def test_partial_date_compliance(self, temp_dir):
        """Verify partial date handling with exiftool."""
        filename = "1950.00.00.00.00.00.C.FAM.POR.0002.A.WEB.jpg"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        plugin = FilenameMetadataExtractor()
        plugin.process(str(file_path), {})
        
        processed_path = temp_dir / "processed" / filename
        
        meta = self.get_exiftool_json(processed_path)
        
        # 1. DateTimeOriginal should be ABSENT
        assert "ExifIFD:DateTimeOriginal" not in meta
        
        # 2. XMP DateCreated should be present (partial)
        # Note: pyexiv2 writes Xmp.Iptc4xmpCore.DateCreated. 
        # Exiftool usually maps this to XMP-iptcCore:DateCreated or just XMP:DateCreated
        
        # Let's check if we can find the year 1950 in any DateCreated field
        found_date = False
        for key, value in meta.items():
            if "DateCreated" in key and "1950" in str(value):
                found_date = True
                break
        assert found_date, f"Could not find partial date 1950 in metadata: {meta}"
