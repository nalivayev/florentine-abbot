from abc import ABC, abstractmethod
from pathlib import Path
import datetime
import uuid

from common.exifer import Exifer
from common.tagger import Tagger
from common.tags import KeyValueTag, HistoryTag
from common.logger import Logger
from common.version import get_version
from common.constants import (
    EXIFTOOL_LARGE_FILE_TIMEOUT,
    MIME_TYPE_MAP,
    TAG_XMP_XMPMM_DOCUMENT_ID,
    TAG_XMP_XMPMM_INSTANCE_ID,
    XMP_ACTION_CREATED,
    XMP_ACTION_EDITED,
    TAG_XMP_DC_FORMAT,
    TAG_XMP_EXIF_DATETIME_DIGITIZED,
    TAG_EXIFIFD_DATETIME_DIGITIZED,
    TAG_EXIFIFD_CREATE_DATE,
    TAG_EXIF_OFFSET_TIME_DIGITIZED,
    TAG_IFD0_DATETIME,
    TAG_IFD0_MAKE,
    TAG_IFD0_MODEL,
    TAG_IFD0_SOFTWARE,
    TAG_XMP_TIFF_MAKE,
    TAG_XMP_TIFF_MODEL,
    TAG_XMP_TIFF_SOFTWARE,
    TAG_XMP_XMP_CREATOR_TOOL,
)
from scan_batcher.constants import EXIF_DATETIME_FORMAT, EXIF_DATETIME_FORMAT_MS


class Workflow(ABC):
    """
    Abstract base class for all workflow plugins.
    All workflow classes must inherit from this class and implement the __call__ method.
    """

    def __init__(self, logger: Logger | None = None, no_metadata: bool = False) -> None:
        """Initialize the workflow.
        
        Args:
            logger: Optional logger instance for subclasses that need it.
            no_metadata: If True, skip writing EXIF/XMP metadata.
        """
        pass

    @abstractmethod
    def __call__(self, workflow_path: str, templates: dict[str, str]) -> None:
        """
        Execute the workflow.

        Args:
            workflow_path: Path to the workflow configuration directory.
            templates: Dictionary of template values.

        Raises:
            RuntimeError: For workflow-specific errors.
        """
        pass


