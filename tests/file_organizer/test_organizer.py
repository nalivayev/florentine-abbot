"""Tests for FileOrganizer class."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image
from file_organizer.organizer import FileOrganizer
from common.naming import FilenameParser


class TestFileOrganizer:
    """Test cases for FileOrganizer processing API."""

    def setup_method(self):
        """Setup for each test method."""
        self.processor = None
        self.parser = FilenameParser()

    def test_should_process_valid_tiff(self, logger):
        """Test should_process accepts valid TIFF file."""
        processor = FileOrganizer(logger)
        assert processor.should_process(Path('1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')) is True

    def test_should_process_valid_jpg(self, logger):
        """Test should_process accepts valid JPG file."""
        processor = FileOrganizer(logger)
        assert processor.should_process(Path('1950.06.00.00.00.00.C.FAM.POR.000002.R.WEB.jpg')) is True

    def test_should_process_invalid_extension(self, logger):
        """Test should_process rejects invalid extension."""
        processor = FileOrganizer(logger)
        # PNG is a supported image extension; use a truly invalid one here
        assert processor.should_process(Path('1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.txt')) is False

    def test_should_process_invalid_filename(self, logger):
        """Test should_process rejects invalid filename format."""
        processor = FileOrganizer(logger)
        assert processor.should_process(Path('invalid.jpg')) is False

    def test_should_process_invalid_date(self, logger):
        """Test should_process rejects invalid date."""
        processor = FileOrganizer(logger)
        assert processor.should_process(Path('1950.13.15.00.00.00.E.FAM.POR.000001.A.MSR.tiff')) is False

    def test_should_process_case_insensitive_extension(self, logger):
        """Test should_process works with uppercase extensions."""
        processor = FileOrganizer(logger)
        assert processor.should_process(Path('1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.TIFF')) is True
        assert processor.should_process(Path('1950.06.15.12.00.00.E.FAM.POR.000001.A.WEB.JPG')) is True

    def test_should_process_skips_processed_folder(self, logger):
        """Test should_process skips files in 'processed' subfolder."""
        processor = FileOrganizer(logger)
        assert processor.should_process(Path('C:/watch/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')) is True
        assert processor.should_process(Path('C:/watch/processed/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')) is False
        assert processor.should_process(Path('C:/watch/subfolder/processed/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')) is False
        assert processor.should_process(Path('C:/watch/processed/subfolder/1950.06.15.12.00.00.E.FAM.POR.000001.A.WEB.jpg')) is False

    def test_should_process_processes_similar_folder_names(self, logger):
        """Test should_process processes files in folders with similar names to 'processed'."""
        processor = FileOrganizer(logger)
        # These should be processed - only exact 'processed' folder name is skipped
        assert processor.should_process(Path('C:/watch/my_processed_files/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')) is True
        assert processor.should_process(Path('C:/watch/not_processed/1950.06.15.12.00.00.E.FAM.POR.000001.A.WEB.jpg')) is True
        assert processor.should_process(Path('C:/watch/preprocessed/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')) is True

    def test_parse_and_validate_valid_file(self, logger):
        """Test _parse_and_validate with valid filename."""
        processor = FileOrganizer(logger)
        result = processor._parse_and_validate('1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')
        assert result is not None
        assert result.year == 1950

    def test_parse_and_validate_invalid_file(self, logger):
        """Test _parse_and_validate with invalid filename."""
        processor = FileOrganizer(logger)
        result = processor._parse_and_validate('invalid.jpg')
        assert result is None

    def test_parse_and_validate_invalid_date(self, logger):
        """Test _parse_and_validate with invalid date."""
        processor = FileOrganizer(logger)
        result = processor._parse_and_validate('1950.13.15.00.00.00.E.FAM.POR.000001.A.MSR.tiff')
        assert result is None


class TestFileOrganizerIntegration:
    """Integration tests for FileOrganizer with filesystem operations."""

    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = None

    def teardown_method(self):
        """Cleanup after each test method."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_temp_dir(self) -> Path:
        """Create a temporary directory."""
        temp_dir = tempfile.mkdtemp()
        self.temp_dir = Path(temp_dir)
        return self.temp_dir

    def create_dummy_image(self, path: Path):
        """Create a simple 100x100 RGB image."""
        img = Image.new('RGB', (100, 100), color='red')
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

    def test_process_valid_tiff(self, logger):
        """Test processing valid TIFF file."""
        temp_dir = self.create_temp_dir()
        
        # 1. Setup
        filename = "1950.06.15.12.30.45.E.FAM.POR.0001.A.MSR.tiff"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        processor = FileOrganizer(logger)

        # 2. Execute
        result = processor.process(file_path, self._minimal_config())
        
        # 3. Verify
        assert result is True
        
        # Check file moved to processed/YYYY/YYYY.MM.DD/SOURCES/
        processed_root = temp_dir / "processed"
        # 1950 / 1950.06.15 / SOURCES
        expected_path = processed_root / "1950" / "1950.06.15" / "SOURCES" / filename
        
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

    def test_process_normalization(self, logger):
        """Test that filename is normalized (sequence 1 -> 0001)."""
        temp_dir = self.create_temp_dir()
        
        # Input: 1 digit sequence
        filename = "1950.06.15.12.30.45.E.FAM.POR.1.A.MSR.tiff"
        expected_filename = "1950.06.15.12.30.45.E.FAM.POR.0001.A.MSR.tiff"
        
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        processor = FileOrganizer(logger)

        # Execute
        result = processor.process(file_path, self._minimal_config())
        
        assert result is True
        
        # Verify normalized filename in processed folder
        # 1950 / 1950.06.15 / SOURCES
        expected_path = temp_dir / "processed" / "1950" / "1950.06.15" / "SOURCES" / expected_filename
        assert expected_path.exists()

    def test_process_circa_date(self, logger):
        """Test processing of Circa date (no time in EXIF)."""
        temp_dir = self.create_temp_dir()
        
        filename = "1950.00.00.00.00.00.C.FAM.POR.0002.A.WEB.jpg"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        processor = FileOrganizer(logger)

        result = processor.process(file_path, self._minimal_config())
        assert result is True
        
        # 1950 / 1950.00.00 / DERIVATIVES
        expected_path = temp_dir / "processed" / "1950" / "1950.00.00" / "DERIVATIVES" / filename
        assert expected_path.exists()
        
        meta = self.get_exiftool_json(expected_path)
        
        # Should NOT have DateTimeOriginal for Circa dates
        assert "ExifIFD:DateTimeOriginal" not in meta and "EXIF:DateTimeOriginal" not in meta
        
        # Should have partial date in XMP
        assert "XMP:DateCreated" in meta or "XMP-photoshop:DateCreated" in meta
        date_created = meta.get("XMP:DateCreated") or meta.get("XMP-photoshop:DateCreated")
        assert str(date_created) == "1950"

    def test_process_preview_file_placed_in_date_root(self, logger):
        """PRV preview files should be placed directly in the date folder root."""
        temp_dir = self.create_temp_dir()

        # Exact date preview (PRV) file
        filename = "1950.06.15.12.30.45.E.FAM.POR.0003.A.PRV.jpg"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)

        processor = FileOrganizer(logger)

        # Execute
        result = processor.process(file_path, self._minimal_config())
        assert result is True

        # PRV should be stored in processed/YYYY/YYYY.MM.DD/ (no SOURCES/DERIVATIVES)
        expected_dir = temp_dir / "processed" / "1950" / "1950.06.15"
        expected_path = expected_dir / filename

        assert expected_path.exists()
        assert not file_path.exists()

        # Sanity check: no SOURCES/ or DERIVATIVES/ subfolder created for this PRV file
        assert not (expected_dir / "SOURCES").exists()
        assert not (expected_dir / "DERIVATIVES").exists()


class TestExiftoolCompliance:
    """Tests for FileOrganizer metadata compliance with exiftool."""

    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = None

    def teardown_method(self):
        """Cleanup after each test method."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_temp_dir(self) -> Path:
        """Create a temporary directory."""
        temp_dir = tempfile.mkdtemp()
        self.temp_dir = Path(temp_dir)
        return self.temp_dir

    def create_dummy_image(self, path: Path):
        """Create a simple 100x100 RGB image."""
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

    def test_full_metadata_compliance(self, logger):
        """Verify that all required metadata fields are written and visible to exiftool."""
        temp_dir = self.create_temp_dir()
        
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

    def test_partial_date_compliance(self, logger):
        """Verify partial date handling with exiftool."""
        temp_dir = self.create_temp_dir()
        
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

    def test_datetimedigitized_from_createdate(self, logger):
        """Verify that DateTimeDigitized is copied from CreateDate if not already set."""
        temp_dir = self.create_temp_dir()
        
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
        
    def test_datetimedigitized_not_overwritten(self, logger):
        """Verify that existing DateTimeDigitized is not overwritten."""
        temp_dir = self.create_temp_dir()
        
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
