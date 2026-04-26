"""
Tests for FileProcessor class.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from common.logger import Logger
from file_organizer.processor import FileProcessor


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

    def _minimal_config(self) -> dict[str, object]:
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

    def test_process_skips_write_when_no_metadata(self):
        """process() skips _write_metadata when no_metadata=True."""
        processor = FileProcessor(self.logger)
        parsed: dict[str, int | str] = {
            "year": 1950, "month": 6, "day": 15,
            "hour": 12, "minute": 0, "second": 0,
            "modifier": "E", "group": "FAM", "subgroup": "POR",
            "sequence": 1, "side": "A", "suffix": "MSR", "extension": "tiff",
        }

        with patch.object(processor, '_write_metadata') as mock_write:
            processor.process(Path("dummy.tiff"), parsed, no_metadata=True)

        mock_write.assert_not_called()

    def test_process_calls_write_when_no_metadata_is_false(self):
        """process() calls _write_metadata normally when flag is off."""
        processor = FileProcessor(self.logger)
        parsed: dict[str, int | str] = {
            "year": 1950, "month": 6, "day": 15,
            "hour": 12, "minute": 0, "second": 0,
            "modifier": "E", "group": "FAM", "subgroup": "POR",
            "sequence": 1, "side": "A", "suffix": "MSR", "extension": "tiff",
        }

        with patch.object(processor, '_write_metadata') as mock_write:
            processor.process(Path("dummy.tiff"), parsed, no_metadata=False)

        mock_write.assert_called_once()
