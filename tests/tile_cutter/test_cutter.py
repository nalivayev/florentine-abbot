"""
Tests for TileCutter batch and single-file processing.
"""

import os
import shutil
import tempfile
from pathlib import Path

from PIL import Image

from tile_cutter.cutter import TileCutter
from common.logger import Logger
from common.project_config import ProjectConfig
from common.constants import DEFAULT_CONFIG
from tests.common.test_utils import create_test_image


class TestTileCutterBatch:

    def setup_method(self) -> None:
        self.temp_dir: Path | None = None

    def teardown_method(self) -> None:
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, onerror=self._force_remove)

    @staticmethod
    def _force_remove(func: object, path: str, exc_info: object) -> None:
        os.chmod(path, 0o700)
        os.unlink(path)

    def create_temp_dir(self) -> Path:
        self.temp_dir = Path(tempfile.mkdtemp())
        return self.temp_dir

    def _make_archive(self, temp_dir: Path, filename: str, size: tuple[int, int] = (800, 600)) -> tuple[Path, Path]:
        """Create a minimal archive fragment with one source file.

        Returns (archive_root, src_path).
        """
        sources = temp_dir / "archive" / "1950" / "1950.06.15" / "SOURCES"
        sources.mkdir(parents=True, exist_ok=True)
        src = sources / filename
        create_test_image(src, size=size, format="TIFF")
        return temp_dir / "archive", src

    def _tile_dir(self, archive: Path, stem: str) -> Path:
        return archive / ".system" / "scan" / "tiles" / "1950" / "1950.06.15" / stem

    def _make_archive_at(self, root: Path, size: tuple[int, int]) -> Path:
        sources = root / "archive" / "1950" / "1950.06.15" / "SOURCES"
        sources.mkdir(parents=True, exist_ok=True)
        src = sources / "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff"
        create_test_image(src, size=size, format="TIFF")
        return root / "archive"

    def _zoom_levels(self, archive: Path, stem: str) -> int:
        tile_dir = archive / ".system" / "scan" / "tiles" / "1950" / "1950.06.15" / stem
        return len([d for d in tile_dir.iterdir() if d.is_dir()])

    def test_batch_generates_tile_pyramid(self) -> None:
        """Batch call produces a tile set with the expected zoom structure."""
        temp_dir = self.create_temp_dir()
        archive, src = self._make_archive(
            temp_dir, "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff", size=(800, 600)
        )

        cutter = TileCutter(Logger("test_tile_cutter"))
        count = cutter(path=archive, overwrite=False)
        assert count == 1

        tile_dir = self._tile_dir(archive, src.stem)
        assert tile_dir.exists()

        # At least zoom level 0 must exist
        z0 = tile_dir / "0"
        assert z0.is_dir()
        tiles = list(z0.glob("*.png"))
        assert len(tiles) >= 1

    def test_tiles_are_valid_pngs(self) -> None:
        """Every tile file must be a readable PNG with alpha channel."""
        temp_dir = self.create_temp_dir()
        archive, _ = self._make_archive(
            temp_dir, "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff", size=(512, 512)
        )

        cutter = TileCutter(Logger("test_tile_cutter"))
        cutter(path=archive, overwrite=False)

        for tile_path in (archive / ".system" / "scan" / "tiles").rglob("*.png"):
            with Image.open(tile_path) as img:
                assert img.format == "PNG"
                assert img.mode == "RGBA"

    def test_tiles_never_exceed_tile_size(self) -> None:
        """No tile dimension exceeds the configured tile_size (default 256)."""
        temp_dir = self.create_temp_dir()
        archive, _ = self._make_archive(
            temp_dir, "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff", size=(1024, 768)
        )

        cutter = TileCutter(Logger("test_tile_cutter"))
        cutter(path=archive, overwrite=False)

        for tile_path in (archive / ".system" / "scan" / "tiles").rglob("*.png"):
            with Image.open(tile_path) as img:
                assert max(img.size) <= 256

    def test_skips_existing_tile_set_without_overwrite(self) -> None:
        """Second call without overwrite returns 0 (already generated)."""
        temp_dir = self.create_temp_dir()
        archive, _ = self._make_archive(
            temp_dir, "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff"
        )

        cutter = TileCutter(Logger("test_tile_cutter"))
        first = cutter(path=archive, overwrite=False)
        assert first == 1

        second = cutter(path=archive, overwrite=False)
        assert second == 0

    def test_overwrite_regenerates_tile_set(self) -> None:
        """overwrite=True regenerates the tile set."""
        temp_dir = self.create_temp_dir()
        archive, _ = self._make_archive(
            temp_dir, "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff"
        )

        cutter = TileCutter(Logger("test_tile_cutter"))
        cutter(path=archive, overwrite=False)
        count = cutter(path=archive, overwrite=True)
        assert count == 1

    def test_prefers_msr_over_raw(self) -> None:
        """When both MSR and RAW exist for the same shot, only MSR is processed."""
        temp_dir = self.create_temp_dir()
        sources = temp_dir / "archive" / "1950" / "1950.06.15" / "SOURCES"
        sources.mkdir(parents=True, exist_ok=True)

        msr = sources / "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff"
        raw = sources / "1950.06.15.12.00.00.E.FAM.POR.0001.A.RAW.tiff"
        create_test_image(msr, size=(400, 300), format="TIFF")
        create_test_image(raw, size=(400, 300), format="TIFF")

        archive = temp_dir / "archive"
        cutter = TileCutter(Logger("test_tile_cutter"))
        count = cutter(path=archive, overwrite=False)

        # Only one tile set — for MSR
        assert count == 1
        msr_tiles = self._tile_dir(archive, msr.stem)
        raw_tiles = self._tile_dir(archive, raw.stem)
        assert msr_tiles.exists()
        assert not raw_tiles.exists()

    def test_zoom_levels_increase_with_image_size(self) -> None:
        """A larger image produces more zoom levels than a smaller one."""
        temp_dir = self.create_temp_dir()

        small_dir = temp_dir / "small"
        large_dir = temp_dir / "large"

        small_archive = self._make_archive_at(small_dir, (256, 256))
        large_archive = self._make_archive_at(large_dir, (2048, 2048))

        cutter = TileCutter(Logger("test_tile_cutter"))
        cutter(path=small_archive, overwrite=False)
        cutter(path=large_archive, overwrite=False)

        stem = "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR"
        small_levels = self._zoom_levels(small_archive, stem)
        large_levels = self._zoom_levels(large_archive, stem)
        assert large_levels > small_levels

    def test_staging_dir_cleaned_up_on_success(self) -> None:
        """The .tmp staging directory must not remain after successful generation."""
        temp_dir = self.create_temp_dir()
        archive, src = self._make_archive(
            temp_dir, "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff"
        )

        cutter = TileCutter(Logger("test_tile_cutter"))
        cutter(path=archive, overwrite=False)

        tile_dir = self._tile_dir(archive, src.stem)
        staging = tile_dir.parent / (tile_dir.name + ".tmp")
        assert not staging.exists()


