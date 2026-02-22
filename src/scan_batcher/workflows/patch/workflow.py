"""
Patch workflow for adding XMP metadata to existing files.
"""

from pathlib import Path

from common.logger import Logger
from scan_batcher.workflows import register_workflow
from scan_batcher.workflow import MetadataWorkflow


@register_workflow("patch")
class PatchWorkflow(MetadataWorkflow):
    """
    Workflow for patching existing files with XMP metadata.
    
    This workflow adds DocumentID, InstanceID and XMP history entries
    to files that were not processed by scan-batcher (e.g., files from
    external sources or legacy scans).
    
    Usage:
        scan-batcher --batch process "D:\\path" "*.tif" --engine patch
    
    The workflow expects templates dict to contain:
        - path: Full path to the file to patch
        - filename: Name of the file (optional, for logging)
    """

    def __init__(self, logger: Logger, no_metadata: bool = False) -> None:
        """Initialize the patch workflow.
        
        Args:
            logger: Logger instance for this workflow.
            no_metadata: If True, skip writing EXIF/XMP metadata.
        """
        super().__init__(logger, no_metadata=no_metadata)

    def __call__(self, workflow_path: str, templates: dict[str, str]) -> None:
        """
        Execute the patch workflow for a single file.
        
        Args:
            workflow_path: Not used by this workflow.
            templates: Dictionary containing 'path' key with file path.
        """
        file_path_str = templates.get("path")
        if not file_path_str:
            self._logger.error("No 'path' template provided for patch workflow")
            return

        file_path = Path(file_path_str)
        
        if not file_path.exists():
            self._logger.error(f"File not found: {file_path}")
            return

        if not file_path.is_file():
            self._logger.warning(f"Skipping non-file: {file_path}")
            return

        # Check if file extension is supported
        if file_path.suffix.lower() not in self._EXIF_SUPPORTED_EXTENSIONS:
            self._logger.warning(
                f"Skipping unsupported file type: {file_path.name} "
                f"(supported: {', '.join(self._EXIF_SUPPORTED_EXTENSIONS)})"
            )
            return

        self._logger.info(f"Patching file: {file_path.name}")

        # Get datetime from file
        file_datetime = self._get_digitized_datetime(file_path)

        # Write XMP history
        success = self._write_xmp_history(file_path, file_datetime)
        
        if success:
            self._logger.info(f"Successfully patched: {file_path.name}")
        else:
            self._logger.error(f"Failed to patch: {file_path.name}")
