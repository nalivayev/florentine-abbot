from abc import ABC, abstractmethod
from pathlib import Path
import datetime
import uuid

from common.exifer import Exifer
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
    TAG_EXIF_OFFSET_TIME_DIGITIZED,
    TAG_IFD0_MAKE,
    TAG_IFD0_MODEL,
    TAG_XMP_TIFF_MAKE,
    TAG_XMP_TIFF_MODEL,
)
from common.historian import XMPHistorian
from scan_batcher.constants import EXIF_DATETIME_FORMAT, EXIF_DATETIME_FORMAT_MS


class Workflow(ABC):
    """
    Abstract base class for all workflow plugins.
    All workflow classes must inherit from this class and implement the __call__ method.
    """

    def __init__(self, logger: Logger | None = None) -> None:
        """Initialize the workflow.
        
        Args:
            logger: Optional logger instance for subclasses that need it.
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
        "ExifIFD:DateTimeDigitized",
        "ExifIFD:CreateDate",
        "IFD0:DateTime",
    ]

    # Image extensions that support EXIF metadata (lowercase).
    _EXIF_SUPPORTED_EXTENSIONS = {".tif", ".tiff", ".jpg", ".jpeg"}

    def __init__(self, logger: Logger) -> None:
        """Initialize the metadata workflow.
        
        Args:
            logger: Logger instance for this workflow.
        """
        super().__init__(logger)
        self._logger = logger
        self._exifer = Exifer()
        self._historian = XMPHistorian(exifer=self._exifer)

    def _get_major_version(self) -> str:
        """Get major version number from package version.
        
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
        """Extract datetime from file EXIF or use file modification time.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Datetime extracted from EXIF or file modification time (in local timezone).
        """
        from os.path import getmtime
        
        moment = None
        if file_path.suffix.lower() in self._EXIF_SUPPORTED_EXTENSIONS:
            try:
                tags = self._exifer.read(file_path, self._EXIF_DATE_TAGS)
                
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
            # Read existing DocumentID, InstanceID, Software, DateTimeDigitized, and Make/Model
            self._logger.debug(f"Reading existing XMP tags from {file_path.name}...")
            existing_tags = self._exifer.read(file_path, [
                TAG_XMP_XMPMM_DOCUMENT_ID,
                TAG_XMP_XMPMM_INSTANCE_ID,
                TAG_XMP_EXIF_DATETIME_DIGITIZED,
                TAG_EXIFIFD_DATETIME_DIGITIZED,
                TAG_EXIF_OFFSET_TIME_DIGITIZED,
                TAG_IFD0_MAKE,
                TAG_IFD0_MODEL,
            ])

            # Get or generate DocumentID (without dashes)
            document_id = existing_tags.get(TAG_XMP_XMPMM_DOCUMENT_ID)
            if not document_id:
                document_id = uuid.uuid4().hex
                self._logger.debug(f"Generated new DocumentID: {document_id}")
            else:
                self._logger.debug(f"Using existing DocumentID: {document_id}")

            # Get or generate InstanceID (without dashes)
            instance_id = existing_tags.get(TAG_XMP_XMPMM_INSTANCE_ID)
            if not instance_id:
                instance_id = uuid.uuid4().hex
                self._logger.debug(f"Generated new InstanceID: {instance_id}")
            else:
                self._logger.debug(f"Using existing InstanceID: {instance_id}")

            # Write DocumentID and InstanceID to file
            self._logger.debug(f"Writing DocumentID and InstanceID to {file_path.name}...")
            
            # Get MIME type for dc:Format from extension map
            file_extension = file_path.suffix.lower().lstrip('.')
            dc_format = MIME_TYPE_MAP.get(file_extension)
            
            tags_to_write = {
                TAG_XMP_XMPMM_DOCUMENT_ID: document_id,
                TAG_XMP_XMPMM_INSTANCE_ID: instance_id,
            }
            if dc_format:
                tags_to_write[TAG_XMP_DC_FORMAT] = dc_format
            
            # Handle DateTimeDigitized: write new or enrich existing with timezone
            date_digitized = (
                existing_tags.get(TAG_XMP_EXIF_DATETIME_DIGITIZED)
                or existing_tags.get(TAG_EXIFIFD_DATETIME_DIGITIZED)
            )
            
            if not date_digitized:
                # No DateTimeDigitized at all — write full ISO 8601 with timezone
                dt_str = file_datetime.isoformat(timespec='milliseconds')
                tags_to_write[TAG_XMP_EXIF_DATETIME_DIGITIZED] = dt_str
                self._logger.debug(f"Writing DateTimeDigitized: {dt_str}")
            elif "+" not in date_digitized and "-" not in date_digitized[10:]:
                # DateTimeDigitized exists but lacks timezone info (e.g. VueScan writes
                # "2026:02:18 14:30:00" without TZ). Enrich with timezone from file_datetime
                # by writing XMP-exif:DateTimeDigitized in full ISO 8601 format.
                dt_str = file_datetime.isoformat(timespec='milliseconds')
                tags_to_write[TAG_XMP_EXIF_DATETIME_DIGITIZED] = dt_str
                self._logger.debug(f"Enriching DateTimeDigitized with timezone: {date_digitized} -> {dt_str}")
            else:
                self._logger.debug(f"DateTimeDigitized already has timezone: {date_digitized}")
            
            # Write OffsetTimeDigitized if not already set and timezone info is available
            offset_time_digitized = existing_tags.get(TAG_EXIF_OFFSET_TIME_DIGITIZED)
            
            if not offset_time_digitized and file_datetime.tzinfo is not None:
                # Format: ±HH:MM (e.g., "+03:00" or "-05:00")
                offset = file_datetime.strftime("%z")
                if offset:
                    # Insert colon: "+0300" -> "+03:00"
                    offset_formatted = f"{offset[:3]}:{offset[3:]}"
                    tags_to_write[TAG_EXIF_OFFSET_TIME_DIGITIZED] = offset_formatted
                    self._logger.debug(f"Writing OffsetTimeDigitized: {offset_formatted}")
            elif offset_time_digitized:
                self._logger.debug(f"OffsetTimeDigitized already set: {offset_time_digitized}")
            
            # Copy IFD0:Make/Model to XMP-tiff:Make/Model if they exist
            ifd0_make = existing_tags.get(TAG_IFD0_MAKE)
            ifd0_model = existing_tags.get(TAG_IFD0_MODEL)
            
            if ifd0_make:
                tags_to_write[TAG_XMP_TIFF_MAKE] = ifd0_make
                self._logger.debug(f"Copying Make to XMP: {ifd0_make}")
            
            if ifd0_model:
                tags_to_write[TAG_XMP_TIFF_MODEL] = ifd0_model
                self._logger.debug(f"Copying Model to XMP: {ifd0_model}")

            self._exifer.write(file_path, tags_to_write, timeout=EXIFTOOL_LARGE_FILE_TIMEOUT)
            self._logger.debug(f"Successfully wrote DocumentID, InstanceID" + (f", and dc:Format ({dc_format})" if dc_format else ""))

            agent = f"scan-batcher {self._get_major_version()}"

            # Write first history entry: 'created'
            self._logger.debug(f"Writing 'created' history entry for {file_path.name}...")
            success = self._historian.append_entry(
                file_path=file_path,
                action=XMP_ACTION_CREATED,
                software_agent=agent,
                when=file_datetime,
                instance_id=instance_id,
                logger=self._logger,
            )
            if not success:
                self._logger.warning(f"Failed to write 'created' history entry for {file_path.name}")
            else:
                self._logger.debug("Successfully wrote 'created' history entry")

            # Write second history entry: 'edited'
            self._logger.debug(f"Writing 'edited' history entry for {file_path.name}...")
            success = self._historian.append_entry(
                file_path=file_path,
                action=XMP_ACTION_EDITED,
                software_agent=agent,
                when=file_datetime,
                changed="metadata",
                instance_id=instance_id,
                logger=self._logger,
            )
            if not success:
                self._logger.warning(f"Failed to write 'edited' history entry for {file_path.name}")
            else:
                self._logger.debug("Successfully wrote 'edited' history entry")

            self._logger.info(f"XMP history written for {file_path.name}")
            return True

        except Exception as e:
            self._logger.warning(f"Failed to write XMP history: {e}")
            return False
