"""
Fake MetadataWorkflow for testing without full workflow infrastructure.

Exposes MetadataWorkflow's protected methods as public API so that
test utilities (e.g. create_test_image) can simulate scan-batcher's
metadata writing step without going through the full workflow pipeline.

This follows the project's fake-class pattern (FakeExifer, FakeArchiveMetadata)
where test doubles inherit real classes and only override what is needed.
"""

import datetime
from pathlib import Path

from common.logger import Logger
from scan_batcher.workflow import MetadataWorkflow


class FakeMetadataWorkflow(MetadataWorkflow):
    """
    Test double for MetadataWorkflow that exposes metadata writing.
    
    Unlike the real MetadataWorkflow (which is abstract and requires
    subclasses to implement __call__), this fake provides direct access
    to the metadata writing functionality for test fixtures.
    
    Usage:
        workflow = FakeMetadataWorkflow(logger)
        workflow.write_xmp_metadata(file_path, file_datetime)
    """

    def __call__(self, workflow_path: str, templates: dict[str, str]) -> None:
        """
        Not used — this fake is not meant to run as a workflow."""
        raise NotImplementedError("FakeMetadataWorkflow is not a runnable workflow")

    def write_xmp_metadata(
        self,
        file_path: Path,
        file_datetime: datetime.datetime,
    ) -> bool:
        """
        Write XMP metadata to a file (public wrapper for _write_xmp_history).
        
        Delegates to the real MetadataWorkflow._write_xmp_history which:
        - Generates DocumentID and InstanceID (if missing)
        - Writes dc:Format (MIME type)
        - Writes or enriches XMP-exif:DateTimeDigitized with timezone
        - Writes Exif:OffsetTimeDigitized (if missing)
        - Appends XMP History entries (created + edited)
        
        Args:
            file_path: Path to the file to write metadata to.
            file_datetime: Datetime for metadata (with timezone).
        
        Returns:
            True if successful, False otherwise.
        """
        return self._write_xmp_history(file_path, file_datetime)

    def get_digitized_datetime(self, file_path: Path) -> datetime.datetime:
        """
        Extract digitized datetime from file (public wrapper for _get_digitized_datetime).
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Datetime extracted from EXIF or file modification time (in local timezone).
        """
        return self._get_digitized_datetime(file_path)
