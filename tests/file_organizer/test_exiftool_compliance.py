import json
import shutil
import subprocess
import tempfile
from pathlib import Path
import pytest
from PIL import Image
from file_organizer.organizer import FileOrganizer

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

    def _minimal_config(self) -> dict:
        """Return minimal organizer config with required metadata languages."""
        return {
            "metadata": {
                "languages": {
                    "en-US": {
                        "default": True,
                        "creator": "Test Author",
                        "credit": "Test Archive",
                        "rights": "Test Rights",
                        "terms": "Test Terms",
                        "source": "Test Source",
                        "description": "Test description",
                    }
                }
            }
        }

    def test_full_metadata_compliance(self, temp_dir, logger):
        """Verify that all required metadata fields are written and visible to exiftool."""
        filename = "1950.06.15.12.30.45.E.FAM.POR.0001.A.MSR.tiff"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        processor = FileOrganizer(logger)
        config = {
            "metadata": {
                "languages": {
                    "en-US": {
                        "default": True,
                        "creator": "John Doe",
                        "credit": "The Archive",
                        "rights": "Public Domain",
                        "terms": "Free to use",
                        "source": "Box 42",
                        "description": "Test description for 1950-06-15 image",
                    }
                }
            }
        }
        processor.process(file_path, config)
        
        # 1950 / 1950.06.15 / SOURCES
        processed_path = temp_dir / "processed" / "1950" / "1950.06.15" / "SOURCES" / filename
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

        # 4. Check Description (now driven by config, language-specific)
        # We expect the default language (en-US) to be visible via
        # XMP:Description / XMP-dc:Description-*.
        desc = (
            meta.get("XMP:Description")
            or meta.get("XMP-dc:Description-en-US")
            or meta.get("XMP-dc:Description")
        )
        assert desc is not None
        assert "Test description for 1950-06-15 image" in str(desc)

        # 5. Check Configurable Fields
        # XMP-dc:Creator is an array/bag, so ExifTool returns it as a string representation of array
        creator = meta.get("XMP:Creator") or meta.get("XMP-dc:Creator")
        assert creator == "John Doe" or creator == "['John Doe']" or "John Doe" in creator
        assert meta.get("XMP:Credit") == "The Archive" or meta.get("XMP-photoshop:Credit") == "The Archive"
        assert meta.get("XMP:Rights") == "Public Domain" or meta.get("XMP-dc:Rights") == "Public Domain"
        assert meta.get("XMP:UsageTerms") == "Free to use" or meta.get("XMP-xmpRights:UsageTerms") == "Free to use"
        assert meta.get("XMP:Source") == "Box 42" or meta.get("XMP-dc:Source") == "Box 42"
        assert meta.get("XMP:Title") == file_path.stem or meta.get("XMP-dc:Title") == file_path.stem

    def test_partial_date_compliance(self, temp_dir, logger):
        """Verify partial date handling with exiftool."""
        filename = "1950.00.00.00.00.00.C.FAM.POR.0002.A.WEB.jpg"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        processor = FileOrganizer(logger)
        processor.process(file_path, self._minimal_config())
        
        # 1950 / 1950.00.00 / DERIVATIVES
        processed_path = temp_dir / "processed" / "1950" / "1950.00.00" / "DERIVATIVES" / filename
        
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

    def test_datetimedigitized_from_createdate(self, temp_dir, logger):
        """Verify that DateTimeDigitized is copied from CreateDate if not already set."""
        filename = "2025.11.29.14.00.00.C.001.001.0001.A.RAW.tiff"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        # Simulate VueScan behavior: write CreateDate but not DateTimeDigitized
        subprocess.run([
            "exiftool",
            "-EXIF:CreateDate=2025:11:29 14:00:00",
            "-overwrite_original",
            str(file_path)
        ], check=True)
        
        # Verify CreateDate is set but DateTimeDigitized is not
        meta_before = self.get_exiftool_json(file_path)
        assert "EXIF:CreateDate" in meta_before or "ExifIFD:CreateDate" in meta_before
        assert "EXIF:DateTimeDigitized" not in meta_before
        assert "ExifIFD:DateTimeDigitized" not in meta_before
        
        # Process the file
        processor = FileOrganizer(logger)
        processor.process(file_path, self._minimal_config())
        
        # Check processed file: 2025 / 2025.11.29 / SOURCES
        processed_path = temp_dir / "processed" / "2025" / "2025.11.29" / "SOURCES" / filename
        assert processed_path.exists()
        
        meta_after = self.get_exiftool_json(processed_path)
        
        # DateTimeDigitized should now be set from CreateDate (in XMP namespace)
        assert "XMP-exif:DateTimeDigitized" in meta_after or "XMP:DateTimeDigitized" in meta_after
        dt_digitized = meta_after.get("XMP-exif:DateTimeDigitized") or meta_after.get("XMP:DateTimeDigitized")
        assert dt_digitized == "2025:11:29 14:00:00"
        
    def test_datetimedigitized_not_overwritten(self, temp_dir, logger):
        """Verify that existing DateTimeDigitized is not overwritten."""
        filename = "2025.11.29.14.00.00.C.001.001.0001.A.RAW.tiff"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        # Set both CreateDate and DateTimeDigitized (use XMP namespace as EXIF IFD doesn't support it in TIFF)
        subprocess.run([
            "exiftool",
            "-EXIF:CreateDate=2025:11:29 14:00:00",
            "-XMP-exif:DateTimeDigitized=2025:11:29 13:00:00",
            "-overwrite_original",
            str(file_path)
        ], check=True)
        
        # Process the file
        processor = FileOrganizer(logger)
        processor.process(file_path, self._minimal_config())
        
        # Check processed file: 2025 / 2025.11.29 / SOURCES
        processed_path = temp_dir / "processed" / "2025" / "2025.11.29" / "SOURCES" / filename
        assert processed_path.exists(), f"File not found at {processed_path}"
        
        meta_after = self.get_exiftool_json(processed_path)
        
        # DateTimeDigitized should remain unchanged (original value, not CreateDate)
        # Note: Since EXIF:DateTimeDigitized can't be written to TIFF, processor writes to XMP-exif instead
        dt_digitized = meta_after.get("XMP-exif:DateTimeDigitized") or meta_after.get("XMP:DateTimeDigitized")
        assert dt_digitized == "2025:11:29 13:00:00"



