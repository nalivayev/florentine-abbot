"""Regression tests for MakerProcessor file-level behavior."""

from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

from common.logger import Logger
from preview_maker.processor import MakerProcessor
from tests.common.test_utils import create_test_image


class TestMakerProcessor:
    """Covers per-file preview generation without metadata or database access."""

    def test_process_creates_preview_at_explicit_output_path(self) -> None:
        """Processor writes a preview exactly where the caller requests."""
        with TemporaryDirectory() as temp_dir:
            sources_dir = Path(temp_dir) / "input"
            sources_dir.mkdir(parents=True, exist_ok=True)
            output_path = Path(temp_dir) / "output" / "preview.jpg"

            src_path = sources_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff"
            create_test_image(src_path, size=(3000, 2000), color="white", format="TIFF")

            processor = MakerProcessor(Logger("test_preview_processor"))
            written, written_path = processor.process(src_path, output_path=output_path, overwrite=False)

            assert written is True
            assert written_path == output_path
            assert output_path.exists()

            with Image.open(output_path) as img:
                assert max(img.size) <= 2000

    def test_process_skips_existing_preview_without_overwrite(self) -> None:
        """Processor returns False when preview already exists and overwrite is disabled."""
        with TemporaryDirectory() as temp_dir:
            sources_dir = Path(temp_dir) / "input"
            sources_dir.mkdir(parents=True, exist_ok=True)
            output_path = Path(temp_dir) / "output" / "preview.jpg"

            src_path = sources_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff"
            create_test_image(src_path, size=(1200, 800), color="white", format="TIFF")

            processor = MakerProcessor(Logger("test_preview_processor"))
            first_written, first_path = processor.process(src_path, output_path=output_path, overwrite=False)
            second_written, second_path = processor.process(src_path, output_path=output_path, overwrite=False)

            assert first_written is True
            assert first_path == output_path
            assert second_written is False
            assert second_path == output_path

    def test_process_honors_per_call_size(self) -> None:
        """Processor applies the size passed to this individual process call."""
        with TemporaryDirectory() as temp_dir:
            sources_dir = Path(temp_dir) / "input"
            sources_dir.mkdir(parents=True, exist_ok=True)
            output_path = Path(temp_dir) / "output" / "preview.jpg"

            src_path = sources_dir / "1950.06.15.12.00.00.E.FAM.POR.0001.A.MSR.tiff"
            create_test_image(src_path, size=(3000, 2000), color="white", format="TIFF")

            processor = MakerProcessor(Logger("test_preview_processor"))
            written, written_path = processor.process(
                src_path,
                output_path=output_path,
                size=700,
                overwrite=False,
            )

            assert written is True
            assert written_path == output_path

            with Image.open(output_path) as img:
                assert max(img.size) <= 700
