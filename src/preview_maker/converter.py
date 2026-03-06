"""
Pure image converter for Preview Maker.

:class:`Converter` handles pixel-level conversion — resizing and format
conversion — without any knowledge of the archival pipeline, metadata,
routing, or naming conventions.

It is used directly by the ``convert`` CLI command and internally by
:class:`PreviewMaker` for batch/watch modes.
"""

from pathlib import Path
from typing import Any

from PIL import Image

from common.logger import Logger
from preview_maker.constants import FORMAT_MAP, DEFAULT_FORMAT_OPTIONS, FORMAT_ALIASES, DEFAULT_SIZE, DEFAULT_FORMAT


class Converter:
    """Stateless image converter.

    Resizes a source image to fit within a bounding box and saves it
    in the requested format with the given save options.

    After construction, call the instance to perform conversion::

        converter = Converter(logger, size=1000, image_format="png")
        converter(input_path, output_path)
    """

    @staticmethod
    def normalize_format(name: str) -> str:
        """Normalize a format name, resolving common aliases.

        >>> Converter.normalize_format("jpg")
        'jpeg'
        """
        name = name.lower()
        return FORMAT_ALIASES.get(name, name)

    
    def __init__(
        self,
        logger: Logger,
        *,
        size: int = DEFAULT_SIZE,
        image_format: str = DEFAULT_FORMAT,
        save_options: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the converter.

        Args:
            logger: Logger instance.
            size: Maximum long edge in pixels.
            image_format: Output format name (jpeg, png, webp, tiff).
            save_options: **Final** PIL save keyword arguments.
                When *None*, built-in defaults for *image_format* are used.
        """
        self._logger = logger
        self._image_format = self.normalize_format(image_format)
        self._size = size

        entry = FORMAT_MAP.get(self._image_format)
        if not entry:
            raise ValueError(
                f"Unsupported image format '{image_format}'. "
                f"Supported: {', '.join(sorted(FORMAT_MAP))}"
            )
        self._pil_format, self._file_extension = entry

        if save_options is not None:
            self._save_options = dict(save_options)
        else:
            self._save_options = dict(
                DEFAULT_FORMAT_OPTIONS.get(self._image_format, {})
            )

    
    def __call__(self, input_path: Path, output_path: Path) -> None:
        """Convert a source image to the configured format and size.

        Args:
            input_path: Path to the source image.
            output_path: Path for the output file.  Parent directories
                are created automatically.

        Raises:
            FileNotFoundError: If *input_path* does not exist.
        """
        if not input_path.exists():
            self._logger.error(f"Input file does not exist: {input_path}")
            raise FileNotFoundError(f"Input file does not exist: {input_path}")

        Image.MAX_IMAGE_PIXELS = None

        self._logger.debug(
            f"Converting {input_path} -> {output_path} "
            f"(format={self._pil_format}, size={self._size}, "
            f"options={self._save_options})"
        )

        with Image.open(input_path) as img:
            img.load()

            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            img.thumbnail((self._size, self._size), Image.Resampling.LANCZOS)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, format=self._pil_format, **self._save_options)
