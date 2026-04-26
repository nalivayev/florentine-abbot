"""Blind per-file tile pyramid generation without config or database access."""

import json
import math
import shutil
from pathlib import Path

from PIL import Image

from common.logger import Logger
from tile_cutter.constants import DEFAULT_SIZE, DEFAULT_TILE_SIZE


class CutterProcessor:
    """Create a tile pyramid for a single source file.

    This class is intentionally blind. It only knows how to read an input
    file, write a tile pyramid to an explicit output directory, and apply
    low-level tiling settings. Archive layout, configuration files, database
    state, task orchestration, and watcher logic are handled by higher layers.
    """

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def process(
        self,
        src_path: Path,
        *,
        output_dir: Path,
        preview_size: int = DEFAULT_SIZE,
        tile_size: int = DEFAULT_TILE_SIZE,
        overwrite: bool = False,
    ) -> tuple[int, Path]:
        """Generate one tile pyramid at the requested output directory.

        Args:
            src_path: Source image file to tile.
            output_dir: Destination directory for the tile pyramid.
            preview_size: Maximum short side for the intermediate image.
            tile_size: Tile side length in pixels.
            overwrite: If True, regenerate an existing tile pyramid.

        Returns:
            Tuple ``(tile_count, path)`` where *tile_count* is the number of
            PNG tiles written. A count of ``0`` means the existing output was
            kept because overwrite was disabled.
        """
        if preview_size <= 0:
            raise ValueError(f"preview_size must be positive: {preview_size}")
        if tile_size <= 0:
            raise ValueError(f"tile_size must be positive: {tile_size}")
        if not src_path.exists():
            self._logger.error(f"Input file does not exist: {src_path}")
            raise FileNotFoundError(f"Input file does not exist: {src_path}")
        if output_dir.exists() and output_dir.is_file():
            raise ValueError(f"Output path points to a file: {output_dir}")
        if output_dir.exists() and not overwrite:
            self._logger.debug(
                f"Skipping existing tile set (overwrite disabled): {output_dir}"
            )
            return 0, output_dir

        Image.MAX_IMAGE_PIXELS = None
        self._logger.info(f"Cutting tiles: {src_path.name} -> {output_dir}")
        total = self._cut_tiles(
            src_path,
            output_dir,
            preview_size=preview_size,
            tile_size=tile_size,
        )
        return total, output_dir

    def _cut_tiles(
        self,
        src_path: Path,
        output_dir: Path,
        *,
        preview_size: int,
        tile_size: int,
    ) -> int:
        """Write a complete tile pyramid via a staging directory."""
        staging_dir = output_dir.parent / (output_dir.name + ".tmp")
        if staging_dir.exists():
            shutil.rmtree(staging_dir)

        try:
            total = self._write_tiles(
                src_path,
                staging_dir,
                preview_size=preview_size,
                tile_size=tile_size,
            )

            if output_dir.exists():
                shutil.rmtree(output_dir)
            staging_dir.rename(output_dir)

        except Exception:
            shutil.rmtree(staging_dir, ignore_errors=True)
            raise

        return total

    def _write_tiles(
        self,
        src_path: Path,
        out_dir: Path,
        *,
        preview_size: int,
        tile_size: int,
    ) -> int:
        """Resize a source image and write the full tile pyramid."""
        with Image.open(src_path) as raw:
            img = raw.convert("RGBA") if raw.mode != "RGBA" else raw.copy()

        width, height = img.size
        short_side = min(width, height)
        if short_side > preview_size:
            scale = preview_size / short_side
            img = img.resize(
                (round(width * scale), round(height * scale)),
                Image.Resampling.LANCZOS,
            )
            width, height = img.size

        max_dim = max(width, height)
        max_zoom = max(0, math.ceil(math.log2(max_dim / tile_size)))

        total = 0
        for zoom in range(max_zoom + 1):
            scale = min(1.0, (tile_size * (2 ** zoom)) / max_dim)
            zoom_width = max(1, round(width * scale))
            zoom_height = max(1, round(height * scale))

            level_img = (
                img
                if (zoom_width, zoom_height) == (width, height)
                else img.resize((zoom_width, zoom_height), Image.Resampling.LANCZOS)
            )

            x_tiles = math.ceil(zoom_width / tile_size)
            y_tiles = math.ceil(zoom_height / tile_size)

            zoom_dir = out_dir / str(zoom)
            zoom_dir.mkdir(parents=True, exist_ok=True)

            for x_index in range(x_tiles):
                for y_index in range(y_tiles):
                    left = x_index * tile_size
                    top = y_index * tile_size
                    right = min(left + tile_size, zoom_width)
                    bottom = min(top + tile_size, zoom_height)
                    tile = level_img.crop((left, top, right, bottom))
                    if tile.size != (tile_size, tile_size):
                        padded = Image.new("RGBA", (tile_size, tile_size), (0, 0, 0, 0))
                        padded.paste(tile, (0, 0))
                        tile = padded
                    x_dir = zoom_dir / str(x_index)
                    x_dir.mkdir(exist_ok=True)
                    tile.save(x_dir / f"{y_index}.png", "PNG")
                    total += 1

        meta = {
            "width": width,
            "height": height,
            "tile_size": tile_size,
            "max_zoom": max_zoom,
        }
        (out_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

        return total
