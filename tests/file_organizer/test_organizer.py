"""
Tests for FileOrganizer class.
"""

import json
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from datetime import datetime, timezone

from typing import Any

import pytest

from file_organizer.organizer import FileOrganizer
from file_organizer.constants import DEFAULT_METADATA
from common.project_config import ProjectConfig
from common.constants import DEFAULT_CONFIG, TAG_XMP_XMPMM_INSTANCE_ID, TAG_XMP_XMPMM_DOCUMENT_ID, TAG_XMP_XMP_CREATOR_TOOL, TAG_XMP_XMPMM_HISTORY, XMP_ACTION_CREATED, XMP_ACTION_EDITED
from common.logger import Logger
from common.exifer import Exifer
from common.tagger import Tagger
from common.tags import HistoryTag


def _rmtree_force(path: Path) -> None:
    """Remove a directory tree, resetting read-only flags when necessary."""
    def _on_rm_error(_func: Any, p: str, _exc_info: Any) -> None:
        os.chmod(p, 0o700)
        os.unlink(p)
    shutil.rmtree(path, onerror=_on_rm_error)
from tests.common.test_utils import create_test_image


class TestFileOrganizer:
    """
    Test cases for FileOrganizer processing API.
    """

    def test_should_process_delegation(self, logger: Logger) -> None:
        """
        Test that should_process checks extension and path filters.
        """
        organizer = FileOrganizer(logger)
        output = Path('/archive/output')
        # Valid extension
        assert organizer.should_process(Path('1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff'), output_path=output) is True
        assert organizer.should_process(Path('invalid.jpg'), output_path=output) is True  # .jpg is supported extension
        # Invalid extension
        assert organizer.should_process(Path('file.txt'), output_path=output) is False

    def test_rejects_same_input_output(self, logger: Logger, tmp_path: Path) -> None:
        """Output equal to input must raise ValueError."""
        organizer = FileOrganizer(logger)
        with pytest.raises(ValueError, match="must not overlap"):
            organizer(input_path=tmp_path, output_path=tmp_path)

    def test_rejects_output_inside_input(self, logger: Logger, tmp_path: Path) -> None:
        """Output that is a subdirectory of input must raise ValueError."""
        organizer = FileOrganizer(logger)
        nested = tmp_path / "sub" / "deep"
        nested.mkdir(parents=True)
        with pytest.raises(ValueError, match="inside input path"):
            organizer(input_path=tmp_path, output_path=nested)

    def test_rejects_input_inside_output(self, logger: Logger, tmp_path: Path) -> None:
        """Input that is a subdirectory of output must raise ValueError."""
        organizer = FileOrganizer(logger)
        parent = tmp_path / "archive"
        child = parent / "inbox"
        parent.mkdir()
        child.mkdir()
        with pytest.raises(ValueError, match="inside output path"):
            organizer(input_path=child, output_path=parent)


