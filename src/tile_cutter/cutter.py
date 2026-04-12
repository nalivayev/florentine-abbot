"""
Core implementation for Tile Cutter.

Generates a tiled image pyramid from source files in the archive.
Each source is downscaled to a configured intermediate size, then
sliced into JPEG tiles at multiple zoom levels for use with web viewers
such as Leaflet.

Tiles are stored under ``archive/.system/tiles/scan/{collection_id}/{year}/{year}.{month}.{day}/{stem}/``
where the directory layout mirrors the archive structure and
``stem`` is the source filename without extension.

The tile URL template understood by Leaflet is:
    ``/tiles/{year}/{year}.{month}.{day}/{stem}/{z}/{x}.{y}.png``
"""

import fnmatch
import json
import math
import shutil
from pathlib import Path
from typing import Any

from PIL import Image

from common.logger import Logger
from common.constants import SUPPORTED_IMAGE_EXTENSIONS
from common.formatter import Formatter
from common.project_config import ProjectConfig
from tile_cutter.config import Config


class TileCutter:
    """
    Tile generator that can be executed like a function.

    In line with other workflow-like classes (such as :class:`PreviewMaker`),
    a :class:`Logger` instance is provided at construction time, while
    call-specific parameters are passed to :meth:`__call__`.
    """

    def __init__(self, logger: Logger, config_path: str | Path | None = None) -> None:
        self._logger = logger
        self._config = Config(logger, config_path)

        cfg = ProjectConfig.instance()
        self._formatter = Formatter(logger=logger, formats=cfg.formats)

    def __call__(
        self,
        *,
        path: Path,
        overwrite: bool = False,
    ) -> int:
        """
        Run batch tile generation under ``path``.

        This is the primary workflow-style entry point and mirrors how other
        workflow classes are executed.
        """
        return self._generate_tiles_for_sources(path=path, overwrite=overwrite)

    def should_process(self, file_path: Path) -> bool:
        """Check whether a file is eligible for tile generation.

        Checks:

        - Not a symlink
        - Has a supported image extension
        - Filename matches one of the configured ``source_priority`` patterns
        - No higher-priority source sibling exists for the same shot

        Args:
            file_path: Path to the candidate file.

        Returns:
            True if the file should be processed, False otherwise.
        """
        if file_path.is_symlink():
            self._logger.debug(f"Skipping {file_path}: is symlink")
            return False

        if file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            self._logger.debug(f"Skipping {file_path}: unsupported extension '{file_path.suffix}'")
            return False

        parsed = self._formatter.parse(file_path)
        if not parsed:
            self._logger.debug(f"Skipping {file_path}: cannot parse filename")
            return False

        my_priority = self._get_match_priority(file_path.name)
        if my_priority is None:
            self._logger.debug(
                f"Skipping {file_path}: does not match any source_priority pattern"
            )
            return False

        # If a higher-priority source exists for the same shot, skip.
        if my_priority > 0:
            for sibling in file_path.parent.iterdir():
                if sibling == file_path or not sibling.is_file():
                    continue
                sib_priority = self._get_match_priority(sibling.name)
                if sib_priority is not None and sib_priority < my_priority:
                    sib_parsed = self._formatter.parse(sibling)
                    if sib_parsed and self._same_shot(parsed, sib_parsed):
                        self._logger.debug(
                            f"Skipping {file_path.name}: higher-priority source exists ({sibling.name})"
                        )
                        return False

        return True

    def process_single_file(
        self,
        src_path: Path,
        *,
        archive_path: Path,
        overwrite: bool = False,
    ) -> bool:
        """Generate tiles for a single source file.

        Args:
            src_path: Source file matching one of the ``source_priority`` patterns.
            archive_path: Resolved archive root.
            overwrite: If True, regenerate existing tile sets.

        Returns:
            True if tiles were generated, False otherwise.
        """
        parsed = self._formatter.parse(src_path)
        if not parsed:
            raise ValueError(f"Cannot parse filename: {src_path.name}")

        tile_dir = self._tile_dir(archive_path, src_path)

        if tile_dir.exists() and not overwrite:
            self._logger.debug(f"Skipping existing tile set: {tile_dir}")
            return False

        self._logger.info(f"Cutting tiles: {src_path.name} -> {tile_dir}")
        count = self._cut_tiles(src_path, tile_dir)
        self._logger.info(f"Saved {count} tile(s) to {tile_dir}")
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _tile_dir(self, archive_path: Path, src_path: Path) -> Path:
        """Build the output tile directory path for a source file.

        Mirrors the archive path structure:
        scan/000001/2025/2025.06.01/file.tif
        → .system/scan/tiles/000001/2025/2025.06.01/file
        """
        rel = src_path.relative_to(archive_path)
        # rel.parts: ('scan', '000001', '2025', '2025.06.01', 'file.tif')
        # → .system/tiles/scan/000001/2025/2025.06.01/{stem}/
        return archive_path / ".system" / "tiles" / Path(*rel.parts[:-1]) / src_path.stem

    def _cut_tiles(self, src_path: Path, tile_dir: Path) -> int:
        """Open source, resize to target size, cut into tiles.

        Uses a staging directory so the tile set is either fully present
        or absent — never partially written.

        Args:
            src_path: Source image file.
            tile_dir: Final destination directory for this tile set.

        Returns:
            Total number of tile files written.
        """
        staging_dir = tile_dir.parent / (tile_dir.name + ".tmp")
        if staging_dir.exists():
            shutil.rmtree(staging_dir)

        try:
            total = self._write_tiles(src_path, staging_dir)

            # Atomic replace: remove old tile set (if any), then rename staging.
            if tile_dir.exists():
                shutil.rmtree(tile_dir)
            staging_dir.rename(tile_dir)

        except Exception:
            shutil.rmtree(staging_dir, ignore_errors=True)
            raise

        return total

    def _write_tiles(self, src_path: Path, out_dir: Path) -> int:
        """Resize source and write the full tile pyramid into ``out_dir``."""
        with Image.open(src_path) as raw:
            img = raw.convert("RGBA") if raw.mode != "RGBA" else raw.copy()

        # Downscale to configured short-side size (never upscale).
        w, h = img.size
        target = self._config.preview_size
        short = min(w, h)
        if short > target:
            scale = target / short
            img = img.resize((round(w * scale), round(h * scale)), Image.Resampling.LANCZOS)
            w, h = img.size

        tile_size = self._config.tile_size
        max_dim = max(w, h)

        # Number of zoom levels: level 0 fits the image in one tile,
        # level max_zoom shows the image at full (target) resolution.
        max_zoom = max(0, math.ceil(math.log2(max_dim / tile_size)))

        total = 0
        for z in range(max_zoom + 1):
            # Scale the image so its longest side equals tile_size * 2^z,
            # but never enlarge beyond the actual image size.
            scale_z = min(1.0, (tile_size * (2 ** z)) / max_dim)
            zw = max(1, round(w * scale_z))
            zh = max(1, round(h * scale_z))

            level_img = img if (zw, zh) == (w, h) else img.resize((zw, zh), Image.Resampling.LANCZOS)

            nx = math.ceil(zw / tile_size)
            ny = math.ceil(zh / tile_size)

            z_dir = out_dir / str(z)
            z_dir.mkdir(parents=True, exist_ok=True)

            for x in range(nx):
                for y in range(ny):
                    left   = x * tile_size
                    top    = y * tile_size
                    right  = min(left + tile_size, zw)
                    bottom = min(top  + tile_size, zh)
                    tile = level_img.crop((left, top, right, bottom))
                    if tile.size != (tile_size, tile_size):
                        padded = Image.new("RGBA", (tile_size, tile_size), (0, 0, 0, 0))
                        padded.paste(tile, (0, 0))
                        tile = padded
                    x_dir = z_dir / str(x)
                    x_dir.mkdir(exist_ok=True)
                    tile.save(x_dir / f"{y}.png", "PNG")
                    total += 1

        meta = {
            "width": w,
            "height": h,
            "tile_size": tile_size,
            "max_zoom": max_zoom,
        }
        (out_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

        return total

    def _generate_tiles_for_sources(
        self,
        *,
        path: Path,
        overwrite: bool,
    ) -> int:
        """Walk under *path* and generate tile sets for matching source files.

        Skips the ``.system`` subtree to avoid processing derivative files.
        """
        written = 0

        self._logger.debug(
            f"Starting batch tile generation under {path} "
            f"(overwrite={overwrite}, size={self._config.preview_size}, "
            f"tile_size={self._config.tile_size})"
        )

        for src_path in path.rglob("*"):
            if not src_path.is_file():
                continue
            # Skip anything inside .system/
            if ".system" in src_path.parts:
                continue
            if not self.should_process(src_path):
                continue
            try:
                if self.process_single_file(src_path, archive_path=path, overwrite=overwrite):
                    written += 1
            except Exception as e:
                self._logger.error(f"Error processing {src_path.name}: {e}")

        self._logger.info(f"Finished batch tile generation: {written} tile set(s) written")
        return written

    def _get_match_priority(self, filename: str) -> int | None:
        """Return the priority index of the first matching source pattern.

        Returns *None* when the filename does not match any pattern.
        """
        for i, pattern in enumerate(self._config.source_priority):
            if fnmatch.fnmatch(filename.upper(), pattern.upper()):
                return i
        return None

    @staticmethod
    def _same_shot(a: dict[str, Any], b: dict[str, Any]) -> bool:
        """Check whether two parsed filenames represent the same shot."""
        return (
            a["year"]     == b["year"]
            and a["month"]    == b["month"]
            and a["day"]      == b["day"]
            and a["hour"]     == b["hour"]
            and a["minute"]   == b["minute"]
            and a["second"]   == b["second"]
            and a["modifier"] == b["modifier"]
            and a["group"]    == b["group"]
            and a["subgroup"] == b["subgroup"]
            and a["sequence"] == b["sequence"]
            and a["side"]     == b["side"]
        )
