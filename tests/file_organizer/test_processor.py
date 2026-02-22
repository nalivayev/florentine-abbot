"""
Tests for FileProcessor class.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from common.logger import Logger
from common.naming import ParsedFilename
from file_organizer.processor import FileProcessor
from tests.common.test_utils import create_test_image


class TestFileProcessor:
    """
    Tests for FileProcessor suffix routing and file processing.
    """

    def setup_method(self):
        """
        Setup for each test method.
        """
        self.temp_dir = None
        self.logger = Logger("test_processor", console=True)

    def teardown_method(self):
        """
        Cleanup after each test method.
        """
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_temp_dir(self) -> Path:
        """
        Create a temporary directory.
        """
        temp_dir = tempfile.mkdtemp()
        self.temp_dir = Path(temp_dir)
        return self.temp_dir

    def create_dummy_image(self, path: Path):
        """
        Create a simple 100x100 RGB image with DocumentID/InstanceID.
        """
        create_test_image(path, color='red')

    def _minimal_config(self) -> dict:
        """
        Minimal configuration for testing.
        """
        return {
            "languages": {
                "en-US": {
                    "default": True,
                    "creator": ["Test User"],
                    "description": "Test description",
                }
            }
        }

    def test_parse_and_validate_valid_file(self):
        """
        Test _parse_and_validate with valid filename.
        """
        processor = FileProcessor(self.logger)
        result = processor._parse_and_validate('1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')
        assert result is not None
        assert result.year == 1950

    def test_parse_and_validate_invalid_file(self):
        """
        Test _parse_and_validate with invalid filename.
        """
        processor = FileProcessor(self.logger)
        result = processor._parse_and_validate('invalid.jpg')
        assert result is None

    def test_parse_and_validate_invalid_date(self):
        """
        Test _parse_and_validate with invalid date.
        """
        processor = FileProcessor(self.logger)
        result = processor._parse_and_validate('1950.13.15.00.00.00.E.FAM.POR.000001.A.MSR.tiff')
        assert result is None

    def test_process_skips_write_when_no_metadata(self):
        """process() returns True without calling _write_metadata."""
        processor = FileProcessor(self.logger)
        parsed = ParsedFilename(
            year=1950, month=6, day=15,
            hour=12, minute=0, second=0,
            modifier="E", group="FAM", subgroup="POR",
            sequence="000001", side="A", suffix="MSR", extension="tiff",
        )

        with patch.object(processor, '_write_metadata') as mock_write:
            result = processor.process(Path("dummy.tiff"), parsed, no_metadata=True)

        assert result is True
        mock_write.assert_not_called()

    def test_process_calls_write_when_no_metadata_is_false(self):
        """process() calls _write_metadata normally when flag is off."""
        processor = FileProcessor(self.logger)
        parsed = ParsedFilename(
            year=1950, month=6, day=15,
            hour=12, minute=0, second=0,
            modifier="E", group="FAM", subgroup="POR",
            sequence="000001", side="A", suffix="MSR", extension="tiff",
        )

        with patch.object(processor, '_write_metadata', return_value=True) as mock_write:
            result = processor.process(Path("dummy.tiff"), parsed, no_metadata=False)

        assert result is True
        mock_write.assert_called_once()

