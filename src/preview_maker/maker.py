"""
Core implementation for Preview Maker.

Provides utilities to generate preview JPEGs from source files whose
names match configurable glob patterns listed in priority order.

The primary API is exposed via the :class:`PreviewMaker` class, which is
configured with parameters and then executed via :meth:`__call__`.
"""

import fnmatch
import uuid
import datetime
from pathlib import Path

from common.logger import Logger
from common.formatter import Formatter
from common.constants import SUPPORTED_IMAGE_EXTENSIONS, MIME_TYPE_MAP, TAG_XMP_DC_IDENTIFIER, TAG_XMP_XMP_IDENTIFIER, TAG_XMP_DC_RELATION, TAG_XMP_DC_FORMAT, TAG_XMP_XMPMM_DOCUMENT_ID, TAG_XMP_XMPMM_INSTANCE_ID, TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID, TAG_XMP_XMPMM_DERIVED_FROM_INSTANCE_ID, XMP_ACTION_CONVERTED, XMP_ACTION_EDITED
from common.exifer import Exifer
from common.tagger import Tagger
from common.tags import KeyValueTag, HistoryTag
from common.router import Router
from common.version import get_version
from common.project_config import ProjectConfig
from preview_maker.config import Config
from preview_maker.constants import FORMAT_MAP
from preview_maker.converter import Converter


