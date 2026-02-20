"""
Core implementation for Preview Maker.

Provides utilities to generate PRV (preview) JPEGs from RAW/MSR sources.

The primary API is exposed via the :class:`PreviewMaker` class, which is
configured with parameters and then executed via :meth:`__call__`.
"""

import uuid
import datetime
from pathlib import Path
from PIL import Image

from common.logger import Logger
from common.naming import FilenameParser, ParsedFilename
from common.constants import SUPPORTED_IMAGE_EXTENSIONS, MIME_TYPE_MAP, TAG_XMP_DC_IDENTIFIER, TAG_XMP_XMP_IDENTIFIER, TAG_XMP_DC_RELATION, TAG_XMP_DC_FORMAT, TAG_XMP_XMPMM_DOCUMENT_ID, TAG_XMP_XMPMM_INSTANCE_ID, TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID, TAG_XMP_XMPMM_DERIVED_FROM_INSTANCE_ID, XMP_ACTION_CONVERTED, XMP_ACTION_EDITED
from common.metadata import ArchiveMetadata
from common.exifer import Exifer
from common.tagger import Tagger
from common.tags import KeyValueTag, HistoryTag
from common.router import Router
from common.version import get_version


class PreviewMaker:
    """
    Preview generator that can be executed like a function.

    In line with other workflow-like classes (such as :class:`VuescanWorkflow`),
    a :class:`Logger` instance is provided at construction time, while
    call-specific parameters are passed to :meth:`__call__`.
    """

    def __init__(self, logger: Logger) -> None:
        self._logger = logger
        self._metadata = ArchiveMetadata(logger=logger)
        self._exifer = Exifer()
        self._parser = FilenameParser()
        self._router = Router(logger=logger)

    def __call__(
        self,
        *,
        path: Path,
        overwrite: bool = False,
        max_size: int = 2000,
        quality: int = 80,
    ) -> int:
        """
        Run batch preview generation under ``path``.

        This is the primary workflow-style entry point and mirrors how other
        workflow classes are executed.
        """

        return self._generate_previews_for_sources(
            path=path,
            overwrite=overwrite,
            max_size=max_size,
            quality=quality,
        )

    def should_process(self, file_path: Path) -> bool:
        """Check whether a file is a master image eligible for PRV generation.

        Checks:
        - Not a symlink
        - Has a supported image extension
        - Filename parses to a RAW or MSR suffix
        - If RAW, no MSR sibling exists (MSR is preferred)

        Args:
            file_path: Path to the candidate file.

        Returns:
            True if the file should be processed, False otherwise.
        """
        if file_path.is_symlink():
            self._logger.debug("Skipping %s: is symlink", file_path)
            return False

        if file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            self._logger.debug("Skipping %s: unsupported extension '%s'", file_path, file_path.suffix)
            return False

        parsed = self._parser.parse(file_path.name)
        if not parsed:
            self._logger.debug("Skipping %s: cannot parse filename", file_path)
            return False

        suffix = parsed.suffix.upper()
        if suffix not in {"RAW", "MSR"}:
            self._logger.debug("Skipping %s: suffix %s is not RAW/MSR", file_path, suffix)
            return False

        if suffix == "RAW":
            msr_name = file_path.name.replace(".RAW.", ".MSR.")
            msr_candidate = file_path.with_name(msr_name)
            if msr_candidate.exists():
                self._logger.debug(
                    "Skipping RAW in favour of MSR: %s (found %s)",
                    file_path, msr_candidate,
                )
                return False

        return True

    def process_single_file(
        self,
        src_path: Path,
        *,
        archive_path: Path,
        overwrite: bool = False,
        max_size: int = 2000,
        quality: int = 80,
    ) -> bool:
        """Generate a PRV preview for a single master file.

        This is the core per-file logic used by both batch and watch modes.
        The caller is responsible for filtering (see :meth:`should_process`).

        Args:
            src_path: Source master file (RAW or MSR).
            archive_path: Resolved archive root for PRV destination routing.
            overwrite: If True, regenerate existing PRV files.
            max_size: Maximum long edge in pixels.
            quality: JPEG quality (1-100).

        Returns:
            True if a PRV was generated, False otherwise.
        """
        parsed = self._parser.parse(src_path.name)
        if not parsed:
            self._logger.warning("Cannot parse filename: %s", src_path.name)
            return False

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
            extension="jpg",
        )

        # Use router to determine PRV output folder
        prv_dir = self._router.get_target_folder(prv_parsed, archive_path)
        prv_filename = self._router.get_normalized_filename(prv_parsed) + ".jpg"
        prv_path = prv_dir / prv_filename

        if prv_path.exists() and not overwrite:
            # Even without overwrite, regenerate PRV when a better master
            # appears.  If the source is MSR and the existing PRV was
            # derived from a different master (e.g. RAW), upgrade it.
            if parsed.suffix.upper() == "MSR" and self._should_upgrade_prv(prv_path, src_path):
                self._logger.info(
                    "Upgrading PRV from MSR (was derived from RAW): %s",
                    prv_path,
                )
            else:
                self._logger.debug("Skipping existing PRV (overwrite disabled): %s", prv_path)
                return False

        self._logger.info("Creating PRV: %s -> %s", src_path.name, prv_path)

        try:
            self._convert_to_prv(
                input_path=src_path,
                output_path=prv_path,
                max_size=max_size,
                quality=quality,
            )
            return True
        except ValueError:
            # Missing DocumentID/InstanceID — already logged by _convert_to_prv
            return False

    def _should_upgrade_prv(self, prv_path: Path, msr_path: Path) -> bool:
        """Check whether an existing PRV should be regenerated from MSR.

        Returns True when the PRV's ``DerivedFromDocumentID`` does **not**
        match the MSR's ``DocumentID``, meaning the PRV was created from a
        different master (typically RAW) and should be upgraded.

        If either ID cannot be read (e.g. the PRV has no metadata yet),
        returns False to avoid accidental overwrites.
        """
        try:
            tagger = Tagger(prv_path, exifer=self._exifer)
            tagger.begin()
            tagger.read(KeyValueTag(TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID))
            prv_tags = tagger.end() or {}

            tagger = Tagger(msr_path, exifer=self._exifer)
            tagger.begin()
            tagger.read(KeyValueTag(TAG_XMP_XMPMM_DOCUMENT_ID))
            msr_tags = tagger.end() or {}

            prv_derived_from = prv_tags.get(TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID)
            msr_doc_id = msr_tags.get(TAG_XMP_XMPMM_DOCUMENT_ID)

            if not prv_derived_from or not msr_doc_id:
                return False

            return prv_derived_from != msr_doc_id
        except Exception as exc:
            self._logger.debug(
                "Cannot determine upgrade eligibility for %s: %s",
                prv_path, exc,
            )
            return False

    def _generate_previews_for_sources(
        self,
        *,
        path: Path,
        overwrite: bool,
        max_size: int,
        quality: int,
    ) -> int:
        """
        Walk under ``path`` and generate PRV JPEGs for master files (RAW/MSR).
        """

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

        self._logger.debug("Scanning for master files in folders: %s", target_folders)

        # Determine archive base path:
        # If path/processed exists, use it as the base (legacy organizer layout)
        # Otherwise use path itself (already organized archive)
        processed_path = path / "processed"
        archive_path = processed_path if processed_path.exists() else path

        # Scan only target folders (e.g., SOURCES/)
        for folder_name in target_folders:
            for dirpath in path.rglob(folder_name):
                if not dirpath.is_dir():
                    continue

                self._logger.info("Scanning for master files in: %s", dirpath)

                for src_path in dirpath.iterdir():
                    if not src_path.is_file():
                        continue

                    if not self.should_process(src_path):
                        continue

                    if self.process_single_file(
                        src_path,
                        archive_path=archive_path,
                        overwrite=overwrite,
                        max_size=max_size,
                        quality=quality,
                    ):
                        written += 1

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
        """
        Convert a single source image to a PRV JPEG.
        """

        if not input_path.exists():
            self._logger.error("Input file does not exist: %s", input_path)
            raise FileNotFoundError(f"Input file does not exist: {input_path}")

        # Check for DocumentID/InstanceID in master (must be set by scan-batcher)
        tagger = Tagger(input_path, exifer=self._exifer)
        tagger.begin()
        tagger.read(KeyValueTag(TAG_XMP_XMPMM_DOCUMENT_ID))
        tagger.read(KeyValueTag(TAG_XMP_XMPMM_INSTANCE_ID))
        existing_ids = tagger.end() or {}
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
        """
        Write EXIF/XMP metadata to PRV derivative based on master.
        
        Copies ALL XMP and EXIF metadata from master to PRV (format-agnostic tags),
        then overwrites derivative-specific tags (identifiers, DerivedFrom, Format)
        and adds XMP History entries — all in a single exiftool call.
        
        This ensures any new tags added by batcher or scanner automatically propagate
        to PRV without manual duplication. IFD0/TIFF tags are excluded as they're
        TIFF-specific and don't transfer reliably to JPEG format.
        
        Args:
            master_path: Path to the master (MSR/RAW) file.
            prv_path: Path to the PRV file.
        """
        # Read all XMP and EXIF tags from master, excluding History and
        # XMP-xmp:Identifier (bag type — exiftool accumulates instead of
        # replacing, so we exclude it and write a fresh value below).
        tags_from_master = self._exifer.read(
            master_path, 
            [],
            exclude_patterns=["XMP-xmpMM:History", "XMP-xmp:Identifier"],
            include_patterns=["XMP-", "XMP:", "EXIF:", "ExifIFD:"]
        )
        
        # Save master's identifiers before overwriting
        master_id = tags_from_master.get(TAG_XMP_DC_IDENTIFIER) or tags_from_master.get(TAG_XMP_XMP_IDENTIFIER)
        master_document_id = tags_from_master.get(TAG_XMP_XMPMM_DOCUMENT_ID)
        master_instance_id = tags_from_master.get(TAG_XMP_XMPMM_INSTANCE_ID)
        
        # Fresh InstanceIDs for derivative
        # Two modifications happen:
        #   1. Format conversion (PIL creates JPEG from master) → converted_instance_id
        #   2. Metadata write (this exiftool call) → edited_instance_id
        converted_instance_id = uuid.uuid4().hex
        edited_instance_id = uuid.uuid4().hex

        # ── single batch write to PRV ─────────────────────────────────
        self._logger.debug("Writing metadata to PRV %s based on master %s", prv_path, master_path)
        tagger = Tagger(prv_path, exifer=self._exifer)
        tagger.begin()

        # Write all master tags (these become the baseline)
        for tag, value in tags_from_master.items():
            tagger.write(KeyValueTag(tag, value))

        # Overwrite derivative-specific tags:
        
        # 1. Fresh identifier for PRV
        prv_uuid = uuid.uuid4().hex
        tagger.write(KeyValueTag(TAG_XMP_DC_IDENTIFIER, prv_uuid))
        tagger.write(KeyValueTag(TAG_XMP_XMP_IDENTIFIER, prv_uuid))
        
        # 2. Relation to master
        if master_id:
            tagger.write(KeyValueTag(TAG_XMP_DC_RELATION, master_id))
        
        # 3. Fresh InstanceID (DocumentID stays same)
        tagger.write(KeyValueTag(TAG_XMP_XMPMM_INSTANCE_ID, edited_instance_id))
        
        # 4. dc:Format based on PRV file extension
        prv_extension = prv_path.suffix.lower().lstrip('.')
        dc_format = MIME_TYPE_MAP.get(prv_extension)
        if dc_format:
            tagger.write(KeyValueTag(TAG_XMP_DC_FORMAT, dc_format))
        
        # 5. DerivedFrom structure pointing to master
        if master_document_id:
            tagger.write(KeyValueTag(TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID, master_document_id))
        if master_instance_id:
            tagger.write(KeyValueTag(TAG_XMP_XMPMM_DERIVED_FROM_INSTANCE_ID, master_instance_id))

        # 6. XMP History entries
        if master_document_id:
            version = get_version()
            major_version = "0.0" if version == "unknown" else ".".join(version.split(".")[:2])
            now = datetime.datetime.now().astimezone()

            # 'converted' — PRV file created from master via format conversion
            tagger.write(HistoryTag(
                action=XMP_ACTION_CONVERTED,
                when=now,
                software_agent=f"preview-maker {major_version}",
                instance_id=converted_instance_id,
            ))

            # 'edited' — metadata population from master
            tagger.write(HistoryTag(
                action=XMP_ACTION_EDITED,
                when=now,
                software_agent=f"preview-maker {major_version}",
                changed="metadata",
                instance_id=edited_instance_id,
            ))

        tagger.end()  # single exiftool call
