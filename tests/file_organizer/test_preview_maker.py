import shutil
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from file_organizer.preview_maker import generate_previews_for_sources


class TestPreviewMakerBatch:
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def _create_tiff(self, path: Path, size=(4000, 3000)) -> None:
        img = Image.new("RGB", size, color="white")
        img.save(path, format="TIFF")

    def test_generate_prv_from_msr_prefers_msr_over_raw(self, temp_dir):
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

        count = generate_previews_for_sources(temp_dir, overwrite=False, max_size=1000, quality=70)
        assert count == 1

        prv_path = date_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.PRV.jpg"
        assert prv_path.exists()

        # Ensure size constraint respected
        with Image.open(prv_path) as img:
            w, h = img.size
            assert max(w, h) <= 1000

    def test_overwrite_flag_regenerates_prv(self, temp_dir):
        date_dir = temp_dir / "PHOTO_ARCHIVES" / "0001.Family" / "1950" / "1950.06.15"
        sources_dir = date_dir / "SOURCES"
        sources_dir.mkdir(parents=True, exist_ok=True)

        msr_name = "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff"
        msr_path = sources_dir / msr_name
        self._create_tiff(msr_path, size=(3000, 2000))

        prv_path = date_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.PRV.jpg"
        # Create an initial PRV with a small size
        self._create_tiff(prv_path, size=(500, 500))

        # Without overwrite, nothing should change
        count_no_overwrite = generate_previews_for_sources(temp_dir, overwrite=False, max_size=800, quality=70)
        assert count_no_overwrite == 0
        with Image.open(prv_path) as img:
            assert max(img.size) == 500

        # With overwrite, PRV should be regenerated and respect new max_size
        count_overwrite = generate_previews_for_sources(temp_dir, overwrite=True, max_size=800, quality=70)
        assert count_overwrite == 1
        with Image.open(prv_path) as img:
            assert max(img.size) <= 800
