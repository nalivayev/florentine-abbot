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