class PreviewMaker:
    """
    Preview generator that can be executed like a function.

    In line with other workflow-like classes (such as :class:`VuescanWorkflow`),
    a :class:`Logger` instance is provided at construction time, while
    call-specific parameters are passed to :meth:`__call__`.
    """

    def __init__(self, logger: Logger, config_path: str | Path | None = None, no_metadata: bool = False) -> None:
        self._logger = logger
        self._config = Config(logger, config_path)
        self._converter = Converter(
            logger,
            size=self._config.image_size,
            image_format=self._config.image_format,
            save_options=self._config.save_options,
        )

        cfg = ProjectConfig.instance()
        self._exifer = Exifer()
        self._formatter = Formatter(logger=logger, formats=cfg.formats)
        self._router = Router(routes=cfg.routes, logger=logger, formats=cfg.formats)
        self._no_metadata = no_metadata


    def __call__(
        self,
        *,
        path: Path,
        overwrite: bool = False,
    ) -> int:
        """
        Run batch preview generation under ``path``.

        This is the primary workflow-style entry point and mirrors how other
        workflow classes are executed.
        """

        return self._generate_previews_for_sources(
            path=path,
            overwrite=overwrite,
        )

    
    def should_process(self, file_path: Path) -> bool:
        """Check whether a file is eligible for preview generation.

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
        """Generate a preview for a single source file.

        This is the core per-file logic used by both batch and watch modes.
        The caller is responsible for filtering (see :meth:`should_process`).

        Args:
            src_path: Source file matching one of the ``source_priority`` patterns.
            archive_path: Resolved archive root for preview destination routing.
            overwrite: If True, regenerate existing previews.

        Returns:
            True if a preview was generated, False otherwise.
        """
        parsed = self._formatter.parse(src_path)
        if not parsed:
            raise ValueError(f"Cannot parse filename: {src_path.name}")

        # Verify that scan-batcher has registered this file before preview
        # generation. DocumentID/InstanceID are required for provenance metadata
        # in the derivative preview.
        tagger = Tagger(src_path, exifer=self._exifer)
        tagger.begin()
        tagger.read(KeyValueTag(TAG_XMP_XMPMM_DOCUMENT_ID))
        tagger.read(KeyValueTag(TAG_XMP_XMPMM_INSTANCE_ID))
        existing_ids = tagger.end() or {}
        if not existing_ids.get(TAG_XMP_XMPMM_DOCUMENT_ID) or not existing_ids.get(TAG_XMP_XMPMM_INSTANCE_ID):
            self._logger.warning(
                f"Skipping preview generation for {src_path.name}: missing DocumentID or InstanceID. "
                "These must be set by scan-batcher before processing."
            )
            raise ValueError(f"Missing DocumentID or InstanceID in {src_path.name}")

        # Build preview filename from configured template
        prv_filename = self._build_preview_filename(parsed)

        prv_dir = self._prv_dir(archive_path, src_path)
        prv_dir.mkdir(parents=True, exist_ok=True)
        prv_path = prv_dir / prv_filename

        if prv_path.exists() and not overwrite:
            # Even without overwrite, regenerate preview when the existing one
            # was derived from a different source (e.g. RAW → MSR upgrade).
            if self._should_upgrade_prv(prv_path, src_path):
                self._logger.info(f"Upgrading preview from higher-priority source: {prv_path}")
            else:
                self._logger.debug(f"Skipping existing preview (overwrite disabled): {prv_path}")
                return False

        self._logger.info(f"Creating preview: {src_path.name} -> {prv_path}")

        self._convert_to_prv(
            input_path=src_path,
            output_path=prv_path,
        )

        return True

    
    def _should_upgrade_prv(self, prv_path: Path, src_path: Path) -> bool:
        """Check whether an existing preview should be regenerated.

        Returns True when the preview's ``DerivedFromDocumentID`` does
        **not** match *src_path*'s ``DocumentID``, meaning the preview
        was created from a different source and should be upgraded.

        If either ID cannot be read (e.g. the preview has no metadata
        yet), returns False to avoid accidental overwrites.
        """
        try:
            tagger = Tagger(prv_path, exifer=self._exifer)
            tagger.begin()
            tagger.read(KeyValueTag(TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID))
            prv_tags = tagger.end() or {}

            tagger = Tagger(src_path, exifer=self._exifer)
            tagger.begin()
            tagger.read(KeyValueTag(TAG_XMP_XMPMM_DOCUMENT_ID))
            src_tags = tagger.end() or {}

            prv_derived_from = prv_tags.get(TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID)
            src_doc_id = src_tags.get(TAG_XMP_XMPMM_DOCUMENT_ID)

            if not prv_derived_from or not src_doc_id:
                return False

            return prv_derived_from != src_doc_id
        except Exception as exc:
            self._logger.debug(f"Cannot determine upgrade eligibility for {prv_path}: {exc}")
            return False

    
    def _generate_previews_for_sources(
        self,
        *,
        path: Path,
        overwrite: bool,
    ) -> int:
        """Walk under *path* and generate previews for matching source files."""

        written = 0

        self._logger.debug(f"Starting batch preview generation under {path} (overwrite={overwrite}, size={self._config.image_size}, format={self._config.image_format})")

        # Get folders where source files are stored according to routing rules
        target_folders = self._router.get_folders_for_patterns(self._config.source_priority)

        if not target_folders:
            self._logger.warning("No target folders found for source patterns in routing configuration")
            return 0

        self._logger.debug(f"Scanning for source files in folders: {target_folders}")

        archive_path = path

        # Scan only target folders (e.g., SOURCES/)
        for folder_name in target_folders:
            for dirpath in path.rglob(folder_name):
                if not dirpath.is_dir():
                    continue

                self._logger.info(f"Scanning for source files in: {dirpath}")

                for src_path in dirpath.iterdir():
                    if not src_path.is_file():
                        continue

                    if not self.should_process(src_path):
                        continue

                    try:
                        if self.process_single_file(
                            src_path,
                            archive_path=archive_path,
                            overwrite=overwrite,
                        ):
                            written += 1
                    except Exception as e:
                        self._logger.error(f"Error processing {src_path.name}: {e}")

        self._logger.info(f"Finished batch preview generation: {written} file(s) written")

        return written

    
    def _prv_dir(self, archive_path: Path, src_path: Path) -> Path:
        """Build the output preview directory path for a source file.

        Mirrors the archive path structure:
        scan/000001/2025/2025.06.01/file.tif
        → .system/scan/previews/000001/2025/2025.06.01/
        """
        rel = src_path.relative_to(archive_path)
        # rel.parts: ('scan', '000001', '2025', '2025.06.01', 'file.tif')
        # → .system/previews/scan/000001/2025/2025.06.01/
        return archive_path / ".system" / "previews" / Path(*rel.parts[:-1])

    def _build_preview_filename(self, parsed: dict[str, int | str]) -> str:
        """Build preview filename from configured template and parsed fields."""
        stem = self._formatter.format_template(parsed, self._config.template)
        return f"{stem}{FORMAT_MAP[self._config.image_format][1]}"

    
    def _get_match_priority(self, filename: str) -> int | None:
        """Return the priority index of the first matching source pattern.

        Returns *None* when the filename does not match any pattern.
        """
        for i, pattern in enumerate(self._config.source_priority):
            if fnmatch.fnmatch(filename.upper(), pattern.upper()):
                return i
        return None

    
    @staticmethod
    def _same_shot(a: dict[str, int | str], b: dict[str, int | str]) -> bool:
        """Check whether two parsed filenames represent the same shot.

        Compares all identity fields **except** suffix and extension.
        """
        return (
            a["year"] == b["year"]
            and a["month"] == b["month"]
            and a["day"] == b["day"]
            and a["hour"] == b["hour"]
            and a["minute"] == b["minute"]
            and a["second"] == b["second"]
            and a["modifier"] == b["modifier"]
            and a["group"] == b["group"]
            and a["subgroup"] == b["subgroup"]
            and a["sequence"] == b["sequence"]
            and a["side"] == b["side"]
        )

    
    def _convert_to_prv(
        self,
        *,
        input_path: Path,
        output_path: Path,
    ) -> None:
        """Convert a single source image to a preview.

        Delegates pixel conversion to :class:`Converter` and then
        optionally writes archival metadata to the output file.
        """

        self._converter(input_path, output_path)

        # After pixels are written, propagate archival metadata from source
        # to the preview derivative.
        if self._no_metadata:
            self._logger.info(f"Skipping metadata write for {output_path.name} (--no-metadata)")
        else:
            try:
                self._write_derivative_metadata(input_path, output_path)
            except (FileNotFoundError, RuntimeError, ValueError) as exc:
                # Treat metadata issues as errors in logs but keep the image.
                self._logger.error(f"Failed to copy metadata to preview {output_path}: {exc}")

        self._logger.info(f"Saved preview: {output_path}")

    
    def _write_derivative_metadata(self, master_path: Path, prv_path: Path) -> None:
        """Write EXIF/XMP metadata to preview derivative based on source.

        Copies ALL XMP and EXIF metadata from source to preview (format-agnostic
        tags), then overwrites derivative-specific tags (identifiers, DerivedFrom,
        Format) and adds XMP History entries — all in a single exiftool call.

        This ensures any new tags added by batcher or scanner automatically
        propagate to the preview without manual duplication.  IFD0/TIFF tags are
        excluded as they're TIFF-specific and don't transfer reliably to JPEG.

        Args:
            master_path: Path to the source file.
            prv_path: Path to the preview file.
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

        # single batch write to PRV
        self._logger.debug(f"Writing metadata to PRV {prv_path} based on master {master_path}")
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
            now = datetime.datetime.now().astimezone()

            # 'converted' — PRV file created from master via format conversion
            tagger.write(HistoryTag(
                action=XMP_ACTION_CONVERTED,
                when=now,
                software_agent=f"preview-maker {version}",
                instance_id=converted_instance_id,
            ))

            # 'edited' — metadata population from master
            tagger.write(HistoryTag(
                action=XMP_ACTION_EDITED,
                when=now,
                software_agent=f"preview-maker {version}",
                changed="metadata",
                instance_id=edited_instance_id,
            ))

        tagger.end()  # single exiftool call
