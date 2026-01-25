"""Tests for FileOrganizer custom formatting and routing."""

import shutil
import tempfile
from pathlib import Path
from typing import Any

from file_organizer.organizer import FileOrganizer
from common.logger import Logger
from common.router import Router
from common.formatter import Formatter

class TestFileOrganizerCustomFormatting:
    """Test cases for FileOrganizer with custom formatters."""

    def setup_method(self):
        """Setup for each test method."""
        self.logger = Logger("test")
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Cleanup after each test method."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_dummy_image(self, path: Path):
        """Create a simple dummy file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("dummy")

    def test_process_with_flat_path_structure(self):
        """Test file organization with flat path structure (no year folder)."""
        filename = "2024.03.15.14.30.00.E.TEST.GRP.0001.A.RAW.tif"
        file_path = self.temp_dir / filename
        self.create_dummy_image(file_path)
        processed_root = self.temp_dir / "processed"

        formatter = Formatter(
            path_template="{year:04d}.{month:02d}.{day:02d}",
            filename_template="{year:04d}.{month:02d}.{day:02d}.{hour:02d}.{minute:02d}.{second:02d}.{modifier}.{group}.{subgroup}.{sequence:04d}.{side}.{suffix}"
        )

        organizer = FileOrganizer(self.logger)
        # Inject custom formatter into the organizer's router
        organizer._router._formatter = formatter

        # Parse filename to passed to _calculate_destination_paths
        parsed = organizer._parse_and_validate(file_path.name)
        assert parsed is not None

        # Check destination calculation
        dest_path, _, _ = organizer._calculate_destination_paths(file_path, parsed, processed_root)

        # Expected: processed/2024.03.15/SOURCES/filename
        # Note: SOURCES is appended by Router for images usually, unless format template handles it differently?
        # Standard Router.get_target_folder appends 'SOURCES' or 'DERIVATIVES' relative to path_template result.
        expected_parent = processed_root / "2024.03.15" / "SOURCES"
        assert dest_path.parent == expected_parent
        assert dest_path.name == filename

    def test_process_with_month_grouping(self):
        """Test file organization grouped by year and month."""
        filename = "2024.03.15.14.30.00.E.TEST.GRP.0001.A.MSR.tif"
        file_path = self.temp_dir / filename
        self.create_dummy_image(file_path)
        processed_root = self.temp_dir / "processed"

        formatter = Formatter(
            path_template="{year:04d}/{year:04d}.{month:02d}",
            filename_template="{year:04d}.{month:02d}.{day:02d}.{hour:02d}.{minute:02d}.{second:02d}.{modifier}.{group}.{subgroup}.{sequence:04d}.{side}.{suffix}"
        )

        organizer = FileOrganizer(self.logger)
        organizer._router._formatter = formatter

        parsed = organizer._parse_and_validate(file_path.name)
        dest_path, _, _ = organizer._calculate_destination_paths(file_path, parsed, processed_root)

        # {year}/{year}.{month} -> 2024/2024.03
        expected_parent = processed_root / "2024" / "2024.03" / "SOURCES"
        assert dest_path.parent == expected_parent

    def test_process_with_group_in_path(self):
        """Test file organization with group component in path."""
        filename = "2024.03.15.14.30.00.E.FAM.POR.0001.A.RAW.tif"
        file_path = self.temp_dir / filename
        self.create_dummy_image(file_path)
        processed_root = self.temp_dir / "processed"

        formatter = Formatter(
            path_template="{group}/{year:04d}/{year:04d}.{month:02d}.{day:02d}",
            filename_template="{year:04d}.{month:02d}.{day:02d}.{hour:02d}.{minute:02d}.{second:02d}.{modifier}.{group}.{subgroup}.{sequence:04d}.{side}.{suffix}"
        )

        organizer = FileOrganizer(self.logger)
        organizer._router._formatter = formatter

        parsed = organizer._parse_and_validate(file_path.name)
        dest_path, _, _ = organizer._calculate_destination_paths(file_path, parsed, processed_root)

        # {group}/{year}/{date} -> FAM.POR/2024/2024.03.15
        group_part = parsed.group
        expected_parent = processed_root / group_part / "2024" / "2024.03.15" / "SOURCES"
        assert dest_path.parent == expected_parent

    def test_process_with_compact_filename(self):
        """Test file organization with compact filename format."""
        original_filename = "2024.03.15.14.30.00.E.TEST.GRP.0042.A.RAW.tif"
        file_path = self.temp_dir / original_filename
        self.create_dummy_image(file_path)
        processed_root = self.temp_dir / "processed"

        formatter = Formatter(
            path_template="{year:04d}/{year:04d}.{month:02d}.{day:02d}",
            filename_template="{year:04d}{month:02d}{day:02d}_{hour:02d}{minute:02d}{second:02d}_{group}_{suffix}"
        )

        organizer = FileOrganizer(self.logger)
        organizer._router._formatter = formatter

        parsed = organizer._parse_and_validate(file_path.name)
        dest_path, _, _ = organizer._calculate_destination_paths(file_path, parsed, processed_root)

        # File should have compact name: 20240315_143000_TEST_RAW.tif (assuming sub group GRP is ignored)
        # Note: 'TEST' is the group (from TEST.GRP) - GRP is subgroup. Template uses {group}.
        expected_filename = "20240315_143000_TEST_RAW.tif"
        assert dest_path.name == expected_filename
