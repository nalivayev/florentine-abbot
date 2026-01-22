import logging
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy import select

from file_organizer.organizer import FileOrganizer
from archive_keeper.engine import DatabaseManager
from archive_keeper.scanner import ArchiveScanner
from archive_keeper.models import File, FileStatus
from preview_maker import PreviewMaker
from common.exifer import Exifer
from common.logger import Logger


# Configure logging to capture output during tests
logging.basicConfig(level=logging.DEBUG)


class TestPipeline:
    """End-to-end filesystem/DB pipeline tests.

    These tests are intentionally higher-level and slower. Detailed
    metadata field coverage is handled in dedicated tests under
    tests/file_organizer, so here we focus on:

    - FileOrganizer moving files into the expected processed/ layout
    - PreviewMaker generating PRV files from MSR sources
    - ArchiveScanner/DatabaseManager seeing processed files in the DB
    """

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        # Temporary root and input directory
        self.root_path = tmp_path

        self.logger = Logger("test")

        self.input_dir = self.root_path / "input"
        self.input_dir.mkdir()

        # ArchiveKeeper DB
        self.db_path = self.root_path / "archive.db"
        self.db_manager = DatabaseManager(str(self.db_path))
        self.db_manager.init_db()
        
        yield
        
        self.db_manager.engine.dispose()

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

        # --- Step 1: File Organizer ---
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

        success = organizer.process(file_path, config)
        assert success, f"File Organizer failed to process file in scenario: {scenario['name']}"

        # Verify file moved into processed/YYYY/... tree
        processed_root = self.input_dir / "processed"
        found_files = list(processed_root.rglob(filename))
        assert len(found_files) == 1, f"File {filename} not found in processed folder"
        processed_path = found_files[0]

        # Level 1 folder should match provided expectation
        l1_folder = processed_path.parent.parent.parent.name
        assert l1_folder == scenario["folder_l1"], f"Incorrect Level 1 folder for {scenario['name']}"

        # --- Step 2: Archive Keeper ---

        scanner = ArchiveScanner(self.logger, str(self.input_dir), self.db_manager)
        scanner.scan()

        session = self.db_manager.get_session()
        try:
            expected_rel_path = processed_path.relative_to(self.input_dir)

            files = session.scalars(select(File)).all()
            found_in_db = False
            for db_file in files:
                if Path(db_file.path) == expected_rel_path:
                    found_in_db = True
                    assert db_file.hash, "File hash should be calculated"
                    assert db_file.status == FileStatus.OK
                    break

            assert found_in_db, f"File {expected_rel_path} not found in DB"
        finally:
            session.close()

    def test_pipeline_with_preview_maker(self) -> None:
        """Filesystem E2E: FileOrganizer + PreviewMaker on an MSR source."""

        # Ensure exiftool is available (required by FileOrganizer)
        try:
            Exifer()._run(["-ver"])
        except (FileNotFoundError, RuntimeError):
            pytest.skip("ExifTool not found, skipping E2E test with PreviewMaker")

        filename = "2023.10.27.12.00.00.E.Group.Sub.0001.A.MSR.tiff"
        file_path = self._create_dummy_tiff(filename)

        # Step 1: organize MSR into processed/YYYY/YYYY.MM.DD/SOURCES
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

        success = organizer.process(file_path, config)
        assert success, "File Organizer failed to process MSR file in PreviewMaker pipeline test"

        processed_root = self.input_dir / "processed"
        found_files = list(processed_root.rglob(filename))
        assert len(found_files) == 1, f"MSR file {filename} not found in processed folder"
        processed_msr_path = found_files[0]

        assert processed_msr_path.parent.name == "SOURCES"
        assert processed_msr_path.parent.parent.name == "2023.10.27"
        assert processed_msr_path.parent.parent.parent.name == "2023"

        # Step 2: generate PRV via PreviewMaker
        maker = PreviewMaker(self.logger)
        count = maker(path=self.input_dir, overwrite=False, max_size=1000, quality=70)
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