class TestFileOrganizerIntegration:
    """
    Integration tests for FileOrganizer with filesystem operations.
    """

    def setup_method(self) -> None:
        """
        Setup for each test method.
        """
        self.temp_dir: Path | None = None
        ProjectConfig.instance(data=DEFAULT_CONFIG)

    def teardown_method(self) -> None:
        """
        Cleanup after each test method.
        """
        if self.temp_dir and self.temp_dir.exists():
            _rmtree_force(self.temp_dir)

    def create_temp_dir(self) -> tuple[Path, Path]:
        """
        Create a temporary root with sibling input/ and output/ subdirs.

        Returns:
            (input_dir, output_dir) as sibling directories.
        """
        root = Path(tempfile.mkdtemp())
        self.temp_dir = root
        input_dir = root / "input"
        input_dir.mkdir()
        output_dir = root / "output"
        return input_dir, output_dir

    def get_exiftool_json(self, file_path: Path) -> dict[str, Any]:
        """
        Helper to read metadata using exiftool.
        """
        cmd = ["exiftool", "-json", "-G", str(file_path)]
        # Force UTF-8 encoding to avoid Windows charmap errors
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8')
        return json.loads(result.stdout)[0]  # type: ignore[no-any-return]

    def _minimal_config(self) -> dict[str, Any]:
        """
        Return minimal organizer config with required metadata languages.
        """
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

    def _write_config(self, dir_path: Path, config: dict[str, Any] | None) -> Path | None:
        """
        Helper: write config dict to dir_path/config.json and return its path.
        """
        if config is None:
            return None
        cfg_path = dir_path / "config.json"
        cfg_path.write_text(json.dumps(config), encoding="utf-8")
        return cfg_path

    @staticmethod
    def _norm(v: object) -> str:
        """Normalize a tag value for comparison: lowercase, strip uuid: prefix and dashes."""
        if not isinstance(v, str):
            return str(v)
        return v.lower().replace('uuid:', '').replace('-', '')

    def test_process_valid_tiff(self, logger: Logger) -> None:
        """
        Test processing valid TIFF file.
        """
        input_dir, output_dir = self.create_temp_dir()
        
        # 1. Setup
        filename = "1950.06.15.12.30.45.E.FAM.POR.0001.A.MSR.tiff"
        file_path = input_dir / filename
        create_test_image(file_path)
        
        organizer = FileOrganizer(logger)

        # 2. Execute via batch API
        config_path = self._write_config(input_dir, self._minimal_config())
        result = organizer(
            input_path=input_dir,
            output_path=output_dir,
            config_path=config_path,
            recursive=False,
            copy_mode=False
        )

        # 3. Verify
        assert result["succeeded"] == 1
        
        # Check file moved to output/YYYY/YYYY.MM.DD/SOURCES/
        # 1950 / 1950.06.15 / SOURCES
        expected_path = output_dir / "1950" / "1950.06.15" / "SOURCES" / filename
        
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

    def test_process_normalization(self, logger: Logger) -> None:
        """
        Test that filename is normalized (sequence 1 -> 0001).
        """
        input_dir, output_dir = self.create_temp_dir()
        
        # Input: 1 digit sequence
        filename = "1950.06.15.12.30.45.E.FAM.POR.1.A.MSR.tiff"
        expected_filename = "1950.06.15.12.30.45.E.FAM.POR.0001.A.MSR.tiff"
        
        file_path = input_dir / filename
        create_test_image(file_path)
        
        organizer = FileOrganizer(logger)

        # Execute
        config_path = self._write_config(input_dir, self._minimal_config())
        processed_count = organizer(
            input_path=input_dir, 
            output_path=output_dir,
            config_path=config_path, 
            recursive=False, 
            copy_mode=False
        )
        
        assert processed_count["succeeded"] == 1
        
        # Verify normalized filename in output folder
        # 1950 / 1950.06.15 / SOURCES
        expected_path = output_dir / "1950" / "1950.06.15" / "SOURCES" / expected_filename
        assert expected_path.exists()

    def test_process_circa_date(self, logger: Logger) -> None:
        """
        Test processing of Circa date (no time in EXIF).
        """
        input_dir, output_dir = self.create_temp_dir()
        
        filename = "1950.00.00.00.00.00.C.FAM.POR.0002.A.WEB.jpg"
        file_path = input_dir / filename
        create_test_image(file_path)
        
        organizer = FileOrganizer(logger)

        config_path = self._write_config(input_dir, self._minimal_config())
        processed_count = organizer(
            input_path=input_dir, 
            output_path=output_dir,
            config_path=config_path, 
            recursive=False, 
            copy_mode=False
        )
        assert processed_count["succeeded"] == 1
        
        # 1950 / 1950.00.00 / DERIVATIVES
        expected_path = output_dir / "1950" / "1950.00.00" / "DERIVATIVES" / filename
        assert expected_path.exists()
        
        meta = self.get_exiftool_json(expected_path)
        
        # Should NOT have DateTimeOriginal for Circa dates
        assert "ExifIFD:DateTimeOriginal" not in meta and "EXIF:DateTimeOriginal" not in meta
        
        # Should have partial date in XMP
        assert "XMP:DateCreated" in meta or "XMP-photoshop:DateCreated" in meta
        date_created = meta.get("XMP:DateCreated") or meta.get("XMP-photoshop:DateCreated")
        assert str(date_created) == "1950"

    def test_process_preview_file_placed_in_date_root(self, logger: Logger) -> None:
        """
        PRV preview files should be placed directly in the date folder root.
        """
        input_dir, output_dir = self.create_temp_dir()

        # Exact date preview (PRV) file
        filename = "1950.06.15.12.30.45.E.FAM.POR.0003.A.PRV.jpg"
        file_path = input_dir / filename
        create_test_image(file_path)

        organizer = FileOrganizer(logger)

        # Execute
        config_path = self._write_config(input_dir, self._minimal_config())
        processed_count = organizer(
            input_path=input_dir, 
            output_path=output_dir,
            config_path=config_path, 
            recursive=False, 
            copy_mode=False
        )
        assert processed_count["succeeded"] == 1

        # PRV should be stored in output/YYYY/YYYY.MM.DD/ (no SOURCES/DERIVATIVES)
        expected_dir = output_dir / "1950" / "1950.06.15"
        expected_path = expected_dir / filename

        assert expected_path.exists()
        assert not file_path.exists()

        # Sanity check: no SOURCES/ or DERIVATIVES/ subfolder created for this PRV file
        assert not (expected_dir / "SOURCES").exists()
        assert not (expected_dir / "DERIVATIVES").exists()

    def test_protected_files_are_read_only(self, logger: Logger) -> None:
        """Files matched by a routing rule with protect=true should be read-only."""
        import stat

        input_dir, output_dir = self.create_temp_dir()

        # MSR → SOURCES with protect=true (default routes)
        filename = "1950.06.15.12.30.45.E.FAM.POR.0001.A.MSR.tiff"
        file_path = input_dir / filename
        create_test_image(file_path)

        organizer = FileOrganizer(logger)
        config_path = self._write_config(input_dir, self._minimal_config())
        processed_count = organizer(
            input_path=input_dir,
            output_path=output_dir,
            config_path=config_path,
            recursive=False,
            copy_mode=False,
        )
        assert processed_count["succeeded"] == 1

        dest = output_dir / "1950" / "1950.06.15" / "SOURCES" / filename
        assert dest.exists()

        mode = dest.stat().st_mode
        assert not (mode & stat.S_IWUSR), "Owner write bit should be cleared"
        assert not (mode & stat.S_IWGRP), "Group write bit should be cleared"
        assert not (mode & stat.S_IWOTH), "Other write bit should be cleared"

    def test_unprotected_files_stay_writable(self, logger: Logger) -> None:
        """Files matched by a rule without protect flag should remain writable."""
        import stat

        input_dir, output_dir = self.create_temp_dir()

        # WEB → DERIVATIVES, no protect flag (default routes)
        filename = "1950.06.15.12.30.45.E.FAM.POR.0001.A.WEB.jpg"
        file_path = input_dir / filename
        create_test_image(file_path)

        organizer = FileOrganizer(logger)
        config_path = self._write_config(input_dir, self._minimal_config())
        processed_count = organizer(
            input_path=input_dir,
            output_path=output_dir,
            config_path=config_path,
            recursive=False,
            copy_mode=False,
        )
        assert processed_count["succeeded"] == 1

        dest = output_dir / "1950" / "1950.06.15" / "DERIVATIVES" / filename
        assert dest.exists()

        mode = dest.stat().st_mode
        assert mode & stat.S_IWUSR, "Owner write bit should still be set"

    def test_date_modifier_scenarios(self, logger: Logger, require_exiftool: None) -> None:
        """Test FileOrganizer with different date modifiers (E, C, B, F, A).
        
        This test validates that files with various date precision levels
        are correctly processed and placed in appropriate year folders.
        Also verifies XMP History tracking works across different scenarios.
        """
        scenarios: list[dict[str, str]] = [
            {
                "name": "Exact Date",
                "filename": "2023.10.27.12.00.00.E.Group.Sub.0001.A.Orig.jpg",
                "folder_l1": "2023",
            },
            {
                "name": "Circa Year",
                "filename": "1950.00.00.00.00.00.C.Group.Sub.0002.A.Orig.jpg",
                "folder_l1": "1950",
            },
            {
                "name": "Before Year-Month",
                "filename": "1960.01.00.00.00.00.B.Group.Sub.0003.A.Orig.jpg",
                "folder_l1": "1960",
            },
            {
                "name": "After Year-Month-Day",
                "filename": "1970.05.20.00.00.00.F.Group.Sub.0004.A.Orig.jpg",
                "folder_l1": "1970",
            },
            {
                "name": "Absent Date",
                "filename": "0000.00.00.00.00.00.A.Group.Sub.0005.A.Orig.jpg",
                "folder_l1": "0000",
            },
        ]
        
        for scenario in scenarios:
            input_dir, output_dir = self.create_temp_dir()
            filename = scenario["filename"]
            file_path = input_dir / filename
            
            # Create test image
            create_test_image(file_path)
            
            # Write XMP identifiers and history entries
            ex = Exifer()
            
            # Check existing tags and only write missing ones
            existing = ex.read(file_path, [TAG_XMP_XMPMM_INSTANCE_ID, TAG_XMP_XMPMM_DOCUMENT_ID, TAG_XMP_XMP_CREATOR_TOOL])
            
            instance: str | None = existing.get(TAG_XMP_XMPMM_INSTANCE_ID)
            document: str | None = existing.get(TAG_XMP_XMPMM_DOCUMENT_ID)
            creator: str | None = existing.get(TAG_XMP_XMP_CREATOR_TOOL)
            
            to_write: dict[str, str] = {}
            if not instance:
                instance = uuid.uuid4().hex
                to_write[TAG_XMP_XMPMM_INSTANCE_ID] = instance
            if not document:
                document = uuid.uuid4().hex
                to_write[TAG_XMP_XMPMM_DOCUMENT_ID] = document
            if not creator:
                creator = "test-organizer"
                to_write[TAG_XMP_XMP_CREATOR_TOOL] = creator
            
            if to_write:
                ex.write(file_path, to_write)
            
            # Append history entries via Tagger
            created_when = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
            tagger = Tagger(file_path, exifer=ex)
            tagger.begin()
            tagger.write(HistoryTag(
                action=XMP_ACTION_CREATED,
                when=created_when,
                software_agent="test-organizer",
                instance_id=instance,
            ))
            tagger.write(HistoryTag(
                action=XMP_ACTION_EDITED,
                when=datetime.now(timezone.utc),
                software_agent="test-organizer",
                changed="metadata",
                instance_id=instance,
            ))
            tagger.end()
            
            # Read back tags including history
            read_back = ex.read(file_path, [TAG_XMP_XMPMM_INSTANCE_ID, TAG_XMP_XMPMM_DOCUMENT_ID, TAG_XMP_XMP_CREATOR_TOOL, TAG_XMP_XMPMM_HISTORY])

            # Verify identifiers and CreatorTool
            assert instance is not None
            assert document is not None
            assert self._norm(read_back.get(TAG_XMP_XMPMM_INSTANCE_ID, '')) == instance, f"{scenario['name']}: InstanceID not written correctly"
            assert self._norm(read_back.get(TAG_XMP_XMPMM_DOCUMENT_ID, '')) == document, f"{scenario['name']}: DocumentID not written correctly"
            assert read_back.get(TAG_XMP_XMP_CREATOR_TOOL) == creator, f"{scenario['name']}: CreatorTool not written correctly"
            
            # Verify history if present
            history_raw = read_back.get(TAG_XMP_XMPMM_HISTORY)
            if history_raw:
                history_text = str(history_raw).lower()
                assert XMP_ACTION_CREATED in history_text, f"{scenario['name']}: Missing 'created' action in history"
                assert XMP_ACTION_EDITED in history_text, f"{scenario['name']}: Missing 'edited' action in history"
                assert instance is not None
                assert instance in history_text, f"{scenario['name']}: Missing instance ID in history"
            
            # Process with FileOrganizer
            organizer = FileOrganizer(logger)
            config: dict[str, Any] = {
                "metadata": {
                    "languages": {
                        "en-US": {
                            "default": True,
                            "creator": "Test User",
                            "rights": "Public Domain",
                        }
                    }
                }
            }
            
            config_path = input_dir / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            
            processed_count = organizer(
                input_path=input_dir,
                output_path=output_dir,
                config_path=config_path,
                recursive=False,
                copy_mode=False,
            )
            
            assert processed_count["succeeded"] == 1, f"{scenario['name']}: FileOrganizer failed to process file"
            
            # Verify file moved into output/YYYY/... tree
            found_files = list(output_dir.rglob(filename))
            assert len(found_files) == 1, f"{scenario['name']}: File not found in output folder"
            processed_path = found_files[0]
            
            # Level 1 folder should match expected year
            l1_folder = processed_path.parent.parent.parent.name
            assert l1_folder == scenario["folder_l1"], f"{scenario['name']}: Expected folder {scenario['folder_l1']}, got {l1_folder}"
            
            # Cleanup for next scenario
            assert self.temp_dir is not None
            _rmtree_force(self.temp_dir)
            self.temp_dir = None


