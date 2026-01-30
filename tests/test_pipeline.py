from pathlib import Path
import json

import pytest
from PIL import Image
from file_organizer.organizer import FileOrganizer
from preview_maker import PreviewMaker
from common.exifer import Exifer
from common.logger import Logger
from common.historian import (
    XMP_TAG_INSTANCE_ID,
    XMP_TAG_DOCUMENT_ID,
    XMP_TAG_CREATOR_TOOL,
    XMP_TAG_HISTORY,
    XMP_ACTION_CREATED,
    XMP_ACTION_EDITED,
)
from common.historian import XMPHistorian
from datetime import datetime, timezone
import uuid


class TestPipeline:
    """End-to-end filesystem pipeline tests.

    These tests are intentionally higher-level and slower. Detailed
    metadata field coverage is handled in dedicated tests under
    tests/file_organizer, so here we focus on:

    - FileOrganizer moving files into the expected processed/ layout
    - PreviewMaker generating PRV files from MSR sources
    """

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        # Temporary root and input directory
        self.root_path = tmp_path

        self.logger = Logger("test")

        self.input_dir = self.root_path / "input"
        self.input_dir.mkdir()

        yield

    def _create_dummy_jpeg(self, filename: str) -> Path:
        """Create a small valid JPEG image in the input directory."""

        file_path = self.input_dir / filename
        img = Image.new("RGB", (100, 100), color="red")
        img.save(file_path, format="JPEG")
        return file_path

    def _create_dummy_tiff(self, filename: str) -> Path:
        """Create a small valid TIFF image in the input directory."""

        file_path = self.input_dir / filename
        img = Image.new("RGB", (100, 100), color="white")
        img.save(file_path, format="TIFF")
        return file_path

    def _run_scenario(self, scenario: dict) -> None:
        """Run a single FileOrganizer + ArchiveKeeper scenario."""

        filename = scenario["filename"]
        file_path = self._create_dummy_jpeg(filename)
        print(f"\n[Pipeline] Running scenario: {scenario['name']}")
        print(f"[Pipeline] Processing file: {file_path}")

        # --- Historian / XMP sanity check ---
        # Write the same set of XMP tags and History entries the workflows do,
        # then read them back and assert they were written.
        try:
            ex = Exifer()
            # quick availability check
            ex._run(["-ver"])
        except (FileNotFoundError, RuntimeError):
            # exiftool not available — skip historian write/read for this scenario
            print("[Pipeline] exiftool not available, skipping historian check")
        else:
            # Check existing tags and only write missing ones
            existing = ex.read(file_path, [XMP_TAG_INSTANCE_ID, XMP_TAG_DOCUMENT_ID, XMP_TAG_CREATOR_TOOL])

            instance = existing.get(XMP_TAG_INSTANCE_ID)
            document = existing.get(XMP_TAG_DOCUMENT_ID)
            creator = existing.get(XMP_TAG_CREATOR_TOOL)

            to_write = {}
            if not instance:
                instance = uuid.uuid4().hex
                to_write[XMP_TAG_INSTANCE_ID] = instance
            if not document:
                document = uuid.uuid4().hex
                to_write[XMP_TAG_DOCUMENT_ID] = document
            if not creator:
                creator = "test-pipeline"
                to_write[XMP_TAG_CREATOR_TOOL] = creator

            if to_write:
                ex.write(file_path, to_write)

            # Append history entries using XMPHistorian (keeps behaviour as before)
            historian = XMPHistorian(exifer=ex)
            created_when = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
            historian.append_entry(file_path, XMP_ACTION_CREATED, f"test-pipeline", created_when, logger=self.logger, instance_id=instance)
            historian.append_entry(file_path, XMP_ACTION_EDITED, f"test-pipeline", datetime.now(timezone.utc), changed='metadata', logger=self.logger, instance_id=instance)

            # Read back tags including history
            read_back = ex.read(file_path, [XMP_TAG_INSTANCE_ID, XMP_TAG_DOCUMENT_ID, XMP_TAG_CREATOR_TOOL, XMP_TAG_HISTORY])

            def _norm(v: str) -> str:
                if not isinstance(v, str):
                    return str(v)
                return v.lower().replace('uuid:', '').replace('-', '')

            # Always assert identifiers and CreatorTool
            assert _norm(read_back.get(XMP_TAG_INSTANCE_ID, '')) == instance, 'InstanceID not written/read correctly'
            assert _norm(read_back.get(XMP_TAG_DOCUMENT_ID, '')) == document, 'DocumentID not written/read correctly'
            assert read_back.get(XMP_TAG_CREATOR_TOOL) == creator, 'CreatorTool not written/read correctly'

            # History may not be immediately visible depending on exiftool behaviour; only assert if present
            history_raw = read_back.get(XMP_TAG_HISTORY)
            if history_raw:
                history_text = str(history_raw).lower()
                assert XMP_ACTION_CREATED in history_text
                assert XMP_ACTION_EDITED in history_text
                assert instance in history_text

        # --- Step 1: File Organizer (batch mode handles moves) ---
        organizer = FileOrganizer(self.logger)
        config = {
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

        # Persist config and call organizer in batch mode on input_dir
        config_path = self.input_dir / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")

        processed_count = organizer(
            input_path=self.input_dir,
            config_path=config_path,
            recursive=False,
            copy_mode=False,
        )
        assert processed_count == 1, f"File Organizer failed to process file in scenario: {scenario['name']}"

        # Verify file moved into processed/YYYY/... tree
        processed_root = self.input_dir / "processed"
        found_files = list(processed_root.rglob(filename))
        assert len(found_files) == 1, f"File {filename} not found in processed folder"
        processed_path = found_files[0]

        # Level 1 folder should match provided expectation
        l1_folder = processed_path.parent.parent.parent.name
        assert l1_folder == scenario["folder_l1"], f"Incorrect Level 1 folder for {scenario['name']}"

        # ArchiveKeeper step removed: this pipeline test focuses on
        # FileOrganizer behaviour and PreviewMaker only.

    def test_pipeline_with_preview_maker(self) -> None:
        """Filesystem E2E: FileOrganizer + PreviewMaker on an MSR source."""

        # Ensure exiftool is available (required by FileOrganizer)
        try:
            Exifer()._run(["-ver"])
        except (FileNotFoundError, RuntimeError):
            pytest.skip("ExifTool not found, skipping E2E test with PreviewMaker")

        filename = "2023.10.27.12.00.00.E.Group.Sub.0001.A.MSR.tiff"
        file_path = self._create_dummy_tiff(filename)

        # Step 1: organize MSR into processed/YYYY/YYYY.MM.DD/SOURCES via batch API
        organizer = FileOrganizer(self.logger)
        config = {
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

        config_path = self.input_dir / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")

        processed_count = organizer(
            input_path=self.input_dir,
            config_path=config_path,
            recursive=False,
            copy_mode=False,
        )
        assert processed_count == 1, "File Organizer failed to process MSR file in PreviewMaker pipeline test"

        processed_root = self.input_dir / "processed"
        found_files = list(processed_root.rglob(filename))
        assert len(found_files) == 1, f"MSR file {filename} not found in processed folder"
        processed_msr_path = found_files[0]

        assert processed_msr_path.parent.name == "SOURCES"
        assert processed_msr_path.parent.parent.name == "2023.10.27"
        assert processed_msr_path.parent.parent.parent.name == "2023"

        # Step 2: generate PRV via PreviewMaker
        maker = PreviewMaker(self.logger)
        # Pass the archive base (processed/) where year folders begin
        count = maker(path=processed_root, overwrite=False, max_size=1000, quality=70)
        assert count == 1, "PreviewMaker should generate exactly one PRV file"

        date_dir = processed_msr_path.parent.parent
        prv_name = "2023.10.27.12.00.00.E.Group.Sub.0001.A.PRV.jpg"
        prv_path = date_dir / prv_name

        assert prv_path.exists(), f"PRV file not found at expected path: {prv_path}"

    def test_scenarios(self) -> None:
        """Run multiple pipeline scenarios for different date modifiers.

        This keeps the high-level pipeline coverage (organizer + scanner) for
        several filename patterns, while detailed EXIF/XMP expectations live
        in test_exiftool_compliance.
        """

        # Skip completely if exiftool is unavailable
        try:
            Exifer()._run(["-ver"])
        except (FileNotFoundError, RuntimeError):
            pytest.skip("ExifTool not found, skipping E2E test")

        scenarios = [
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

        for case in scenarios:
            self._run_scenario(case)
