import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from preview_maker import PreviewMaker
from file_organizer.organizer import FileOrganizer
from common.logger import Logger


class TestPreviewMakerBatch:
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = None

    def teardown_method(self):
        """Cleanup after each test method."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_temp_dir(self) -> Path:
        """Create a temporary directory."""
        temp_dir = tempfile.mkdtemp()
        self.temp_dir = Path(temp_dir)
        return self.temp_dir

    def _create_tiff(self, path: Path, size=(4000, 3000)) -> None:
        img = Image.new("RGB", size, color="white")
        img.save(path, format="TIFF")

    def _get_exiftool_json(self, file_path: Path) -> dict:
        cmd = ["exiftool", "-json", "-G", str(file_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)[0]

    def test_generate_prv_from_msr_prefers_msr_over_raw(self):
        temp_dir = self.create_temp_dir()
        
        # Simulate small archive fragment
        date_dir = temp_dir / "PHOTO_ARCHIVES" / "0001.Family" / "1950" / "1950.06.15"
        sources_dir = date_dir / "SOURCES"
        sources_dir.mkdir(parents=True, exist_ok=True)

        raw_name = "1950.06.15.12.00.00.E.FAM.POR.0001.A.RAW.tiff"
        msr_name = "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff"

        raw_path = sources_dir / raw_name
        msr_path = sources_dir / msr_name

        self._create_tiff(raw_path)
        self._create_tiff(msr_path)

        maker = PreviewMaker(Logger("test_preview_maker"))
        count = maker(path=temp_dir, overwrite=False, max_size=1000, quality=70)
        assert count == 1

        prv_path = date_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.PRV.jpg"
        assert prv_path.exists()

        # Ensure size constraint respected
        with Image.open(prv_path) as img:
            w, h = img.size
            assert max(w, h) <= 1000

    def test_overwrite_flag_regenerates_prv(self):
        temp_dir = self.create_temp_dir()
        
        date_dir = temp_dir / "PHOTO_ARCHIVES" / "0001.Family" / "1950" / "1950.06.15"
        sources_dir = date_dir / "SOURCES"
        sources_dir.mkdir(parents=True, exist_ok=True)

        msr_name = "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff"
        msr_path = sources_dir / msr_name
        self._create_tiff(msr_path, size=(3000, 2000))

        prv_path = date_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.PRV.jpg"
        # Create an initial PRV with a small size
        self._create_tiff(prv_path, size=(500, 500))

        maker = PreviewMaker(Logger("test_preview_maker"))

        # Without overwrite, nothing should change
        count_no_overwrite = maker(path=temp_dir, overwrite=False, max_size=800, quality=70)
        assert count_no_overwrite == 0
        with Image.open(prv_path) as img:
            assert max(img.size) == 500

        # With overwrite, PRV should be regenerated and respect new max_size
        count_overwrite = maker(path=temp_dir, overwrite=True, max_size=800, quality=70)
        assert count_overwrite == 1
        with Image.open(prv_path) as img:
            assert max(img.size) <= 800

    def test_generate_prv_from_raw_when_no_msr(self):
        """If only RAW exists, it should still generate a PRV."""
        temp_dir = self.create_temp_dir()

        date_dir = temp_dir / "PHOTO_ARCHIVES" / "0001.Family" / "1951" / "1951.07.20"
        sources_dir = date_dir / "SOURCES"
        sources_dir.mkdir(parents=True, exist_ok=True)

        raw_name = "1951.07.20.13.30.00.E.FAM.POR.0002.A.RAW.tiff"
        raw_path = sources_dir / raw_name
        self._create_tiff(raw_path, size=(3000, 2000))

        maker = PreviewMaker(Logger("test_preview_maker"))
        count = maker(path=temp_dir, overwrite=False, max_size=900, quality=70)
        assert count == 1

        prv_path = date_dir / "1951.07.20.13.30.00.E.FAM.POR.0002.A.PRV.jpg"
        assert prv_path.exists()

        with Image.open(prv_path) as img:
            w, h = img.size
            assert max(w, h) <= 900

    def test_prv_inherits_metadata_with_new_identifier(self):
        """PRV should inherit context metadata but have its own identifier.

        We create an MSR file, let FileOrganizer write full metadata to it,
        then generate a PRV via PreviewMaker and verify that key fields are
        preserved while identifiers differ and a relation back to the master
        is recorded.
        """
        temp_dir = self.create_temp_dir()

        # Skip if exiftool is not available
        if shutil.which("exiftool") is None:
            pytest.skip("ExifTool not found, skipping metadata inheritance test")

        root = temp_dir
        input_dir = root / "input"
        input_dir.mkdir(parents=True, exist_ok=True)

        filename = "1950.06.15.12.30.45.E.FAM.POR.0001.A.MSR.tiff"
        msr_path = input_dir / filename
        self._create_tiff(msr_path)

        logger = Logger("test_preview_maker_metadata")

        # Step 1: run FileOrganizer to write canonical metadata to MSR
        organizer = FileOrganizer(logger)
        config = {
            "metadata": {
                "languages": {
                    "en-US": {
                        "default": True,
                        "creator": "John Doe",
                        "credit": "The Archive",
                        "rights": "Public Domain",
                        "terms": "Free to use",
                        "source": "Box 42",
                    }
                }
            }
        }

        assert organizer.process(msr_path, config)

        processed_msr = input_dir / "processed" / "1950" / "1950.06.15" / "SOURCES" / filename
        assert processed_msr.exists()

        meta_master = self._get_exiftool_json(processed_msr)

        master_id = meta_master.get("XMP:Identifier") or meta_master.get("XMP-dc:Identifier")
        assert master_id

        master_desc = meta_master.get("XMP:Description") or meta_master.get("XMP-dc:Description")
        master_creator = meta_master.get("XMP:Creator") or meta_master.get("XMP-dc:Creator")
        master_rights = meta_master.get("XMP:Rights") or meta_master.get("XMP-dc:Rights")
        master_credit = meta_master.get("XMP:Credit") or meta_master.get("XMP-photoshop:Credit")
        master_usage = meta_master.get("XMP:UsageTerms") or meta_master.get("XMP-xmpRights:UsageTerms")
        master_source = meta_master.get("XMP:Source") or meta_master.get("XMP-dc:Source")

        # Step 2: generate PRV via PreviewMaker
        maker = PreviewMaker(logger)
        count = maker(path=input_dir, overwrite=False, max_size=1000, quality=70)
        assert count == 1

        prv_path = (
            input_dir
            / "processed"
            / "1950"
            / "1950.06.15"
            / "1950.06.15.12.30.45.E.FAM.POR.0001.A.PRV.jpg"
        )
        assert prv_path.exists()

        meta_prv = self._get_exiftool_json(prv_path)

        prv_id = meta_prv.get("XMP:Identifier") or meta_prv.get("XMP-dc:Identifier")
        assert prv_id
        assert prv_id != master_id

        relation = meta_prv.get("XMP:Relation") or meta_prv.get("XMP-dc:Relation")
        assert relation == master_id

        prv_desc = meta_prv.get("XMP:Description") or meta_prv.get("XMP-dc:Description")
        prv_creator = meta_prv.get("XMP:Creator") or meta_prv.get("XMP-dc:Creator")
        prv_rights = meta_prv.get("XMP:Rights") or meta_prv.get("XMP-dc:Rights")
        prv_credit = meta_prv.get("XMP:Credit") or meta_prv.get("XMP-photoshop:Credit")
        prv_usage = meta_prv.get("XMP:UsageTerms") or meta_prv.get("XMP-xmpRights:UsageTerms")
        prv_source = meta_prv.get("XMP:Source") or meta_prv.get("XMP-dc:Source")

        assert prv_desc == master_desc
        assert prv_creator == master_creator
        assert prv_rights == master_rights
        assert prv_credit == master_credit
        assert prv_usage == master_usage
        assert prv_source == master_source