class TestFileOrganizerCustomFormats:
    """
    Test FileOrganizer with custom path and filename formats.
    """
    
    def setup_method(self) -> None:
        """
        Setup for each test method.
        """
        self.temp_dir: Path | None = None

    def teardown_method(self) -> None:
        """
        Cleanup after each test method.
        """
        ProjectConfig.instance(data=DEFAULT_CONFIG)
        if self.temp_dir and self.temp_dir.exists():
            _rmtree_force(self.temp_dir)
    
    def create_temp_dir(self) -> tuple[Path, Path]:
        """
        Create a temporary root with sibling input/ and output/ subdirs.
        """
        root = Path(tempfile.mkdtemp())
        self.temp_dir = root
        input_dir = root / "input"
        input_dir.mkdir()
        output_dir = root / "output"
        return input_dir, output_dir
    
    def _write_config(self, dir_path: Path, config: dict[str, Any] | None) -> Path | None:
        """
        Helper: write config dict to dir_path/config.json and return its path.
        """
        if config is None:
            return None
        cfg_path = dir_path / "config.json"
        cfg_path.write_text(json.dumps(config), encoding="utf-8")
        return cfg_path

    def _minimal_config(self) -> dict[str, Any]:
        """
        Minimal configuration for testing.
        """
        return {
            "metadata": {
                "languages": {
                    "en-US": {
                        "default": True,
                        "creator": "Test User",
                        "credit": "Test Archive",
                        "rights": "Test Rights",
                        "terms": "Test Terms",
                        "source": "Test Source",
                        "description": "Test description",
                    }
                }
            }
        }
    
    def test_process_with_flat_path_structure(self, logger: Logger) -> None:
        """
        Test file organization with flat path structure (no year folder).
        """
        input_dir, output_dir = self.create_temp_dir()
        
        filename = "2024.03.15.14.30.00.E.TEST.GRP.0001.A.RAW.tif"
        file_path = input_dir / filename
        create_test_image(file_path)
        
        # Re-initialize ProjectConfig with custom formats for this test
        ProjectConfig.instance(data={
            **DEFAULT_CONFIG,
            "formats": {
                "archive_path_template": "{year:04d}.{month:02d}.{day:02d}",
                "archive_filename_template": "{year:04d}.{month:02d}.{day:02d}.{hour:02d}.{minute:02d}.{second:02d}.{modifier}.{group}.{subgroup}.{sequence:04d}.{side}.{suffix}",
            },
        })
        organizer = FileOrganizer(logger)
        
        config_path = self._write_config(input_dir, self._minimal_config())
        
        # Run batch
        processed_count = organizer(
             input_path=input_dir,
             output_path=output_dir,
             config_path=config_path,
             recursive=False,
             copy_mode=False
        )
        assert processed_count["succeeded"] == 1
        
        # File should be in flat structure: output/2024.03.15/SOURCES/
        expected_path = output_dir / "2024.03.15" / "SOURCES" / filename
        assert expected_path.exists(), f"File not found at {expected_path}"
    
    def test_process_with_month_grouping(self, logger: Logger) -> None:
        """
        Test file organization grouped by year and month.
        """
        input_dir, output_dir = self.create_temp_dir()
        
        filename = "2024.03.15.14.30.00.E.TEST.GRP.0001.A.MSR.tif"
        file_path = input_dir / filename
        create_test_image(file_path)
        
        ProjectConfig.instance(data={
            **DEFAULT_CONFIG,
            "formats": {
                "archive_path_template": "{year:04d}/{year:04d}.{month:02d}",
                "archive_filename_template": "{year:04d}.{month:02d}.{day:02d}.{hour:02d}.{minute:02d}.{second:02d}.{modifier}.{group}.{subgroup}.{sequence:04d}.{side}.{suffix}",
            },
        })
        organizer = FileOrganizer(logger)
        
        config_path = self._write_config(input_dir, self._minimal_config())
        processed_count = organizer(
             input_path=input_dir,
             output_path=output_dir,
             config_path=config_path,
             recursive=False,
             copy_mode=False
        )
        assert processed_count["succeeded"] == 1
        
        # File should be in: output/2024/2024.03/SOURCES/
        expected_path = output_dir / "2024" / "2024.03" / "SOURCES" / filename
        assert expected_path.exists(), f"File not found at {expected_path}"
    
    def test_process_with_group_in_path(self, logger: Logger) -> None:
        """
        Test file organization with group component in path.
        """
        input_dir, output_dir = self.create_temp_dir()
        
        filename = "2024.03.15.14.30.00.E.FAM.POR.0001.A.RAW.tif"
        file_path = input_dir / filename
        create_test_image(file_path)
        
        ProjectConfig.instance(data={
            **DEFAULT_CONFIG,
            "formats": {
                "archive_path_template": "{group}/{year:04d}/{year:04d}.{month:02d}.{day:02d}",
                "archive_filename_template": "{year:04d}.{month:02d}.{day:02d}.{hour:02d}.{minute:02d}.{second:02d}.{modifier}.{group}.{subgroup}.{sequence:04d}.{side}.{suffix}",
            },
        })
        organizer = FileOrganizer(logger)
        
        config_path = self._write_config(input_dir, self._minimal_config())
        processed_count = organizer(
             input_path=input_dir,
             output_path=output_dir,
             config_path=config_path,
             recursive=False,
             copy_mode=False
        )
        assert processed_count["succeeded"] == 1
        
        # File should be in: output/FAM/2024/2024.03.15/SOURCES/
        expected_path = output_dir / "FAM" / "2024" / "2024.03.15" / "SOURCES" / filename
        assert expected_path.exists(), f"File not found at {expected_path}"
    
    def test_process_with_compact_filename(self, logger: Logger) -> None:
        """
        Test file organization with compact filename format.
        """
        input_dir, output_dir = self.create_temp_dir()
        
        original_filename = "2024.03.15.14.30.00.E.TEST.GRP.0042.A.RAW.tif"
        file_path = input_dir / original_filename
        create_test_image(file_path)
        
        ProjectConfig.instance(data={
            **DEFAULT_CONFIG,
            "formats": {
                "archive_path_template": "{year:04d}/{year:04d}.{month:02d}.{day:02d}",
                "archive_filename_template": "{year:04d}{month:02d}{day:02d}_{hour:02d}{minute:02d}{second:02d}_{group}_{suffix}",
            },
        })
        organizer = FileOrganizer(logger)
        
        config_path = self._write_config(input_dir, self._minimal_config())
        processed_count = organizer(
             input_path=input_dir,
             output_path=output_dir,
             config_path=config_path,
             recursive=False,
             copy_mode=False
        )
        assert processed_count["succeeded"] == 1
        
        # File should have compact name: 20240315_143000_TEST_RAW.tif
        expected_filename = "20240315_143000_TEST_RAW.tif"
        expected_path = output_dir / "2024" / "2024.03.15" / "SOURCES" / expected_filename
        assert expected_path.exists(), f"File not found at {expected_path}"


