import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from preview_maker import PreviewMaker
from file_organizer.organizer import FileOrganizer
from common.logger import Logger
from common.constants import (
    TAG_XMP_DC_IDENTIFIER, TAG_XMP_XMP_IDENTIFIER, TAG_XMP_DC_RELATION,
    TAG_XMP_DC_DESCRIPTION, TAG_XMP_DC_CREATOR, TAG_XMP_DC_RIGHTS,
    TAG_XMP_PHOTOSHOP_CREDIT, TAG_XMP_XMPRIGHTS_USAGE_TERMS, TAG_XMP_DC_SOURCE,
    TAG_XMP_XMPMM_DOCUMENT_ID, TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID,
)
from common.exifer import Exifer
from tests.common.test_utils import create_test_image, exiftool_available


class TestPreviewMakerBatch:
    def setup_method(self):
        """
        Setup for each test method.
        """
        self.temp_dir = None

    def teardown_method(self):
        """
        Cleanup after each test method.
        """
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_temp_dir(self) -> Path:
        """
        Create a temporary directory.
        """
        temp_dir = tempfile.mkdtemp()
        self.temp_dir = Path(temp_dir)
        return self.temp_dir

    def _get_exiftool_json(self, file_path: Path) -> dict:
        cmd = ["exiftool", "-json", "-G", str(file_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8')
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

        create_test_image(raw_path, color="white", format="TIFF")
        create_test_image(msr_path, color="white", format="TIFF")

        maker = PreviewMaker(Logger("test_preview_maker"))
        # Pass the archive base (where the year folders start)
        archive_base = temp_dir / "PHOTO_ARCHIVES" / "0001.Family"
        count = maker(path=archive_base, overwrite=False, max_size=1000, quality=70)
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
        create_test_image(msr_path, size=(3000, 2000), color="white", format="TIFF")

        prv_path = date_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.PRV.jpg"
        # Create an initial PRV with a small size
        create_test_image(prv_path, size=(500, 500), color="white", format="JPEG")

        maker = PreviewMaker(Logger("test_preview_maker"))
        archive_base = temp_dir / "PHOTO_ARCHIVES" / "0001.Family"

        # Without overwrite, nothing should change
        count_no_overwrite = maker(path=archive_base, overwrite=False, max_size=800, quality=70)
        assert count_no_overwrite == 0
        with Image.open(prv_path) as img:
            assert max(img.size) == 500

        # With overwrite, PRV should be regenerated and respect new max_size
        count_overwrite = maker(path=archive_base, overwrite=True, max_size=800, quality=70)
        assert count_overwrite == 1
        with Image.open(prv_path) as img:
            assert max(img.size) <= 800

    def test_msr_upgrade_regenerates_prv_from_raw(self, require_exiftool):
        """
        When MSR appears after PRV was already generated from RAW,
        process_single_file should regenerate the PRV from MSR even
        without overwrite=True.

        The upgrade is detected by comparing DerivedFromDocumentID in the
        existing PRV against the MSR's DocumentID.
        """
        temp_dir = self.create_temp_dir()

        date_dir = temp_dir / "PHOTO_ARCHIVES" / "0001.Family" / "1952" / "1952.01.10"
        sources_dir = date_dir / "SOURCES"
        sources_dir.mkdir(parents=True, exist_ok=True)

        raw_name = "1952.01.10.08.00.00.E.FAM.POR.0001.A.RAW.tiff"
        raw_path = sources_dir / raw_name
        create_test_image(raw_path, size=(2000, 1500), color="blue", format="TIFF")

        logger = Logger("test_msr_upgrade")
        maker = PreviewMaker(logger)
        archive_base = temp_dir / "PHOTO_ARCHIVES" / "0001.Family"

        # Step 1: generate PRV from RAW
        result = maker.process_single_file(
            raw_path,
            archive_path=archive_base,
            overwrite=False,
            max_size=800,
            quality=70,
        )
        assert result is True

        prv_path = date_dir / "1952.01.10.08.00.00.E.FAM.POR.0001.A.PRV.jpg"
        assert prv_path.exists()

        # Read the PRV's DerivedFromDocumentID — should point to RAW's DocumentID
        exifer = Exifer()
        prv_meta_before = exifer.read(prv_path, [TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID])
        raw_meta = exifer.read(raw_path, [TAG_XMP_XMPMM_DOCUMENT_ID])
        assert prv_meta_before[TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID] == raw_meta[TAG_XMP_XMPMM_DOCUMENT_ID]

        # Step 2: create MSR for the same frame (different DocumentID)
        msr_name = "1952.01.10.08.00.00.E.FAM.POR.0001.A.MSR.tiff"
        msr_path = sources_dir / msr_name
        create_test_image(msr_path, size=(2000, 1500), color="green", format="TIFF")

        msr_meta = exifer.read(msr_path, [TAG_XMP_XMPMM_DOCUMENT_ID])
        msr_doc_id = msr_meta[TAG_XMP_XMPMM_DOCUMENT_ID]

        # The MSR has a different DocumentID than the RAW
        assert msr_doc_id != raw_meta[TAG_XMP_XMPMM_DOCUMENT_ID]

        # Step 3: process MSR — should upgrade PRV without overwrite flag
        result = maker.process_single_file(
            msr_path,
            archive_path=archive_base,
            overwrite=False,
            max_size=800,
            quality=70,
        )
        assert result is True, "Expected PRV upgrade from MSR"

        # Step 4: verify PRV now derives from MSR
        prv_meta_after = exifer.read(prv_path, [TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID])
        assert prv_meta_after[TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID] == msr_doc_id

    def test_msr_no_upgrade_when_prv_already_from_msr(self, require_exiftool):
        """
        When PRV was already generated from MSR, presenting the same MSR
        again should NOT regenerate (DerivedFromDocumentID already matches).
        """
        temp_dir = self.create_temp_dir()

        date_dir = temp_dir / "PHOTO_ARCHIVES" / "0001.Family" / "1953" / "1953.05.20"
        sources_dir = date_dir / "SOURCES"
        sources_dir.mkdir(parents=True, exist_ok=True)

        msr_name = "1953.05.20.14.00.00.E.FAM.POR.0001.A.MSR.tiff"
        msr_path = sources_dir / msr_name
        create_test_image(msr_path, size=(2000, 1500), color="red", format="TIFF")

        logger = Logger("test_msr_no_upgrade")
        maker = PreviewMaker(logger)
        archive_base = temp_dir / "PHOTO_ARCHIVES" / "0001.Family"

        # Generate PRV from MSR
        result = maker.process_single_file(
            msr_path,
            archive_path=archive_base,
            overwrite=False,
            max_size=800,
            quality=70,
        )
        assert result is True

        prv_path = date_dir / "1953.05.20.14.00.00.E.FAM.POR.0001.A.PRV.jpg"
        assert prv_path.exists()

        # Process MSR again — should skip (DerivedFromDocumentID matches)
        result = maker.process_single_file(
            msr_path,
            archive_path=archive_base,
            overwrite=False,
            max_size=800,
            quality=70,
        )
        assert result is False, "Should skip when PRV already derived from same MSR"

    def test_generate_prv_from_raw_when_no_msr(self):
        """
        If only RAW exists, it should still generate a PRV.
        """
        temp_dir = self.create_temp_dir()

        date_dir = temp_dir / "PHOTO_ARCHIVES" / "0001.Family" / "1951" / "1951.07.20"
        sources_dir = date_dir / "SOURCES"
        sources_dir.mkdir(parents=True, exist_ok=True)

        raw_name = "1951.07.20.13.30.00.E.FAM.POR.0002.A.RAW.tiff"
        raw_path = sources_dir / raw_name
        create_test_image(raw_path, size=(3000, 2000), color="white", format="TIFF")

        maker = PreviewMaker(Logger("test_preview_maker"))
        archive_base = temp_dir / "PHOTO_ARCHIVES" / "0001.Family"
        count = maker(path=archive_base, overwrite=False, max_size=900, quality=70)
        assert count == 1

        prv_path = date_dir / "1951.07.20.13.30.00.E.FAM.POR.0002.A.PRV.jpg"
        assert prv_path.exists()

        with Image.open(prv_path) as img:
            w, h = img.size
            assert max(w, h) <= 900

    def test_prv_inherits_metadata_with_new_identifier(self, require_exiftool):
        """
        PRV should inherit context metadata but have its own identifier.

        We create an MSR file, let FileOrganizer write full metadata to it,
        then generate a PRV via PreviewMaker and verify that key fields are
        preserved while identifiers differ and a relation back to the master
        is recorded.
        """
        temp_dir = self.create_temp_dir()

        input_dir = temp_dir / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir = temp_dir / "output"

        filename = "1950.06.15.12.30.45.E.FAM.POR.0001.A.MSR.tiff"
        msr_path = input_dir / filename
        create_test_image(msr_path, color="white", format="TIFF")

        logger = Logger("test_preview_maker_metadata")

        # Step 1: run FileOrganizer in batch mode to write canonical metadata to MSR
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

        # Write config to disk and use batch API so move/copy is handled by organizer
        config_path = input_dir / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")

        processed_count = organizer(
            input_path=input_dir,
            output_path=output_dir,
            config_path=config_path,
            recursive=False,
            copy_mode=False,
        )
        assert processed_count == 1

        processed_msr = output_dir / "1950" / "1950.06.15" / "SOURCES" / filename
        assert processed_msr.exists()

        meta_master = self._get_exiftool_json(processed_msr)

        master_id = meta_master.get(TAG_XMP_XMP_IDENTIFIER) or meta_master.get(TAG_XMP_DC_IDENTIFIER) or meta_master.get("XMP:Identifier")
        assert master_id

        master_desc = meta_master.get(TAG_XMP_DC_DESCRIPTION) or meta_master.get("XMP:Description")
        master_creator = meta_master.get(TAG_XMP_DC_CREATOR) or meta_master.get("XMP:Creator")
        master_rights = meta_master.get(TAG_XMP_DC_RIGHTS) or meta_master.get("XMP:Rights")
        master_credit = meta_master.get(TAG_XMP_PHOTOSHOP_CREDIT) or meta_master.get("XMP:Credit")
        master_usage = meta_master.get(TAG_XMP_XMPRIGHTS_USAGE_TERMS) or meta_master.get("XMP:UsageTerms")
        master_source = meta_master.get(TAG_XMP_DC_SOURCE) or meta_master.get("XMP:Source")

        # Step 2: generate PRV via PreviewMaker
        maker = PreviewMaker(logger)
        # Pass the archive base where year folders begin
        archive_base = output_dir
        count = maker(path=archive_base, overwrite=False, max_size=1000, quality=70)
        assert count == 1

        prv_path = (
            output_dir
            / "1950"
            / "1950.06.15"
            / "1950.06.15.12.30.45.E.FAM.POR.0001.A.PRV.jpg"
        )
        assert prv_path.exists()

        meta_prv = self._get_exiftool_json(prv_path)

        prv_id = meta_prv.get(TAG_XMP_XMP_IDENTIFIER) or meta_prv.get(TAG_XMP_DC_IDENTIFIER) or meta_prv.get("XMP:Identifier")
        assert prv_id
        assert prv_id != master_id

        relation = meta_prv.get(TAG_XMP_DC_RELATION) or meta_prv.get("XMP:Relation")
        assert relation == master_id

        prv_desc = meta_prv.get(TAG_XMP_DC_DESCRIPTION) or meta_prv.get("XMP:Description")
        prv_creator = meta_prv.get(TAG_XMP_DC_CREATOR) or meta_prv.get("XMP:Creator")
        prv_rights = meta_prv.get(TAG_XMP_DC_RIGHTS) or meta_prv.get("XMP:Rights")
        prv_credit = meta_prv.get(TAG_XMP_PHOTOSHOP_CREDIT) or meta_prv.get("XMP:Credit")
        prv_usage = meta_prv.get(TAG_XMP_XMPRIGHTS_USAGE_TERMS) or meta_prv.get("XMP:UsageTerms")
        prv_source = meta_prv.get(TAG_XMP_DC_SOURCE) or meta_prv.get("XMP:Source")

        assert prv_desc == master_desc
        assert prv_creator == master_creator
        assert prv_rights == master_rights
        assert prv_credit == master_credit
        assert prv_usage == master_usage
        assert prv_source == master_source

    @pytest.mark.skipif(not exiftool_available(), reason="exiftool not installed")
    def test_convert_skips_metadata_when_no_metadata(self):
        """_convert_to_prv does not call _write_derivative_metadata when flag is set."""
        temp_dir = self.create_temp_dir()

        date_dir = temp_dir / "ARCHIVES" / "0001.Family" / "1950" / "1950.06.15"
        sources_dir = date_dir / "SOURCES"
        sources_dir.mkdir(parents=True, exist_ok=True)

        msr_path = sources_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff"
        create_test_image(msr_path)

        prv_dir = date_dir / "PREVIEWS"
        prv_dir.mkdir(parents=True, exist_ok=True)
        prv_path = prv_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.PRV.jpg"

        logger = Logger("test", console=False)
        maker = PreviewMaker(logger, no_metadata=True)

        with patch.object(maker, '_write_derivative_metadata') as mock_write:
            maker._convert_to_prv(
                input_path=msr_path, output_path=prv_path,
                max_size=200, quality=80,
            )

        assert prv_path.exists()
        mock_write.assert_not_called()

    @pytest.mark.skipif(not exiftool_available(), reason="exiftool not installed")
    def test_convert_writes_metadata_when_no_metadata_is_false(self):
        """_convert_to_prv calls _write_derivative_metadata normally when flag is off."""
        temp_dir = self.create_temp_dir()

        date_dir = temp_dir / "ARCHIVES" / "0001.Family" / "1950" / "1950.06.15"
        sources_dir = date_dir / "SOURCES"
        sources_dir.mkdir(parents=True, exist_ok=True)

        msr_path = sources_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff"
        create_test_image(msr_path)

        prv_dir = date_dir / "PREVIEWS"
        prv_dir.mkdir(parents=True, exist_ok=True)
        prv_path = prv_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.PRV.jpg"

        logger = Logger("test", console=False)
        maker = PreviewMaker(logger, no_metadata=False)

        with patch.object(maker, '_write_derivative_metadata') as mock_write:
            maker._convert_to_prv(
                input_path=msr_path, output_path=prv_path,
                max_size=200, quality=80,
            )

        assert prv_path.exists()
        mock_write.assert_called_once()


class TestPreviewMakerCustomFormats:
    """
    Test PreviewMaker with custom path formats.
    """
    
    def setup_method(self):
        """
        Setup for each test method.
        """
        self.temp_dir = None
    
    def teardown_method(self):
        """
        Cleanup after each test method.
        """
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_temp_dir(self) -> Path:
        """
        Create a temporary directory.
        """
        temp_dir = tempfile.mkdtemp()
        self.temp_dir = Path(temp_dir)
        return self.temp_dir
    

    
    def test_generate_prv_with_flat_path_structure(self):
        """
        Test preview generation with flat path structure (no year folder).
        """
        temp_dir = self.create_temp_dir()
        logger = Logger("test", console=False)
        
        # Create archive with flat structure: 2024.03.15/SOURCES/
        date_dir = temp_dir / "archive" / "2024.03.15"
        sources_dir = date_dir / "SOURCES"
        sources_dir.mkdir(parents=True, exist_ok=True)
        
        msr_name = "2024.03.15.10.30.00.E.TEST.GRP.0001.A.MSR.tiff"
        msr_path = sources_dir / msr_name
        create_test_image(msr_path, color="green", format="TIFF")
        
        # Create custom formatter with flat structure
        from common.formatter import Formatter
        from common.router import Router
        
        formatter = Formatter(
            path_template="{year:04d}.{month:02d}.{day:02d}",
            filename_template="{year:04d}.{month:02d}.{day:02d}.{hour:02d}.{minute:02d}.{second:02d}.{modifier}.{group}.{subgroup}.{sequence:04d}.{side}.{suffix}"
        )
        
        # Create PreviewMaker with custom router
        maker = PreviewMaker(logger=logger)
        maker._router._formatter = formatter
        
        # Generate preview
        count = maker(path=temp_dir / "archive", overwrite=False, max_size=800)
        assert count == 1
        
        # Preview should be in: 2024.03.15/2024.03.15.10.30.00.E.TEST.GRP.0001.A.PRV.jpg
        prv_name = "2024.03.15.10.30.00.E.TEST.GRP.0001.A.PRV.jpg"
        prv_path = date_dir / prv_name
        
        assert prv_path.exists(), f"PRV not found at {prv_path}"
    
    def test_generate_prv_with_month_grouping(self):
        """
        Test preview generation with year/month grouping.
        """
        temp_dir = self.create_temp_dir()
        logger = Logger("test", console=False)
        
        # Create archive with month structure: 2024/2024.03/SOURCES/
        date_dir = temp_dir / "archive" / "2024" / "2024.03"
        sources_dir = date_dir / "SOURCES"
        sources_dir.mkdir(parents=True, exist_ok=True)
        
        msr_name = "2024.03.15.10.30.00.E.TEST.GRP.0001.A.MSR.tiff"
        msr_path = sources_dir / msr_name
        create_test_image(msr_path, color="green", format="TIFF")
        
        from common.formatter import Formatter
        
        formatter = Formatter(
            path_template="{year:04d}/{year:04d}.{month:02d}",
            filename_template="{year:04d}.{month:02d}.{day:02d}.{hour:02d}.{minute:02d}.{second:02d}.{modifier}.{group}.{subgroup}.{sequence:04d}.{side}.{suffix}"
        )
        
        maker = PreviewMaker(logger=logger)
        maker._router._formatter = formatter
        
        count = maker(path=temp_dir / "archive", overwrite=False, max_size=800)
        assert count == 1
        
        # Preview should be in: 2024/2024.03/2024.03.15.10.30.00.E.TEST.GRP.0001.A.PRV.jpg
        prv_name = "2024.03.15.10.30.00.E.TEST.GRP.0001.A.PRV.jpg"
        prv_path = date_dir / prv_name
        
        assert prv_path.exists(), f"PRV not found at {prv_path}"
    
    def test_generate_prv_with_group_in_path(self):
        """
        Test preview generation with group in path structure.
        """
        temp_dir = self.create_temp_dir()
        logger = Logger("test", console=False)
        
        # Create archive: FAM/2024/2024.03.15/SOURCES/
        date_dir = temp_dir / "archive" / "FAM" / "2024" / "2024.03.15"
        sources_dir = date_dir / "SOURCES"
        sources_dir.mkdir(parents=True, exist_ok=True)
        
        msr_name = "2024.03.15.10.30.00.E.FAM.POR.0001.A.MSR.tiff"
        msr_path = sources_dir / msr_name
        create_test_image(msr_path, color="green", format="TIFF")
        
        from common.formatter import Formatter
        
        formatter = Formatter(
            path_template="{group}/{year:04d}/{year:04d}.{month:02d}.{day:02d}",
            filename_template="{year:04d}.{month:02d}.{day:02d}.{hour:02d}.{minute:02d}.{second:02d}.{modifier}.{group}.{subgroup}.{sequence:04d}.{side}.{suffix}"
        )
        
        maker = PreviewMaker(logger=logger)
        maker._router._formatter = formatter
        
        count = maker(path=temp_dir / "archive", overwrite=False, max_size=800)
        assert count == 1
        
        # Preview should be in: FAM/2024/2024.03.15/2024.03.15.10.30.00.E.FAM.POR.0001.A.PRV.jpg
        prv_name = "2024.03.15.10.30.00.E.FAM.POR.0001.A.PRV.jpg"
        prv_path = date_dir / prv_name
        
        assert prv_path.exists(), f"PRV not found at {prv_path}"
    
    def test_generate_prv_with_compact_filename(self):
        """
        Test preview generation with compact filename format.
        """
        temp_dir = self.create_temp_dir()
        logger = Logger("test", console=False)
        
        # Create archive: 2024/2024.03.15/SOURCES/
        date_dir = temp_dir / "archive" / "2024" / "2024.03.15"
        sources_dir = date_dir / "SOURCES"
        sources_dir.mkdir(parents=True, exist_ok=True)
        
        # Master has standard name
        msr_name = "2024.03.15.10.30.00.E.TEST.GRP.0001.A.MSR.tiff"
        msr_path = sources_dir / msr_name
        create_test_image(msr_path, color="green", format="TIFF")
        
        from common.formatter import Formatter
        
        formatter = Formatter(
            path_template="{year:04d}/{year:04d}.{month:02d}.{day:02d}",
            filename_template="{year:04d}{month:02d}{day:02d}_{hour:02d}{minute:02d}{second:02d}_{group}_{suffix}"
        )
        
        maker = PreviewMaker(logger=logger)
        maker._router._formatter = formatter
        
        count = maker(path=temp_dir / "archive", overwrite=False, max_size=800)
        assert count == 1
        
        # Preview should have compact name: 20240315_103000_TEST_PRV.jpg
        prv_name = "20240315_103000_TEST_PRV.jpg"
        prv_path = date_dir / prv_name
        
        assert prv_path.exists(), f"PRV not found at {prv_path}"
