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

    def test_default_routing_raw_to_sources(self):
        """RAW files should go to SOURCES/ with default routing."""
        temp_dir = self.create_temp_dir()
        
        filename = "2020.01.15.10.00.00.E.FAM.POR.0001.A.RAW.tif"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        processor = FileProcessor(self.logger)
        result = processor.process(file_path, self._minimal_config())
        
        assert result is True
        expected_path = temp_dir / "processed" / "2020" / "2020.01.15" / "SOURCES" / filename
        assert expected_path.exists()

    def test_default_routing_prv_to_date_root(self):
        """PRV files should go to date root with default routing."""
        temp_dir = self.create_temp_dir()
        
        filename = "2020.01.15.10.00.00.E.FAM.POR.0001.A.PRV.jpg"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        processor = FileProcessor(self.logger)
        result = processor.process(file_path, self._minimal_config())
        
        assert result is True
        expected_path = temp_dir / "processed" / "2020" / "2020.01.15" / filename
        assert expected_path.exists()
        # No subfolders for PRV
        date_dir = temp_dir / "processed" / "2020" / "2020.01.15"
        assert not (date_dir / "SOURCES").exists()
        assert not (date_dir / "DERIVATIVES").exists()

    def test_custom_routing_tiff_to_custom_folder(self):
        """TIFF files with custom routing should go to custom folder."""
        temp_dir = self.create_temp_dir()
        
        filename = "2020.01.15.10.00.00.E.FAM.POR.0001.A.TIFF.tif"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        # Custom routing: TIFF → MASTERS subfolder
        custom_routing = {
            "RAW": "SOURCES",
            "MSR": "SOURCES",
            "PRV": ".",
            "TIFF": "MASTERS",
        }
        
        processor = FileProcessor(self.logger, suffix_routing=custom_routing)
        result = processor.process(file_path, self._minimal_config())
        
        assert result is True
        expected_path = temp_dir / "processed" / "2020" / "2020.01.15" / "MASTERS" / filename
        assert expected_path.exists()

    def test_custom_routing_jpeg_to_date_root(self):
        """JPEG files with custom routing can go to date root."""
        temp_dir = self.create_temp_dir()
        
        filename = "2020.01.15.10.00.00.E.FAM.POR.0001.A.JPEG.jpg"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        # Custom routing: JPEG → date root (like PRV)
        custom_routing = {
            "RAW": "SOURCES",
            "JPEG": ".",
        }
        
        processor = FileProcessor(self.logger, suffix_routing=custom_routing)
        result = processor.process(file_path, self._minimal_config())
        
        assert result is True
        expected_path = temp_dir / "processed" / "2020" / "2020.01.15" / filename
        assert expected_path.exists()

    def test_custom_routing_multiple_custom_folders(self):
        """Multiple custom subfolders can be defined."""
        temp_dir = self.create_temp_dir()
        
        # Custom routing with multiple custom folders
        custom_routing = {
            "RAW": "ORIGINALS",
            "MSR": "MASTERS",
            "PRV": "PREVIEWS",
            "TIFF": "EDITS",
        }
        
        test_files = [
            ("2020.01.15.10.00.00.E.FAM.POR.0001.A.RAW.tif", "ORIGINALS"),
            ("2020.01.15.10.00.00.E.FAM.POR.0001.A.MSR.tif", "MASTERS"),
            ("2020.01.15.10.00.00.E.FAM.POR.0001.A.PRV.jpg", "PREVIEWS"),
            ("2020.01.15.10.00.00.E.FAM.POR.0001.A.TIFF.tif", "EDITS"),
        ]
        
        processor = FileProcessor(self.logger, suffix_routing=custom_routing)
        
        for filename, expected_subfolder in test_files:
            file_path = temp_dir / filename
            self.create_dummy_image(file_path)
            
            result = processor.process(file_path, self._minimal_config())
            assert result is True
            
            expected_path = temp_dir / "processed" / "2020" / "2020.01.15" / expected_subfolder / filename
            assert expected_path.exists(), f"Expected {filename} in {expected_subfolder}/"

    def test_unknown_suffix_defaults_to_derivatives(self):
        """Unknown suffixes should default to DERIVATIVES."""
        temp_dir = self.create_temp_dir()
        
        filename = "2020.01.15.10.00.00.E.FAM.POR.0001.A.UNKNOWN.tif"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        processor = FileProcessor(self.logger)
        result = processor.process(file_path, self._minimal_config())
        
        assert result is True
        expected_path = temp_dir / "processed" / "2020" / "2020.01.15" / "DERIVATIVES" / filename
        assert expected_path.exists()

    def test_case_insensitive_suffix_routing(self):
        """Suffix routing should be case-insensitive."""
        temp_dir = self.create_temp_dir()
        
        # Test different case variations
        test_files = [
            "2020.01.15.10.00.00.E.FAM.POR.0001.A.raw.tif",
            "2020.01.15.10.00.00.E.FAM.POR.0002.A.Raw.tif",
            "2020.01.15.10.00.00.E.FAM.POR.0003.A.RAW.tif",
        ]
        
        processor = FileProcessor(self.logger)
        
        for filename in test_files:
            file_path = temp_dir / filename
            self.create_dummy_image(file_path)
            
            result = processor.process(file_path, self._minimal_config())
            assert result is True
            
            # All should go to SOURCES regardless of case
            expected_path = temp_dir / "processed" / "2020" / "2020.01.15" / "SOURCES" / filename
            assert expected_path.exists(), f"{filename} should be in SOURCES/"
