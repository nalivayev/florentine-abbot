"""Unit tests for FileOrganizer (processing logic)."""

import pytest
from pathlib import Path
from file_organizer.organizer import FileOrganizer
from common.naming import FilenameParser


class TestFileOrganizer:
    """Test cases for FileOrganizer processing API."""

    @pytest.fixture
    def processor(self, logger):
        """Create organizer instance."""
        return FileOrganizer(logger)

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return FilenameParser()

    def test_should_process_valid_tiff(self, processor):
        """Test should_process accepts valid TIFF file."""
        assert processor.should_process(Path('1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')) is True

    def test_should_process_valid_jpg(self, processor):
        """Test should_process accepts valid JPG file."""
        assert processor.should_process(Path('1950.06.00.00.00.00.C.FAM.POR.000002.R.WEB.jpg')) is True

    def test_should_process_invalid_extension(self, processor):
        """Test should_process rejects invalid extension."""
        assert processor.should_process(Path('1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.png')) is False

    def test_should_process_invalid_filename(self, processor):
        """Test should_process rejects invalid filename format."""
        assert processor.should_process(Path('invalid.jpg')) is False

    def test_should_process_invalid_date(self, processor):
        """Test should_process rejects invalid date."""
        assert processor.should_process(Path('1950.13.15.00.00.00.E.FAM.POR.000001.A.MSR.tiff')) is False

    def test_should_process_case_insensitive_extension(self, processor):
        """Test should_process works with uppercase extensions."""
        assert processor.should_process(Path('1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.TIFF')) is True
        assert processor.should_process(Path('1950.06.15.12.00.00.E.FAM.POR.000001.A.WEB.JPG')) is True

    def test_should_process_skips_processed_folder(self, processor):
        """Test should_process skips files in 'processed' subfolder."""
        assert processor.should_process(Path('C:/watch/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')) is True
        assert processor.should_process(Path('C:/watch/processed/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')) is False
        assert processor.should_process(Path('C:/watch/subfolder/processed/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')) is False
        assert processor.should_process(Path('C:/watch/processed/subfolder/1950.06.15.12.00.00.E.FAM.POR.000001.A.WEB.jpg')) is False

    def test_should_process_processes_similar_folder_names(self, processor):
        """Test should_process processes files in folders with similar names to 'processed'."""
        # These should be processed - only exact 'processed' folder name is skipped
        assert processor.should_process(Path('C:/watch/my_processed_files/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')) is True
        assert processor.should_process(Path('C:/watch/not_processed/1950.06.15.12.00.00.E.FAM.POR.000001.A.WEB.jpg')) is True
        assert processor.should_process(Path('C:/watch/preprocessed/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')) is True

    def test_parse_and_validate_valid_file(self, processor):
        """Test _parse_and_validate with valid filename."""
        result = processor._parse_and_validate('1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')
        assert result is not None
        assert result.year == 1950

    def test_parse_and_validate_invalid_file(self, processor):
        """Test _parse_and_validate with invalid filename."""
        result = processor._parse_and_validate('invalid.jpg')
        assert result is None

    def test_parse_and_validate_invalid_date(self, processor):
        """Test _parse_and_validate with invalid date."""
        result = processor._parse_and_validate('1950.13.15.00.00.00.E.FAM.POR.000001.A.MSR.tiff')
        assert result is None