class TestTileCutterSingleFile:

    def setup_method(self) -> None:
        self.temp_dir: Path | None = None

    def teardown_method(self) -> None:
        ProjectConfig.instance(data=DEFAULT_CONFIG)
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_temp_dir(self) -> Path:
        self.temp_dir = Path(tempfile.mkdtemp())
        return self.temp_dir

    def test_process_single_file_returns_true(self) -> None:
        temp_dir = self.create_temp_dir()
        sources = temp_dir / "archive" / "1952" / "1952.03.10" / "SOURCES"
        sources.mkdir(parents=True, exist_ok=True)
        src = sources / "1952.03.10.08.00.00.E.FAM.POR.0001.A.MSR.tiff"
        create_test_image(src, size=(512, 384), format="TIFF")

        archive = temp_dir / "archive"
        cutter = TileCutter(Logger("test"))
        result = cutter.process_single_file(src, archive_path=archive, overwrite=False)
        assert result is True

    def test_process_single_file_skips_on_second_call(self) -> None:
        temp_dir = self.create_temp_dir()
        sources = temp_dir / "archive" / "1952" / "1952.03.10" / "SOURCES"
        sources.mkdir(parents=True, exist_ok=True)
        src = sources / "1952.03.10.08.00.00.E.FAM.POR.0001.A.MSR.tiff"
        create_test_image(src, size=(512, 384), format="TIFF")

        archive = temp_dir / "archive"
        cutter = TileCutter(Logger("test"))
        cutter.process_single_file(src, archive_path=archive, overwrite=False)
        result = cutter.process_single_file(src, archive_path=archive, overwrite=False)
        assert result is False

    def test_tile_dir_path_matches_date_from_filename(self) -> None:
        """Tile directory must reflect year/month/day from the filename."""
        temp_dir = self.create_temp_dir()
        sources = temp_dir / "archive" / "1963" / "1963.11.22" / "SOURCES"
        sources.mkdir(parents=True, exist_ok=True)
        src = sources / "1963.11.22.14.30.00.E.FAM.POR.0002.A.MSR.tiff"
        create_test_image(src, size=(400, 300), format="TIFF")

        archive = temp_dir / "archive"
        cutter = TileCutter(Logger("test"))
        cutter.process_single_file(src, archive_path=archive, overwrite=False)

        expected = archive / ".system" / "scan" / "tiles" / "1963" / "1963.11.22" / src.stem
        assert expected.exists()