class TestExiftoolCompliance:
    """
    Tests for FileOrganizer metadata compliance with exiftool.
    """

    def setup_method(self) -> None:
        """
        Setup for each test method.
        """
        self.temp_dir: Path | None = None

    def teardown_method(self) -> None:
        """
        Cleanup after each test method.
        """
        if self.temp_dir and self.temp_dir.exists():
            _rmtree_force(self.temp_dir)

    def create_temp_dir(self) -> tuple[Path, Path]:
        """
        Create a temporary root with sibling input/ and output/ subdirs.
        """
        root = Path(tempfile.mkdtemp())
        self.temp_dir = root
        input_dir = root / "input"
        input_dir.mkdir()
        output_dir = root / "output"
        return input_dir, output_dir

    def get_exiftool_json(self, file_path: Path) -> dict[str, Any]:
        """
        Helper to read metadata using exiftool.
        """
        cmd = ["exiftool", "-json", "-G", str(file_path)]
        # Force UTF-8 encoding to avoid Windows charmap errors
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8')
        return json.loads(result.stdout)[0]  # type: ignore[no-any-return]

    def _minimal_config(self) -> dict[str, Any]:
        """
        Return minimal organizer config with required metadata languages.
        """
        return {
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

    def _write_config(self, dir_path: Path, config: dict[str, Any] | None) -> Path | None:
        """Helper: write config dict to dir_path/config.json and return its path.

        If config is None, returns None so organizer uses its default config lookup.
        """
        if config is None:
            return None
        cfg_path = dir_path / "config.json"
        cfg_path.write_text(json.dumps(config), encoding="utf-8")
        return cfg_path

    def test_full_metadata_compliance(self, logger: Logger) -> None:
        """
        Verify that all required metadata fields are written and visible to exiftool.

        Metadata is read from file-organizer/config.json (the ``metadata`` section),
        not from ProjectConfig.
        """
        metadata_config: dict[str, Any] = {
            "tags": DEFAULT_METADATA["tags"],
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

        input_dir, output_dir = self.create_temp_dir()

        filename = "1950.06.15.12.30.45.E.FAM.POR.0001.A.MSR.tiff"
        file_path = input_dir / filename
        create_test_image(file_path)

        organizer = FileOrganizer(logger)

        # Metadata lives in file-organizer config, not in ProjectConfig
        config: dict[str, Any] = {"metadata": metadata_config}
        config_path = self._write_config(input_dir, config)
        
        try:
            processed_count = organizer(
                input_path=input_dir,
                output_path=output_dir,
                config_path=config_path,
                recursive=False,
                copy_mode=False,
            )
            assert processed_count["succeeded"] == 1

            # 1950 / 1950.06.15 / SOURCES
            processed_path = output_dir / "1950" / "1950.06.15" / "SOURCES" / filename
            assert processed_path.exists()

            meta = self.get_exiftool_json(processed_path)

            # 1. Check Identifiers
            assert "XMP:Identifier" in meta or "XMP-dc:Identifier" in meta

            # 2. Check DateTimeOriginal (ExifIFD)
            assert "ExifIFD:DateTimeOriginal" in meta or "EXIF:DateTimeOriginal" in meta
            dt_orig = meta.get("ExifIFD:DateTimeOriginal") or meta.get("EXIF:DateTimeOriginal")
            assert dt_orig == "1950:06:15 12:30:45"

            # 3. Check XMP DateCreated
            assert "XMP:DateCreated" in meta or "XMP-photoshop:DateCreated" in meta
            date_created = meta.get("XMP:DateCreated") or meta.get("XMP-photoshop:DateCreated")
            assert date_created is not None
            assert "1950:06:15 12:30:45" in date_created or "1950-06-15" in date_created

            # 4. Check Description
            desc = (
                meta.get("XMP:Description")
                or meta.get("XMP-dc:Description-en-US")
                or meta.get("XMP-dc:Description")
            )
            assert desc is not None
            assert "Test description for 1950-06-15 image" in str(desc)

            # 5. Check Configurable Fields (except Creator which doesn't support LangAlt)
            # Creator is defined in config but exiftool ignores language variants for it
            assert meta.get("XMP:Credit") == "The Archive" or meta.get("XMP-photoshop:Credit") == "The Archive"
            assert meta.get("XMP:Rights") == "Public Domain" or meta.get("XMP-dc:Rights") == "Public Domain"
            assert meta.get("XMP:UsageTerms") == "Free to use" or meta.get("XMP-xmpRights:UsageTerms") == "Free to use"  
            assert meta.get("XMP:Source") == "Box 42" or meta.get("XMP-dc:Source") == "Box 42"
            # Title is no longer written (it just duplicated the filename)
        finally:
            pass  # ProjectConfig is not modified in this test

    def test_partial_date_compliance(self, logger: Logger) -> None:
        """
        Verify partial date handling with exiftool.
        """
        input_dir, output_dir = self.create_temp_dir()

        filename = "1950.00.00.00.00.00.C.FAM.POR.0002.A.WEB.jpg"
        file_path = input_dir / filename
        create_test_image(file_path)

        organizer = FileOrganizer(logger)

        config_path = self._write_config(input_dir, self._minimal_config())
        processed_count = organizer(
            input_path=input_dir,
            output_path=output_dir,
            config_path=config_path,
            recursive=False,
            copy_mode=False,
        )
        assert processed_count["succeeded"] == 1

        # 1950 / 1950.00.00 / DERIVATIVES
        processed_path = output_dir / "1950" / "1950.00.00" / "DERIVATIVES" / filename
        
        meta = self.get_exiftool_json(processed_path)
        
        # 1. DateTimeOriginal should be ABSENT
        assert "ExifIFD:DateTimeOriginal" not in meta
        
        # 2. XMP DateCreated should be present (partial)
        found_date = False
        for key, value in meta.items():
            if "DateCreated" in key and "1950" in str(value):
                found_date = True
                break
        assert found_date, f"Could not find partial date 1950 in metadata: {meta}"

    def test_datetimedigitized_not_overwritten(self, logger: Logger) -> None:
        """
        Verify that existing DateTimeDigitized is not overwritten.
        """
        input_dir, output_dir = self.create_temp_dir()

        filename = "2025.11.29.14.00.00.C.001.001.0001.A.RAW.tiff"
        file_path = input_dir / filename
        create_test_image(file_path)

        # Set both
        subprocess.run([
            "exiftool",
            "-EXIF:CreateDate=2025:11:29 14:00:00",
            "-XMP-exif:DateTimeDigitized=2025:11:29 13:00:00",
            "-overwrite_original",
            str(file_path)
        ], check=True)

        # Process
        organizer = FileOrganizer(logger)
        config_path = self._write_config(input_dir, self._minimal_config())
        processed_count = organizer(
            input_path=input_dir,
            output_path=output_dir,
            config_path=config_path,
            recursive=False,
            copy_mode=False,
        )
        assert processed_count["succeeded"] == 1

        processed_path = output_dir / "2025" / "2025.11.29" / "SOURCES" / filename
        assert processed_path.exists()

        meta_after = self.get_exiftool_json(processed_path)

        dt_digitized = meta_after.get("XMP-exif:DateTimeDigitized") or meta_after.get("XMP:DateTimeDigitized")       
        assert dt_digitized == "2025:11:29 13:00:00"
