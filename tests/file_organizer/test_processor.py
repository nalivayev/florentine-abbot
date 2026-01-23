"""Tests for FileProcessor class."""

import shutil
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from common.logger import Logger
from file_organizer.processor import FileProcessor


class TestFileProcessor:
    """Tests for FileProcessor suffix routing and file processing."""

    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = None
        self.logger = Logger("test_processor", console=True)

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

    def _minimal_config(self) -> dict:
        """Minimal configuration for testing."""
        return {
            "languages": {
                "en-US": {
                    "default": True,
                    "creator": ["Test User"],
                    "description": "Test description",
                }
            }
        }

    def test_should_process_valid_tiff(self):
        """Test should_process accepts valid TIFF file."""
        processor = FileProcessor(self.logger)
        assert processor.should_process(Path('1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')) is True

    def test_should_process_valid_jpg(self):
        """Test should_process accepts valid JPG file."""
        processor = FileProcessor(self.logger)
        assert processor.should_process(Path('1950.06.00.00.00.00.C.FAM.POR.000002.R.WEB.jpg')) is True

    def test_should_process_invalid_extension(self):
        """Test should_process rejects invalid extension."""
        processor = FileProcessor(self.logger)
        # PNG is a supported image extension; use a truly invalid one here
        assert processor.should_process(Path('1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.txt')) is False

    def test_should_process_invalid_filename(self):
        """Test should_process rejects invalid filename format."""
        processor = FileProcessor(self.logger)
        assert processor.should_process(Path('invalid.jpg')) is False

    def test_should_process_invalid_date(self):
        """Test should_process rejects invalid date."""
        processor = FileProcessor(self.logger)
        assert processor.should_process(Path('1950.13.15.00.00.00.E.FAM.POR.000001.A.MSR.tiff')) is False

    def test_should_process_case_insensitive_extension(self):
        """Test should_process works with uppercase extensions."""
        processor = FileProcessor(self.logger)
        assert processor.should_process(Path('1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.TIFF')) is True
        assert processor.should_process(Path('1950.06.15.12.00.00.E.FAM.POR.000001.A.WEB.JPG')) is True

    def test_should_process_skips_processed_folder(self):
        """Test should_process skips files in 'processed' subfolder."""
        processor = FileProcessor(self.logger)
        assert processor.should_process(Path('C:/watch/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')) is True
        assert processor.should_process(Path('C:/watch/processed/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')) is False
        assert processor.should_process(Path('C:/watch/subfolder/processed/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')) is False
        assert processor.should_process(Path('C:/watch/processed/subfolder/1950.06.15.12.00.00.E.FAM.POR.000001.A.WEB.jpg')) is False

    def test_should_process_processes_similar_folder_names(self):
        """Test should_process processes files in folders with similar names to 'processed'."""
        processor = FileProcessor(self.logger)
        # These should be processed - only exact 'processed' folder name is skipped
        assert processor.should_process(Path('C:/watch/my_processed_files/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')) is True
        assert processor.should_process(Path('C:/watch/not_processed/1950.06.15.12.00.00.E.FAM.POR.000001.A.WEB.jpg')) is True
        assert processor.should_process(Path('C:/watch/preprocessed/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')) is True

    def test_parse_and_validate_valid_file(self):
        """Test _parse_and_validate with valid filename."""
        processor = FileProcessor(self.logger)
        result = processor._parse_and_validate('1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')
        assert result is not None
        assert result.year == 1950

    def test_parse_and_validate_invalid_file(self):
        """Test _parse_and_validate with invalid filename."""
        processor = FileProcessor(self.logger)
        result = processor._parse_and_validate('invalid.jpg')
        assert result is None

    def test_parse_and_validate_invalid_date(self):
        """Test _parse_and_validate with invalid date."""
        processor = FileProcessor(self.logger)
        result = processor._parse_and_validate('1950.13.15.00.00.00.E.FAM.POR.000001.A.MSR.tiff')
        assert result is None

    def test_process_with_flat_path_structure(self):
        """Test file organization with flat path structure (no year folder)."""
        temp_dir = self.create_temp_dir()
        
        filename = "2024.03.15.14.30.00.E.TEST.GRP.0001.A.RAW.tif"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        # Create custom formatter with flat structure
        from common.formatter import Formatter
        
        formatter = Formatter(
            path_template="{year:04d}.{month:02d}.{day:02d}",
            filename_template="{year:04d}.{month:02d}.{day:02d}.{hour:02d}.{minute:02d}.{second:02d}.{modifier}.{group}.{subgroup}.{sequence:04d}.{side}.{suffix}"
        )
        
        # Initialize processor and inject custom formatter
        processor = FileProcessor(self.logger)
        processor._router._formatter = formatter
        
        # Check parsed
        parsed = processor._parse_and_validate(file_path.name)
        assert parsed is not None
        
        # Get destination path using custom formatter
        dest_path, _, _ = processor.get_destination_paths(file_path, parsed)
        
        # Expected: parent/processed/2024.03.15/SOURCES/filename
        expected_parent = temp_dir / "processed" / "2024.03.15" / "SOURCES"
        assert dest_path.parent == expected_parent
        assert dest_path.name == filename

    def test_process_with_month_grouping(self):
        """Test file organization grouped by year and month."""

        temp_dir = self.create_temp_dir()
        
        filename = "2024.03.15.14.30.00.E.TEST.GRP.0001.A.MSR.tif"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        from common.formatter import Formatter
        
        formatter = Formatter(
            path_template="{year:04d}/{year:04d}.{month:02d}",
            filename_template="{year:04d}.{month:02d}.{day:02d}.{hour:02d}.{minute:02d}.{second:02d}.{modifier}.{group}.{subgroup}.{sequence:04d}.{side}.{suffix}"
        )
        
        # Initialize processor and inject custom formatter
        processor = FileProcessor(self.logger)
        processor._router._formatter = formatter
        
        parsed = processor._parse_and_validate(file_path.name)
        dest_path, _, _ = processor.get_destination_paths(file_path, parsed)
        
        # {year}/{year}.{month} -> 2024/2024.03
        expected_parent = temp_dir / "processed" / "2024" / "2024.03" / "SOURCES"
        assert dest_path.parent == expected_parent
    
    def test_process_with_group_in_path(self):
        """Test file organization with group component in path."""
        temp_dir = self.create_temp_dir()
        
        filename = "2024.03.15.14.30.00.E.FAM.POR.0001.A.RAW.tif"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        from common.formatter import Formatter
        
        formatter = Formatter(
            path_template="{group}/{year:04d}/{year:04d}.{month:02d}.{day:02d}",
            filename_template="{year:04d}.{month:02d}.{day:02d}.{hour:02d}.{minute:02d}.{second:02d}.{modifier}.{group}.{subgroup}.{sequence:04d}.{side}.{suffix}"
        )
        
        # Initialize processor and inject custom formatter
        processor = FileProcessor(self.logger)
        processor._router._formatter = formatter
        
        parsed = processor._parse_and_validate(file_path.name)
        dest_path, _, _ = processor.get_destination_paths(file_path, parsed)
        assert parsed is not None
        
        # {group}/{year}/{date} -> FAM.POR/2024/2024.03.15 (assuming standard parsing puts FAM.POR in group)
        group_part = parsed.group
        expected_parent = temp_dir / "processed" / group_part / "2024" / "2024.03.15" / "SOURCES"
        assert dest_path.parent == expected_parent
    
    def test_process_with_compact_filename(self):
        """Test file organization with compact filename format."""
        temp_dir = self.create_temp_dir()
        
        original_filename = "2024.03.15.14.30.00.E.TEST.GRP.0042.A.RAW.tif"
        file_path = temp_dir / original_filename
        self.create_dummy_image(file_path)
        
        from common.formatter import Formatter
        
        formatter = Formatter(
            path_template="{year:04d}/{year:04d}.{month:02d}.{day:02d}",
            filename_template="{year:04d}{month:02d}{day:02d}_{hour:02d}{minute:02d}{second:02d}_{group}_{suffix}"
        )
        
        # Initialize processor and inject custom formatter
        processor = FileProcessor(self.logger)
        processor._router._formatter = formatter
        
        parsed = processor._parse_and_validate(file_path.name)
        dest_path, _, _ = processor.get_destination_paths(file_path, parsed)
        
        # File should have compact name: 20240315_143000_TEST_RAW.tif (assuming sub group GRP is ignored)
        expected_filename = "20240315_143000_TEST_RAW.tif"
        assert dest_path.name == expected_filename
