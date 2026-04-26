"""Regression tests for CutterProcessor file-level behavior."""

from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

from common.logger import Logger
from tests.common.test_utils import create_test_image
from tile_cutter.processor import CutterProcessor


class TestCutterProcessor:
    """Covers per-file tile generation without config or database access."""

    def test_process_creates_tile_pyramid_at_explicit_output_dir(self) -> None:
        """Processor writes a tile pyramid exactly where the caller requests."""
        with TemporaryDirectory() as temp_dir:
            sources_dir = Path(temp_dir) / "input"
            sources_dir.mkdir(parents=True, exist_ok=True)
            output_dir = Path(temp_dir) / "output" / "tiles"

            src_path = sources_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff"
            create_test_image(src_path, size=(1200, 900), color="white", format="TIFF")

            processor = CutterProcessor(Logger("test_tile_processor"))
            count, written_dir = processor.process(
                src_path,
                output_dir=output_dir,
                overwrite=False,
            )

            assert count > 0
            assert written_dir == output_dir
            assert (output_dir / "meta.json").exists()

            first_tile = next(output_dir.rglob("*.png"))
            with Image.open(first_tile) as img:
                assert img.format == "PNG"
                assert img.mode == "RGBA"

    def test_process_skips_existing_tiles_without_overwrite(self) -> None:
        """Processor returns zero tiles when output already exists and overwrite is off."""
        with TemporaryDirectory() as temp_dir:
            sources_dir = Path(temp_dir) / "input"
            sources_dir.mkdir(parents=True, exist_ok=True)
            output_dir = Path(temp_dir) / "output" / "tiles"

            src_path = sources_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff"
            create_test_image(src_path, size=(800, 600), color="white", format="TIFF")

            processor = CutterProcessor(Logger("test_tile_processor"))
            first_count, first_dir = processor.process(
                src_path,
                output_dir=output_dir,
                overwrite=False,
            )
            second_count, second_dir = processor.process(
                src_path,
                output_dir=output_dir,
                overwrite=False,
            )

            assert first_count > 0
            assert first_dir == output_dir
            assert second_count == 0
            assert second_dir == output_dir

    def test_process_honors_per_call_tile_size(self) -> None:
        """Processor applies the tile size passed to this individual process call."""
        with TemporaryDirectory() as temp_dir:
            sources_dir = Path(temp_dir) / "input"
            sources_dir.mkdir(parents=True, exist_ok=True)
            output_dir = Path(temp_dir) / "output" / "tiles"

            src_path = sources_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff"
            create_test_image(src_path, size=(1600, 1200), color="white", format="TIFF")

            processor = CutterProcessor(Logger("test_tile_processor"))
            count, _output_dir = processor.process(
                src_path,
                output_dir=output_dir,
                preview_size=500,
                tile_size=128,
                overwrite=False,
            )

            assert count > 0

            for tile_path in output_dir.rglob("*.png"):
                with Image.open(tile_path) as img:
                    assert max(img.size) <= 128
