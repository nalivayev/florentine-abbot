"""
Tests for MetadataWorkflow (scan_batcher).
"""

import datetime
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from common.logger import Logger
from tests.scan_batcher.fake_metadata_workflow import FakeMetadataWorkflow
from tests.common.test_utils import create_test_image, exiftool_available

import pytest


class TestMetadataWorkflow:
    """Tests for MetadataWorkflow including --no-metadata flag."""

    def setup_method(self):
        self.temp_dir = None

    def teardown_method(self):
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_temp_dir(self) -> Path:
        temp_dir = tempfile.mkdtemp()
        self.temp_dir = Path(temp_dir)
        return self.temp_dir

    @pytest.mark.skipif(not exiftool_available(), reason="exiftool not installed")
    def test_write_xmp_history_skipped_when_no_metadata(self):
        """_write_xmp_history returns True without calling exiftool."""
        temp_dir = self.create_temp_dir()
        file_path = temp_dir / "test.tiff"
        create_test_image(file_path, add_ids=False)

        logger = Logger("test", console=False)
        workflow = FakeMetadataWorkflow(logger, no_metadata=True)

        now = datetime.datetime.now().astimezone()

        with patch.object(workflow, '_exifer') as mock_exifer:
            result = workflow.write_xmp_metadata(file_path, now)

        assert result is True
        mock_exifer.write.assert_not_called()

    @pytest.mark.skipif(not exiftool_available(), reason="exiftool not installed")
    def test_write_xmp_history_works_when_no_metadata_is_false(self):
        """_write_xmp_history writes metadata normally when flag is off."""
        temp_dir = self.create_temp_dir()
        file_path = temp_dir / "test.tiff"
        create_test_image(file_path, add_ids=False)

        logger = Logger("test", console=False)
        workflow = FakeMetadataWorkflow(logger, no_metadata=False)

        now = datetime.datetime.now().astimezone()
        result = workflow.write_xmp_metadata(file_path, now)

        assert result is True
