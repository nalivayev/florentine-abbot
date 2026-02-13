"""Core implementation for Preview Maker.

Provides utilities to generate PRV (preview) JPEGs from RAW/MSR sources.

The primary API is exposed via the :class:`PreviewMaker` class, which is
configured with parameters and then executed via :meth:`__call__`.
"""

import uuid
import datetime
from pathlib import Path
from typing import Any

from PIL import Image

from common.logger import Logger
from common.naming import FilenameParser, ParsedFilename
from common.constants import SUPPORTED_IMAGE_EXTENSIONS, MIME_TYPE_MAP
from common.metadata import ArchiveMetadata, TAG_XMP_DC_IDENTIFIER, TAG_XMP_XMP_IDENTIFIER, TAG_XMP_DC_RELATION, TAG_XMP_EXIF_DATETIME_DIGITIZED, TAG_EXIFIFD_DATETIME_DIGITIZED, IDENTIFIER_TAGS, DATE_TAGS, TAG_XMP_DC_FORMAT
from common.exifer import Exifer
from common.router import Router
from common.historian import XMPHistorian, TAG_XMP_XMPMM_DOCUMENT_ID, TAG_XMP_XMPMM_INSTANCE_ID, TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID, TAG_XMP_XMPMM_DERIVED_FROM_INSTANCE_ID, XMP_ACTION_CONVERTED, XMP_ACTION_EDITED
from common.version import get_version


