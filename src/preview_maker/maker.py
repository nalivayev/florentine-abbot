"""Core implementation for Preview Maker.

Provides utilities to generate PRV (preview) JPEGs from RAW/MSR sources.

The primary API is exposed via the :class:`PreviewMaker` class, which is
configured with parameters and then executed via :meth:`__call__`.
"""

from pathlib import Path

from PIL import Image

from common.logger import Logger
from common.naming import FilenameParser
from common.constants import SUPPORTED_IMAGE_EXTENSIONS
from common.archive_metadata import ArchiveMetadata
from common.router import Router


class PreviewMaker:
    """Preview generator that can be executed like a function.

    In line with other workflow-like classes (such as :class:`VuescanWorkflow`),
    a :class:`Logger` instance is provided at construction time, while
    call-specific parameters are passed to :meth:`__call__`.
    """

    def __init__(self, logger: Logger) -> None:
        self._logger = logger
        self._metadata = ArchiveMetadata()
        self._router = Router(logger=logger)

    def __call__(
        self,
        *,
        path: Path,
        overwrite: bool = False,
        max_size: int = 2000,
        quality: int = 80,
    ) -> int:
        """Run batch preview generation under ``path``.

        This is the primary workflow-style entry point and mirrors how other
        workflow classes are executed.
        """

        return self._generate_previews_for_sources(
            path=path,
            overwrite=overwrite,
            max_size=max_size,
            quality=quality,
        )

    def _generate_previews_for_sources(
        self,
        *,
        path: Path,
        overwrite: bool,
        max_size: int,
        quality: int,
    ) -> int:
        """Walk under ``path`` and generate PRV JPEGs for master files (RAW/MSR)."""

        parser = FilenameParser()
        written = 0

        self._logger.debug(
            "Starting batch preview generation under %s (overwrite=%s, max_size=%d, quality=%d)",
            path,
            overwrite,
            max_size,
            quality,
        )

    def _generate_previews_for_sources(
        self,
        *,
        path: Path,
        overwrite: bool,
        max_size: int,
        quality: int,
    ) -> int:
        """Walk under ``path`` and generate PRV JPEGs for master files (RAW/MSR)."""

        parser = FilenameParser()
        written = 0

        self._logger.debug(
            "Starting batch preview generation under %s (overwrite=%s, max_size=%d, quality=%d)",
            path,
            overwrite,
            max_size,
            quality,
        )

        # Get folders where RAW/MSR files are stored according to routing rules
        master_suffixes = ["RAW", "MSR"]
        target_folders = self._router.get_folders_for_suffixes(master_suffixes)
        
        if not target_folders:
            self._logger.warning("No target folders found for RAW/MSR files in routing configuration")
            return 0
        
        self._logger.debug(f"Scanning for master files in folders: {target_folders}")

        # Scan only target folders (e.g., SOURCES/)
        for folder_name in target_folders:
            for dirpath in path.rglob(folder_name):
                if not dirpath.is_dir():
                    continue

                self._logger.debug(f"Scanning {folder_name} directory: {dirpath}")

                for src_path in dirpath.iterdir():
                    if not src_path.is_file():
                        continue

                    # Only consider real image files as PRV sources; skip logs and
                    # other sidecar/auxiliary files that may share the same base
                    # name (e.g. *.RAW.log, *.icc).
                    if src_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
                        continue

                    parsed = parser.parse(src_path.name)
                    if not parsed:
                        continue

                    suffix = parsed.suffix.upper()
                    if suffix not in {"RAW", "MSR"}:
                        continue

                    if suffix == "RAW":
                        msr_name = src_path.name.replace(".RAW.", ".MSR.")
                        msr_candidate = src_path.with_name(msr_name)
                        if msr_candidate.exists():
                            # Prefer MSR when both RAW and MSR exist for the same base.
                            self._logger.debug(
                                "Skipping RAW in favour of MSR: %s (found %s)",
                                src_path,
                                msr_candidate,
                            )
                            continue

                    # Create PRV parsed filename by replacing suffix with PRV
                    from common.naming import ParsedFilename
                    prv_parsed = ParsedFilename(
                        year=parsed.year,
                        month=parsed.month,
                        day=parsed.day,
                        hour=parsed.hour,
                        minute=parsed.minute,
                        second=parsed.second,
                        modifier=parsed.modifier,
                        group=parsed.group,
                        subgroup=parsed.subgroup,
                        sequence=parsed.sequence,
                        side=parsed.side,
                        suffix="PRV",
                        extension="jpg"
                    )

                    # Determine base path for router: it's the parent of the year folder
                    # For file at /archive/2020/2020.01.15/SOURCES/file.tif, base is /archive/
                    # We need to find the year folder in the path and get its parent
                    year_str = f"{parsed.year:04d}"
                    try:
                        # Find year folder in path
                        parts = src_path.parts
                        year_index = parts.index(year_str)
                        base_path = Path(*parts[:year_index])
                    except (ValueError, IndexError):
                        # Fallback: use the input path parameter
                        self._logger.warning(f"Could not determine archive base for {src_path}, using input path")
                        base_path = path

                    # Use router to determine PRV output folder
                    prv_dir = self._router.get_target_folder(prv_parsed, base_path)
                    prv_filename = self._router.get_normalized_filename(prv_parsed) + ".jpg"
                    prv_path = prv_dir / prv_filename

                    if prv_path.exists() and not overwrite:
                        self._logger.debug("Skipping existing PRV (overwrite disabled): %s", prv_path)
                        continue

                    self._logger.debug("Creating PRV from %s to %s", src_path, prv_path)

                    self._convert_to_prv(
                        input_path=src_path,
                        output_path=prv_path,
                        max_size=max_size,
                        quality=quality,
                    )
                    written += 1

        self._logger.debug("Finished batch preview generation under %s: %d file(s) written", path, written)

        return written

    def _convert_to_prv(
        self,
        *,
        input_path: Path,
        output_path: Path,
        max_size: int,
        quality: int,
    ) -> None:
        """Convert a single source image to a PRV JPEG."""

        if not input_path.exists():
            self._logger.error("Input file does not exist: %s", input_path)
            raise FileNotFoundError(f"Input file does not exist: {input_path}")

        Image.MAX_IMAGE_PIXELS = None

        self._logger.debug(
            "Opening source image for PRV conversion: %s (max_size=%d, quality=%d)",
            input_path,
            max_size,
            quality,
        )

        with Image.open(input_path) as img:
            img.load()

            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, format="JPEG", quality=quality, optimize=True)

        # After pixels are written, propagate archival metadata from source
        # master (MSR/RAW) to the PRV derivative.
        try:
            self._metadata.write_derivative_tags(
                master_path=input_path,
                prv_path=output_path,
                logger=self._logger,
            )
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            # Treat metadata issues as errors in logs but keep the image.
            self._logger.error("Failed to copy metadata to PRV %s: %s", output_path, exc)

        self._logger.debug("PRV written to %s", output_path)
