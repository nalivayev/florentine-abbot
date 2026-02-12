from abc import ABC, abstractmethod
from pathlib import Path
import datetime
import uuid

from common.exifer import Exifer
from common.logger import Logger
from common.version import get_version
from common.constants import EXIFTOOL_LARGE_FILE_TIMEOUT, MIME_TYPE_MAP
from common.historian import XMPHistorian, TAG_XMP_XMPMM_DOCUMENT_ID, TAG_XMP_XMPMM_INSTANCE_ID, XMP_ACTION_CREATED, XMP_ACTION_EDITED
from common.metadata import TAG_XMP_DC_FORMAT
from scan_batcher.constants import EXIF_DATETIME_FORMAT


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
        "ExifIFD:DateTimeOriginal",
        "ExifIFD:CreateDate",
        "IFD0:DateTime",
    ]

    # EXIF tag for software/creator tool
    _EXIF_SOFTWARE_TAG = "IFD0:Software"

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

    def _get_file_datetime(self, file_path: Path) -> datetime.datetime:
        """Extract datetime from file EXIF or use file modification time.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Datetime extracted from EXIF or file modification time.
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
                            moment = datetime.datetime.strptime(value, EXIF_DATETIME_FORMAT)
                            break
                        except ValueError:
                            pass
            except Exception as e:
                self._logger.warning(f"Unable to extract EXIF from file '{file_path.name}': {e}")

        if moment is None:
            moment = datetime.datetime.fromtimestamp(getmtime(file_path))

        return moment

    def _write_xmp_history(
        self,
        file_path: Path,
        file_datetime: datetime.datetime,
        created_agent: str | None = None,
    ) -> bool:
        """
        Write XMP-xmpMM:History entries and ensure DocumentID/InstanceID are set.
        
        Writes two history entries:
        1. 'created' action - file creation by scanning software
        2. 'edited' action - metadata changes by scan-batcher
        
        Args:
            file_path: Path to the file to write metadata to.
            file_datetime: Datetime for the history entries.
            created_agent: Software agent for 'created' action. If None, reads from
                          IFD0:Software tag or uses scan-batcher version.
        
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
            # Read existing DocumentID, InstanceID, and Software
            self._logger.debug(f"Reading existing XMP tags from {file_path.name}...")
            existing_tags = self._exifer.read(file_path, [
                TAG_XMP_XMPMM_DOCUMENT_ID,
                TAG_XMP_XMPMM_INSTANCE_ID,
                self._EXIF_SOFTWARE_TAG,
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
            
            self._exifer.write(file_path, tags_to_write, timeout=EXIFTOOL_LARGE_FILE_TIMEOUT)
            self._logger.debug(f"Successfully wrote DocumentID, InstanceID" + (f", and dc:Format ({dc_format})" if dc_format else ""))

            # Determine software agent for 'created' action
            if created_agent is None:
                software_tag = existing_tags.get(self._EXIF_SOFTWARE_TAG)
                if software_tag:
                    created_agent = software_tag
                else:
                    created_agent = f"scan-batcher {self._get_major_version()}"

            # Write first history entry: 'created'
            self._logger.debug(f"Writing 'created' history entry for {file_path.name}...")
            success = self._historian.append_entry(
                file_path=file_path,
                action=XMP_ACTION_CREATED,
                software_agent=created_agent,
                when=file_datetime,
                instance_id=instance_id,
                logger=self._logger,
            )
            if not success:
                self._logger.warning(f"Failed to write 'created' history entry for {file_path.name}")
            else:
                self._logger.debug("Successfully wrote 'created' history entry")

            # Write second history entry: 'edited'
            edited_agent = f"scan-batcher {self._get_major_version()}"
            self._logger.debug(f"Writing 'edited' history entry for {file_path.name}...")
            success = self._historian.append_entry(
                file_path=file_path,
                action=XMP_ACTION_EDITED,
                software_agent=edited_agent,
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