class PreviewMaker:
    """Preview generator that can be executed like a function.

    In line with other workflow-like classes (such as :class:`VuescanWorkflow`),
    a :class:`Logger` instance is provided at construction time, while
    call-specific parameters are passed to :meth:`__call__`.
    """

    def __init__(self, logger: Logger) -> None:
        self._logger = logger
        self._metadata = ArchiveMetadata(logger=logger)
        self._exifer = Exifer()
        self._router = Router(logger=logger)
        self._historian = XMPHistorian(exifer=self._exifer)

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

                self._logger.info(f"Scanning for master files in: {dirpath}")

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

                    # Determine archive base path:
                    # If path/processed exists, use it as the base (organizer puts files there)
                    # Otherwise use path itself (already organized archive)
                    processed_path = path / "processed"
                    base_path = processed_path if processed_path.exists() else path

                    # Use router to determine PRV output folder
                    prv_dir = self._router.get_target_folder(prv_parsed, base_path)
                    prv_filename = self._router.get_normalized_filename(prv_parsed) + ".jpg"
                    prv_path = prv_dir / prv_filename

                    if prv_path.exists() and not overwrite:
                        self._logger.debug("Skipping existing PRV (overwrite disabled): %s", prv_path)
                        continue

                    self._logger.info("Creating PRV: %s -> %s", src_path.name, prv_path)

                    try:
                        self._convert_to_prv(
                            input_path=src_path,
                            output_path=prv_path,
                            max_size=max_size,
                            quality=quality,
                        )
                        written += 1
                    except ValueError:
                        # Missing DocumentID/InstanceID - already logged, skip this file
                        continue

        self._logger.info("Finished batch preview generation: %d file(s) written", written)

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

        # Check for DocumentID/InstanceID in master (must be set by scan-batcher)
        existing_ids = self._exifer.read(input_path, [TAG_XMP_XMPMM_DOCUMENT_ID, TAG_XMP_XMPMM_INSTANCE_ID])
        if not existing_ids.get(TAG_XMP_XMPMM_DOCUMENT_ID) or not existing_ids.get(TAG_XMP_XMPMM_INSTANCE_ID):
            self._logger.warning(
                "Skipping PRV generation for %s: missing DocumentID or InstanceID. "
                "These must be set by scan-batcher before processing.",
                input_path.name,
            )
            raise ValueError(f"Missing DocumentID or InstanceID in {input_path.name}")

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
            self._write_derivative_metadata(input_path, output_path)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            # Treat metadata issues as errors in logs but keep the image.
            self._logger.error("Failed to copy metadata to PRV %s: %s", output_path, exc)

        self._logger.info("Saved PRV: %s", output_path)

    def _write_derivative_metadata(self, master_path: Path, prv_path: Path) -> None:
        """Write EXIF/XMP metadata to PRV derivative based on master.
        
        Args:
            master_path: Path to the master (MSR/RAW) file.
            prv_path: Path to the PRV file.
        """
        # Build list of base tags to read from master
        configurable_tags = self._metadata.get_configurable_tags()
        tags_to_read = list(IDENTIFIER_TAGS) + list(DATE_TAGS) + configurable_tags + [TAG_EXIFIFD_DATETIME_DIGITIZED]
        
        # Read all XMP tags from master (including language variants)
        # Use empty list to get ALL tags, then filter what we need
        all_tags = self._exifer.read(master_path, [])
        
        tags_to_write: dict[str, Any] = {}
        
        # 1. Fresh identifier for PRV
        prv_uuid = uuid.uuid4().hex
        tags_to_write[TAG_XMP_DC_IDENTIFIER] = prv_uuid
        tags_to_write[TAG_XMP_XMP_IDENTIFIER] = prv_uuid
        
        # 2. Relation to master
        master_id = all_tags.get(TAG_XMP_DC_IDENTIFIER) or all_tags.get(TAG_XMP_XMP_IDENTIFIER)
        if master_id:
            tags_to_write[TAG_XMP_DC_RELATION] = master_id
        
        # 3. Copy dates (with fallback for DateTimeDigitized)
        for tag in DATE_TAGS:
            value = all_tags.get(tag)
            if value is None and tag == TAG_XMP_EXIF_DATETIME_DIGITIZED:
                value = all_tags.get(TAG_EXIFIFD_DATETIME_DIGITIZED)
            if value is not None:
                tags_to_write[tag] = value
        
        # 4. Copy configurable tags and their language variants
        for tag in configurable_tags:
            # Copy base tag
            value = all_tags.get(tag)
            if value is not None:
                tags_to_write[tag] = value
            
            # Copy language variants (TAG-langCode format)
            for tag_name, tag_value in all_tags.items():
                if tag_name.startswith(tag + "-") and tag_value is not None:
                    tags_to_write[tag_name] = tag_value
        
        # 5. DocumentID from master, fresh InstanceID for derivative
        master_document_id = all_tags.get(TAG_XMP_XMPMM_DOCUMENT_ID)
        if master_document_id:
            tags_to_write[TAG_XMP_XMPMM_DOCUMENT_ID] = master_document_id
        
        prv_instance_id = uuid.uuid4().hex
        tags_to_write[TAG_XMP_XMPMM_INSTANCE_ID] = prv_instance_id
        
        # 6. dc:Format based on PRV file extension (only if known MIME type)
        prv_extension = prv_path.suffix.lower().lstrip('.')
        dc_format = MIME_TYPE_MAP.get(prv_extension)
        if dc_format:
            tags_to_write[TAG_XMP_DC_FORMAT] = dc_format
        
        # 6.1. xmpMM:DerivedFrom structure pointing to master
        master_instance_id = all_tags.get(TAG_XMP_XMPMM_INSTANCE_ID)
        if master_document_id:
            tags_to_write[TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID] = master_document_id
        if master_instance_id:
            tags_to_write[TAG_XMP_XMPMM_DERIVED_FROM_INSTANCE_ID] = master_instance_id
        
        # 7. Write all tags to PRV
        if tags_to_write:
            self._logger.debug("Writing metadata to PRV %s based on master %s", prv_path, master_path)
            self._exifer.write(prv_path, tags_to_write)
        
        # 8. Write XMP History entries for PRV creation (like VuescanWorkflow)
        if master_document_id:
            version = get_version()
            major_version = "0.0" if version == "unknown" else ".".join(version.split(".")[:2])
            now = datetime.datetime.now().astimezone()
            
            # First entry: 'converted' - PRV file created from master via format conversion
            self._historian.append_entry(
                file_path=prv_path,
                action=XMP_ACTION_CONVERTED,
                software_agent=f"preview-maker {major_version}",
                when=now,
                instance_id=prv_instance_id,
                logger=self._logger,
            )
            
            # Second entry: 'edited' - metadata population from master
            self._historian.append_entry(
                file_path=prv_path,
                action=XMP_ACTION_EDITED,
                software_agent=f"preview-maker {major_version}",
                when=now,
                changed="metadata",
                instance_id=prv_instance_id,
                logger=self._logger,
            )
