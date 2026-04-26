"""Blind per-file preview generation without metadata, config, or database access."""

from pathlib import Path
from typing import Any

from PIL import Image

from common.logger import Logger
from preview_maker.constants import DEFAULT_SIZE, FORMAT_MAP, DEFAULT_FORMAT_OPTIONS, FORMAT_ALIASES


class MakerProcessor:
    """Create preview pixels for a single source file.

    This class is intentionally blind. It only knows how to read an input
    file, write an output file, and apply low-level conversion settings.
    Archive layout, naming, metadata, configuration files, database state,
    tasks, and watcher orchestration are handled by higher layers.
    """

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    @staticmethod
    def _normalize_format(name: str) -> str:
        """Normalize a format name, resolving common aliases."""
        name = name.lower()
        return FORMAT_ALIASES.get(name, name)

    def process(
        self,
        src_path: Path,
        *,
        output_path: Path,
        size: int = DEFAULT_SIZE,
        save_options: dict[str, Any] | None = None,
        overwrite: bool = False,
    ) -> tuple[bool, Path]:
        """Generate a preview for a single source file.

        Args:
            src_path: Source file to convert.
            output_path: Output file path.
            size: Maximum long edge in pixels.
            save_options: Low-level PIL save kwargs for the selected format.
            overwrite: If True, regenerate an existing preview file.

        Returns:
            Tuple ``(written, path)`` where *written* indicates whether a new
            preview file was produced.
        """
        if not src_path.exists():
            self._logger.error(f"Input file does not exist: {src_path}")
            raise FileNotFoundError(f"Input file does not exist: {src_path}")

        if output_path.exists() and not overwrite:
            self._logger.debug(f"Skipping existing preview (overwrite disabled): {output_path}")
            return False, output_path

        image_format = output_path.suffix.lower().lstrip(".")
        if not image_format:
            raise ValueError(f"Output path must include a file extension: {output_path}")
        image_format = self._normalize_format(image_format)

        entry = FORMAT_MAP.get(image_format)
        if not entry:
            raise ValueError(
                f"Unsupported image format '{image_format}'. "
                f"Supported: {', '.join(sorted(FORMAT_MAP))}"
            )
        pil_format, _file_extension = entry

        final_save_options = (
            dict(save_options)
            if save_options is not None
            else dict(DEFAULT_FORMAT_OPTIONS.get(image_format, {}))
        )

        Image.MAX_IMAGE_PIXELS = None
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._logger.info(f"Creating preview: {src_path.name} -> {output_path}")
        self._logger.debug(
            f"Converting {src_path} -> {output_path} "
            f"(format={pil_format}, size={size}, options={final_save_options})"
        )

        with Image.open(src_path) as img:
            img.load()

            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            img.save(output_path, format=pil_format, **final_save_options)

        return True, output_path
