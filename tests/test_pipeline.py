from pathlib import Path
import json
from textwrap import dedent

import pytest
from PIL import Image
from file_organizer.organizer import FileOrganizer
from preview_maker import PreviewMaker
from common.exifer import Exifer
from common.logger import Logger
from common.constants import TAG_XMP_XMPMM_INSTANCE_ID, TAG_XMP_XMPMM_DOCUMENT_ID, TAG_XMP_XMP_CREATOR_TOOL, TAG_XMP_XMPMM_HISTORY, XMP_ACTION_CREATED, XMP_ACTION_EDITED
from common.historian import XMPHistorian
from common.metadata import TAG_EXIFIFD_DATETIME_DIGITIZED, TAG_EXIFIFD_CREATE_DATE, TAG_IFD0_SOFTWARE, TAG_IFD0_MAKE, TAG_IFD0_MODEL, TAG_XMP_DC_IDENTIFIER, TAG_XMP_XMP_IDENTIFIER, TAG_XMP_DC_RELATION
from tests.scan_batcher.fake_workflow import FakeVuescanWorkflow
from datetime import datetime, timezone
import uuid


class TestPipeline:
    """End-to-end pipeline test: scan-batcher → file-organizer → preview-maker.
    
    This test class focuses on full integration testing of the complete
    archival workflow. Component-specific tests (e.g., different date modifiers,
    metadata handling) are covered in dedicated test files under tests/file_organizer,
    tests/preview_maker, etc.
    """

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        # Temporary root and input directory
        self.root_path = tmp_path

        self.logger = Logger("test")

        self.input_dir = self.root_path / "input"
        self.input_dir.mkdir()

        yield

    def _create_realistic_scan(self, file_path: Path, datetime_digitized: str = "2024:01:15 14:30:00", software: str = "VueScan 9.12.45", large_file: bool = False) -> Path:
        """Create a realistic fake scanned TIFF file with proper EXIF tags.
        
        Args:
            file_path: Where to create the file.
            datetime_digitized: EXIF datetime in format "YYYY:MM:DD HH:MM:SS".
            software: Software tag value (simulates scanner software).
            large_file: If True, create a ~2GB file to test large file handling.
            
        Returns:
            Path to created file.
        """
        # Create a realistic scan-like image (grayscale, larger size)
        if large_file:
            # Create a huge image (~2GB uncompressed TIFF)
            # RGB mode: 25000 x 27000 pixels x 3 bytes = ~2.02GB
            self.logger.info(f"Creating large test file (~2GB): {file_path.name}")
            img = Image.new("RGB", (25000, 27000), color=(240, 240, 240))
            img.save(file_path, format="TIFF", compression=None)  # No compression for large size
            file_size_mb = file_path.stat().st_size / (1024 ** 2)
            self.logger.info(f"Large file created: {file_size_mb:.1f} MB")
        else:
            img = Image.new("L", (2400, 3200), color=240)  # Gray background like scanned paper
            img.save(file_path, format="TIFF", compression="lzw")
        
        # Write realistic EXIF tags that VueScan would write
        try:
            ex = Exifer()
            ex.write(file_path, {
                TAG_EXIFIFD_DATETIME_DIGITIZED: datetime_digitized,
                TAG_EXIFIFD_CREATE_DATE: datetime_digitized,
                TAG_IFD0_SOFTWARE: software,
                TAG_IFD0_MAKE: "Epson",
                TAG_IFD0_MODEL: "Perfection V600",
            })
        except (FileNotFoundError, RuntimeError):
            # If exiftool not available, just skip EXIF writing
            pass
        
        return file_path

    def test_full_pipeline_scan_to_preview(self, tmp_path) -> None:
        """Complete end-to-end test: scan-batcher → file-organizer → preview-maker.
        
        This test simulates the entire workflow:
        1. Fake scanning with scan-batcher (VuescanWorkflow)
        2. Organizing scanned file with file-organizer
        3. Generating preview with preview-maker
        """
        # Skip if exiftool not available
        try:
            Exifer()._run(["-ver"])
        except (FileNotFoundError, RuntimeError):
            pytest.skip("ExifTool not found, skipping full pipeline test")
        
        logger = Logger("test-pipeline")
        
        # === Step 0: Prepare fake scan file and workflow config ===
        fixtures_dir = tmp_path / "fixtures"
        fixtures_dir.mkdir()
        
        fake_scan_file = fixtures_dir / "temp_scan.tif"
        self._create_realistic_scan(
            fake_scan_file,
            datetime_digitized="2024:01:15 14:30:00",
            software="VueScan 9.12.45",
            large_file=False  # Disable large file creation for normal tests
        )
        
        # Create minimal workflow configuration
        workflow_dir = tmp_path / "workflow"
        workflow_dir.mkdir()
        
        vuescan_output_dir = tmp_path / "vuescan_output"
        vuescan_output_dir.mkdir()
        
        final_output_dir = tmp_path / "scanned"
        final_output_dir.mkdir()
        
        # Create workflow.ini
        workflow_ini = workflow_dir / "workflow.ini"
        workflow_ini.write_text(dedent(f"""\
            [main]
            description = Test scan workflow
            output_path = {final_output_dir}
            output_file_name = 2024.01.15.14.30.00.E.FAM.ALB.0001.A.MSR

            [vuescan]
            output_path = {vuescan_output_dir}
            output_file_name = temp_scan
            output_extension_name = tif
            """), encoding="utf-8")
        
        # Create minimal vuescan.ini (required by workflow)
        vuescan_ini_dir = Path(__file__).parent.parent / "src" / "scan_batcher" / "workflows" / "vuescan"
        vuescan_ini_path = vuescan_ini_dir / "vuescan.ini"
        
        # Backup original vuescan.ini if it exists
        vuescan_ini_backup = None
        if vuescan_ini_path.exists():
            vuescan_ini_backup = vuescan_ini_path.read_text(encoding="utf-8")
        
        # Create test vuescan.ini with paths in tmp_path
        vuescan_settings_dir = tmp_path / "vuescan_settings"
        vuescan_settings_dir.mkdir()
        
        vuescan_ini_path.write_text(dedent(f"""\
            [main]
            settings_path = {vuescan_settings_dir}
            settings_name = vuescan_settings.ini
            program_path = {tmp_path}
            program_name = vuescan_fake.exe
            logging_path = {tmp_path}
            logging_name = scan.log
            """), encoding="utf-8")
        
        # === Step 1: Run scan-batcher with FakeVuescanWorkflow ===
        workflow = FakeVuescanWorkflow(logger, fake_scan_file)
        
        try:
            workflow(str(workflow_dir), templates={})
        except FileNotFoundError as e:
            # Expected if vuescan.ini is missing - skip test
            pytest.skip(f"Workflow configuration incomplete: {e}")
        finally:
            # Restore original vuescan.ini
            if vuescan_ini_backup:
                vuescan_ini_path.write_text(vuescan_ini_backup, encoding="utf-8")
        
        # Verify scan-batcher output
        expected_scan_output = final_output_dir / "2024.01.15.14.30.00.E.FAM.ALB.0001.A.MSR.tif"
        assert expected_scan_output.exists(), f"Scan-batcher output not found: {expected_scan_output}"
        
        # Verify XMP History was written by scan-batcher
        ex = Exifer()
        historian = XMPHistorian(exifer=ex)
        history = historian.read_history(expected_scan_output)
        
        assert len(history) >= 2, "Expected at least 2 history entries from scan-batcher"
        
        # Check for 'created' and 'edited' actions
        actions = [entry.get('action') for entry in history]
        assert XMP_ACTION_CREATED in actions, "Expected 'created' action in history"
        assert XMP_ACTION_EDITED in actions, "Expected 'edited' action in history"
        
        # Verify DocumentID and InstanceID were set
        ids = ex.read(expected_scan_output, [
            TAG_XMP_XMPMM_DOCUMENT_ID, 
            TAG_XMP_XMPMM_INSTANCE_ID, 
            TAG_XMP_DC_IDENTIFIER, 
            TAG_XMP_XMP_IDENTIFIER
        ])
        assert ids.get(TAG_XMP_XMPMM_DOCUMENT_ID), "DocumentID should be set"
        assert ids.get(TAG_XMP_XMPMM_INSTANCE_ID), "InstanceID should be set"
        
        logger.info(f"✓ scan-batcher completed: {expected_scan_output.name}")
        
        # === Step 2: Run file-organizer ===
        organizer = FileOrganizer(logger)
        config = {
            "metadata": {
                "languages": {
                    "en-US": {
                        "default": True,
                        "creator": "Test User",
                        "description": "Test scan from pipeline",
                        "rights": "Public Domain",
                    }
                }
            }
        }
        
        config_path = final_output_dir / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        
        processed_count = organizer(
            input_path=final_output_dir,
            config_path=config_path,
            recursive=False,
            copy_mode=False,
        )
        
        assert processed_count == 1, "file-organizer should process 1 file"
        
        # Verify file was moved to processed/YYYY/YYYY.MM.DD/SOURCES/
        processed_root = final_output_dir / "processed"
        expected_organized = processed_root / "2024" / "2024.01.15" / "SOURCES" / "2024.01.15.14.30.00.E.FAM.ALB.0001.A.MSR.tif"
        assert expected_organized.exists(), f"Organized file not found: {expected_organized}"
        
        # Re-read master file identifiers for later comparison with PRV
        master_ids = ex.read(expected_organized, [
            TAG_XMP_DC_IDENTIFIER, 
            TAG_XMP_XMP_IDENTIFIER
        ])
        master_identifier = master_ids.get(TAG_XMP_DC_IDENTIFIER) or master_ids.get(TAG_XMP_XMP_IDENTIFIER)
        assert master_identifier, "Master should have dc:Identifier after organizer processing"
        
        logger.info(f"✓ file-organizer completed: {expected_organized}")
        
        # === Step 3: Run preview-maker ===
        maker = PreviewMaker(logger)
        prv_count = maker(path=processed_root, overwrite=False, max_size=800, quality=75)
        
        assert prv_count == 1, "preview-maker should generate 1 PRV file"
        
        # Verify PRV was created in date root folder
        expected_prv = processed_root / "2024" / "2024.01.15" / "2024.01.15.14.30.00.E.FAM.ALB.0001.A.PRV.jpg"
        assert expected_prv.exists(), f"PRV file not found: {expected_prv}"
        
        # Verify PRV has proper metadata
        # PRV should NOT have DocumentID/InstanceID - those are for provenance tracking
        # PRV is a derivative, not part of the master's XMP History chain
        # It should only have dc:Relation linking back to master's dc:Identifier
        prv_tags = ex.read(expected_prv, [
            TAG_XMP_DC_IDENTIFIER, 
            TAG_XMP_XMP_IDENTIFIER, 
            TAG_XMP_DC_RELATION
        ])
        assert prv_tags.get(TAG_XMP_DC_IDENTIFIER), "PRV should have its own dc:Identifier"
        assert prv_tags.get(TAG_XMP_DC_RELATION), "PRV should link back to master via dc:Relation"
        
        # Verify the relation points to master's identifier
        assert prv_tags[TAG_XMP_DC_RELATION] == master_identifier, "PRV's dc:Relation should point to master's identifier"
        
        logger.info(f"✓ preview-maker completed: {expected_prv.name}")
        
        print(f"\n{'='*60}")
        print("✅ FULL PIPELINE TEST PASSED")
        print(f"{'='*60}")
        print(f"1. scan-batcher   → {expected_scan_output.name}")
        print(f"2. file-organizer → {expected_organized.relative_to(processed_root)}")
        print(f"3. preview-maker  → {expected_prv.relative_to(processed_root)}")
        print(f"{'='*60}\n")