class MetadataWorkflow(Workflow):
    """
    Base workflow that provides XMP metadata writing functionality.
    
    Subclasses should implement the __call__ method and use _write_xmp_history
    to write DocumentID, InstanceID and XMP history entries to files.
    """

    # EXIF tag names for reading date information
    _EXIF_DATE_TAGS = [
        TAG_EXIFIFD_DATETIME_DIGITIZED,
        TAG_EXIFIFD_CREATE_DATE,
        TAG_IFD0_DATETIME,
    ]

    # Image extensions that support EXIF metadata (lowercase).
    _EXIF_SUPPORTED_EXTENSIONS = {".tif", ".tiff", ".jpg", ".jpeg"}

    def __init__(self, logger: Logger, no_metadata: bool = False) -> None:
        """
        Initialize the metadata workflow.
        
        Args:
            logger: Logger instance for this workflow.
            no_metadata: If True, skip writing EXIF/XMP metadata.
        """
        super().__init__(logger)
        self._logger = logger
        self._exifer = Exifer()
        self._no_metadata = no_metadata

    def _get_major_version(self) -> str:
        """
        Get major version number from package version.
        
        Returns:
            Major version string (e.g., "1.0" from "1.0.5").
        """
        version = get_version()
        if version == "unknown":
            return "0.0"
        parts = version.split(".")
        if len(parts) >= 2:
            return f"{parts[0]}.{parts[1]}"
        return version

    def _get_digitized_datetime(self, file_path: Path) -> datetime.datetime:
        """
        Extract datetime from file EXIF or use file modification time.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Datetime extracted from EXIF or file modification time (in local timezone).
        """
        from os.path import getmtime
        
        moment = None
        if file_path.suffix.lower() in self._EXIF_SUPPORTED_EXTENSIONS:
            try:
                tagger = Tagger(file_path, exifer=self._exifer)
                tagger.begin()
                for tag_name in self._EXIF_DATE_TAGS:
                    tagger.read(KeyValueTag(tag_name))
                tags = tagger.end() or {}
                
                # Try to get date from any of the tags (in priority order)
                for tag_name in self._EXIF_DATE_TAGS:
                    value = tags.get(tag_name)
                    if value:
                        try:
                            # Try with fractional seconds first, then without
                            for fmt in (EXIF_DATETIME_FORMAT_MS, EXIF_DATETIME_FORMAT):
                                try:
                                    naive_moment = datetime.datetime.strptime(value, fmt)
                                    break
                                except ValueError:
                                    continue
                            else:
                                continue
                            # Localize naive datetime to local timezone
                            moment = naive_moment.replace(tzinfo=datetime.datetime.now().astimezone().tzinfo)
                            break
                        except ValueError:
                            pass
            except Exception as e:
                self._logger.warning(f"Unable to extract EXIF from file '{file_path.name}': {e}")

        if moment is None:
            # Get file modification time in local timezone
            moment = datetime.datetime.fromtimestamp(getmtime(file_path)).astimezone()

        return moment

    def _write_xmp_history(
        self,
        file_path: Path,
        file_datetime: datetime.datetime,
    ) -> bool:
        """
        Write XMP metadata: DocumentID/InstanceID, DateTimeDigitized, and History entries.
        
        Ensures proper metadata is set on the file:
        - DocumentID and InstanceID (generated if missing)
        - dc:Format (MIME type from extension)
        - XMP-exif:DateTimeDigitized (written or enriched with timezone if missing)
        - Exif:OffsetTimeDigitized (written if missing and timezone available)
        - XMP History: 'created' + 'edited' entries
        
        When DateTimeDigitized already exists (e.g. written by VueScan) but lacks
        timezone information, it is enriched with the timezone from file_datetime.
        This ensures consistent ISO 8601 format across all files.
        
        Both History entries use "scan-batcher X.Y" as the software agent,
        since scan-batcher is the tool that writes all XMP tags. Scanner
        software info (e.g. VueScan) is already preserved in IFD0:Software.
        
        Args:
            file_path: Path to the file to write metadata to.
            file_datetime: Datetime for the history entries (with timezone).
        
        Returns:
            True if successful, False otherwise.
        """
        if self._no_metadata:
            self._logger.info(f"Skipping metadata write for {file_path.name} (--no-metadata)")
            return True

        if not file_path.exists():
            self._logger.warning(f"Cannot write XMP history: file doesn't exist: {file_path}")
            return False

        # Log file size for large files
        file_size = file_path.stat().st_size
        if file_size > 100 * 1024 * 1024:  # > 100MB
            self._logger.info(
                f"Writing XMP history to large file ({file_size / (1024**2):.1f} MB): {file_path.name}"
            )

        try:
            tagger = Tagger(
                file_path, exifer=self._exifer, timeout=EXIFTOOL_LARGE_FILE_TIMEOUT,
            )

            # ── batch-read existing tags ──────────────────────────────
            self._logger.debug(f"Reading existing XMP tags from {file_path.name}...")
            tagger.begin()
            for tag in (
                TAG_XMP_XMPMM_DOCUMENT_ID,
                TAG_XMP_XMPMM_INSTANCE_ID,
                TAG_XMP_EXIF_DATETIME_DIGITIZED,
                TAG_EXIFIFD_DATETIME_DIGITIZED,
                TAG_EXIF_OFFSET_TIME_DIGITIZED,
                TAG_IFD0_MAKE,
                TAG_IFD0_MODEL,
                TAG_IFD0_SOFTWARE,
            ):
                tagger.read(KeyValueTag(tag))
            existing_tags = tagger.end() or {}

            # ── prepare values ────────────────────────────────────────

            # Get or generate DocumentID (without dashes)
            document_id = existing_tags.get(TAG_XMP_XMPMM_DOCUMENT_ID)
            if not document_id:
                document_id = uuid.uuid4().hex
                self._logger.debug(f"Generated new DocumentID: {document_id}")
            else:
                self._logger.debug(f"Using existing DocumentID: {document_id}")

            # InstanceID for the "created" event (file creation by scanner)
            created_instance_id = existing_tags.get(TAG_XMP_XMPMM_INSTANCE_ID)
            if not created_instance_id:
                created_instance_id = uuid.uuid4().hex
                self._logger.debug(f"Generated InstanceID for 'created': {created_instance_id}")
            else:
                self._logger.debug(f"Using existing InstanceID for 'created': {created_instance_id}")

            # InstanceID for the "edited" event (metadata write by scan-batcher)
            edited_instance_id = uuid.uuid4().hex
            self._logger.debug(f"Generated InstanceID for 'edited': {edited_instance_id}")

            # ── batch-write all tags + history in one call ────────────
            self._logger.debug(f"Writing metadata to {file_path.name}...")
            tagger.begin()

            tagger.write(KeyValueTag(TAG_XMP_XMPMM_DOCUMENT_ID, document_id))
            tagger.write(KeyValueTag(TAG_XMP_XMPMM_INSTANCE_ID, edited_instance_id))

            # dc:Format from extension map
            file_extension = file_path.suffix.lower().lstrip('.')
            dc_format = MIME_TYPE_MAP.get(file_extension)
            if dc_format:
                tagger.write(KeyValueTag(TAG_XMP_DC_FORMAT, dc_format))

            # Handle DateTimeDigitized: write new or enrich existing with timezone
            date_digitized = (
                existing_tags.get(TAG_XMP_EXIF_DATETIME_DIGITIZED)
                or existing_tags.get(TAG_EXIFIFD_DATETIME_DIGITIZED)
            )

            if not date_digitized:
                dt_str = file_datetime.isoformat(timespec='milliseconds')
                tagger.write(KeyValueTag(TAG_XMP_EXIF_DATETIME_DIGITIZED, dt_str))
                self._logger.debug(f"Writing DateTimeDigitized: {dt_str}")
            elif "+" not in date_digitized and "-" not in date_digitized[10:]:
                dt_str = file_datetime.isoformat(timespec='milliseconds')
                tagger.write(KeyValueTag(TAG_XMP_EXIF_DATETIME_DIGITIZED, dt_str))
                self._logger.debug(
                    f"Enriching DateTimeDigitized with timezone: {date_digitized} -> {dt_str}"
                )
            else:
                self._logger.debug(f"DateTimeDigitized already has timezone: {date_digitized}")

            # OffsetTimeDigitized
            offset_time_digitized = existing_tags.get(TAG_EXIF_OFFSET_TIME_DIGITIZED)

            if not offset_time_digitized and file_datetime.tzinfo is not None:
                offset = file_datetime.strftime("%z")
                if offset:
                    offset_formatted = f"{offset[:3]}:{offset[3:]}"
                    tagger.write(KeyValueTag(TAG_EXIF_OFFSET_TIME_DIGITIZED, offset_formatted))
                    self._logger.debug(f"Writing OffsetTimeDigitized: {offset_formatted}")
            elif offset_time_digitized:
                self._logger.debug(f"OffsetTimeDigitized already set: {offset_time_digitized}")

            # Copy IFD0:Make/Model → XMP-tiff:Make/Model
            ifd0_make = existing_tags.get(TAG_IFD0_MAKE)
            ifd0_model = existing_tags.get(TAG_IFD0_MODEL)

            if ifd0_make:
                tagger.write(KeyValueTag(TAG_XMP_TIFF_MAKE, ifd0_make))
                self._logger.debug(f"Copying Make to XMP: {ifd0_make}")

            if ifd0_model:
                tagger.write(KeyValueTag(TAG_XMP_TIFF_MODEL, ifd0_model))
                self._logger.debug(f"Copying Model to XMP: {ifd0_model}")

            # Copy IFD0:Software → XMP-xmp:CreatorTool + XMP-tiff:Software
            ifd0_software = existing_tags.get(TAG_IFD0_SOFTWARE)
            if ifd0_software:
                tagger.write(KeyValueTag(TAG_XMP_XMP_CREATOR_TOOL, ifd0_software))
                tagger.write(KeyValueTag(TAG_XMP_TIFF_SOFTWARE, ifd0_software))
                self._logger.debug(f"Copying Software to XMP: {ifd0_software}")

            # XMP History entries
            agent = f"scan-batcher {self._get_major_version()}"

            tagger.write(HistoryTag(
                action=XMP_ACTION_CREATED,
                when=file_datetime,
                software_agent=agent,
                instance_id=created_instance_id,
            ))

            tagger.write(HistoryTag(
                action=XMP_ACTION_EDITED,
                when=file_datetime,
                software_agent=agent,
                changed="metadata",
                instance_id=edited_instance_id,
            ))

            tagger.end()  # single exiftool call for all writes

            self._logger.info(f"XMP history written for {file_path.name}")
            return True

        except Exception as e:
            self._logger.warning(f"Failed to write XMP history: {e}")
            return False
