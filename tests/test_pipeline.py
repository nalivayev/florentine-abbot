import os
import shutil
import tempfile
import unittest
import logging
from pathlib import Path
from sqlalchemy import select

from file_organizer.processor import ArchiveProcessor
from archive_keeper.engine import DatabaseManager
from archive_keeper.scanner import ArchiveScanner
from archive_keeper.models import File, FileStatus
from common.exifer import Exifer
from common.logger import Logger

# Configure logging to capture output during tests
logging.basicConfig(level=logging.DEBUG)

class TestPipeline(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.root_path = Path(self.test_dir)
        
        # Create logger for tests
        self.logger = Logger("test")
        
        # Setup paths
        self.input_dir = self.root_path / "input"
        self.input_dir.mkdir()
        
        self.db_path = self.root_path / "archive.db"
        
        # Initialize DB once
        self.db_manager = DatabaseManager(str(self.db_path))
        self.db_manager.init_db()

    def tearDown(self):
        self.db_manager.engine.dispose()
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def _create_dummy_file(self, filename: str) -> Path:
        file_path = self.input_dir / filename
        # Minimal valid JPEG
        with open(file_path, "wb") as f:
            f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xbf')
        return file_path

    def _run_scenario(self, scenario):
        filename = scenario["filename"]
        file_path = self._create_dummy_file(filename)
        
        print(f"\n[Pipeline] Running scenario: {scenario['name']}")
        print(f"[Pipeline] Processing file: {file_path}")

        # --- Step 1: File Organizer ---
        processor = ArchiveProcessor(self.logger)
        config = {
            "creator": "Test User",
            "rights": "Public Domain"
        }
        
        success = processor.process(file_path, config)
        self.assertTrue(success, f"File Organizer failed to process file in scenario: {scenario['name']}")
        
        # Verify file moved
        processed_root = self.input_dir / "processed"
        # Expected path depends on folder structure logic
        # Level 1: YYYY
        # Level 2: YYYY.MM.DD
        # Level 3: role folder (SOURCES/DERIVATIVES) or date root for PRV preview files
        
        # We need to construct expected path based on filename parts
        # But scenario provides expected folder_l1, let's assume standard structure for others
        # Or we can just find the file in processed folder
        
        found_files = list(processed_root.rglob(filename))
        self.assertEqual(len(found_files), 1, f"File {filename} not found in processed folder")
        processed_path = found_files[0]
        
        # Verify Level 1 folder
        # processed_path is .../processed/L1/L2/L3/filename
        # So parent.parent.parent.name should be L1
        l1_folder = processed_path.parent.parent.parent.name
        self.assertEqual(l1_folder, scenario["folder_l1"], f"Incorrect Level 1 folder for {scenario['name']}")

        # Verify metadata
        tool = Exifer()
        all_tags = [
            "XMP-dc:Creator",
            "XMP-dc:Description",
            "XMP-xmp:CreateDate",
            "XMP-photoshop:DateCreated",
            "EXIF:DateTimeOriginal",
            "ExifIFD:DateTimeOriginal"
        ]
        metadata = tool.read(processed_path, all_tags)
        flat_meta = {k.split(':')[-1]: v for k, v in metadata.items()}
        
        # Creator is an array in XMP, ExifTool may return it as string representation of array
        creator = flat_meta.get("Creator")
        self.assertTrue(
            creator == "Test User" or creator == "['Test User']" or (creator and "Test User" in creator),
            f"Expected Creator to contain 'Test User', got: {creator}"
        )
        
        # Check Description
        if "expected_desc" in scenario:
            self.assertIn(scenario["expected_desc"], flat_meta.get("Description", ""))
            
        # Check XMP Date
        if "expected_xmp_date" in scenario:
            # Try both CreateDate and DateCreated
            date_created = str(flat_meta.get("DateCreated") or flat_meta.get("CreateDate") or "")
            # Normalize separators to colons for comparison, as ExifTool often returns colons
            date_created_norm = date_created.replace("-", ":")
            expected_norm = scenario["expected_xmp_date"].replace("-", ":")
            
            self.assertIn(expected_norm, date_created_norm)
            
        # Check Exif Date
        if scenario["has_exif_date"]:
            self.assertTrue(flat_meta.get("DateTimeOriginal"), "Exif:DateTimeOriginal should be present")
        else:
            self.assertFalse(flat_meta.get("DateTimeOriginal"), "Exif:DateTimeOriginal should be empty/missing")

        # --- Step 2: Archive Keeper ---
        
        # Run Scan
        scanner = ArchiveScanner(self.logger, str(self.input_dir), self.db_manager)
        scanner.scan()
        
        # Verify DB records
        session = self.db_manager.get_session()
        try:
            # Find the specific file in DB
            # Path in DB is relative to input_dir
            expected_rel_path = processed_path.relative_to(self.input_dir)
            
            # We need to query by path because there might be multiple files from multiple scenarios
            # But wait, ArchiveScanner scans everything.
            # We can just check if THIS file is in DB.
            
            # Note: ArchiveScanner stores paths as strings.
            # On Windows, path separator might be issue if not normalized.
            # Let's fetch all and find ours.
            
            files = session.scalars(select(File)).all()
            found_in_db = False
            for db_file in files:
                if Path(db_file.path) == expected_rel_path:
                    found_in_db = True
                    self.assertTrue(db_file.hash, "File hash should be calculated")
                    self.assertEqual(db_file.status, FileStatus.OK)
                    break
            
            self.assertTrue(found_in_db, f"File {expected_rel_path} not found in DB")
            
        finally:
            session.close()

    def test_scenarios(self):
        """
        Run multiple pipeline scenarios to verify handling of different date modifiers.
        
        Scenarios covered:
        1. Exact Date (E): Full date/time, Exif present.
        2. Circa Year (C): Year only, no Exif date, partial XMP date.
        3. Before Year-Month (B): Year-Month, no Exif date, partial XMP date.
        4. After Year-Month-Day (F): Year-Month-Day, no Exif date, partial XMP date.
        5. Absent Date (A): No date, no Exif date, no XMP date.
        """
        # Check if exiftool is available
        try:
            Exifer()._run(["-ver"])
        except (FileNotFoundError, RuntimeError):
            self.skipTest("ExifTool not found, skipping E2E test")

        scenarios = [
            {
                "name": "Exact Date",
                "filename": "2023.10.27.12.00.00.E.Group.Sub.0001.A.Orig.jpg",
                "expected_desc": "Exact date: 2023-10-27",
                "expected_xmp_date": "2023-10-27",
                "has_exif_date": True,
                "folder_l1": "2023"
            },
            {
                "name": "Circa Year",
                "filename": "1950.00.00.00.00.00.C.Group.Sub.0002.A.Orig.jpg",
                "expected_desc": "Circa 1950",
                "expected_xmp_date": "1950",
                "has_exif_date": False,
                "folder_l1": "1950"
            },
            {
                "name": "Before Year-Month",
                "filename": "1960.01.00.00.00.00.B.Group.Sub.0003.A.Orig.jpg",
                "expected_desc": "Before 1960",
                "expected_xmp_date": "1960-01",
                "has_exif_date": False,
                "folder_l1": "1960"
            },
             {
                "name": "After Year-Month-Day",
                "filename": "1970.05.20.00.00.00.F.Group.Sub.0004.A.Orig.jpg",
                "expected_desc": "After 1970",
                "expected_xmp_date": "1970-05-20",
                "has_exif_date": False,
                "folder_l1": "1970"
            },
            {
                "name": "Absent Date",
                "filename": "0000.00.00.00.00.00.A.Group.Sub.0005.A.Orig.jpg",
                "expected_desc": "Date unknown",
                "has_exif_date": False,
                "folder_l1": "0000"
            }
        ]
        
        for case in scenarios:
            with self.subTest(case=case["name"]):
                self._run_scenario(case)

if __name__ == '__main__':
    unittest.main()


