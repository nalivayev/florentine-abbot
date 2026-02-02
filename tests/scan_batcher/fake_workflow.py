"""Fake workflow for testing scan-batcher without real scanner hardware."""

import shutil
from pathlib import Path

from common.logger import Logger
from scan_batcher.workflows.vuescan.workflow import VuescanWorkflow


class FakeVuescanWorkflow(VuescanWorkflow):
    """Fake VueScan workflow that copies a test file instead of running VueScan.
    
    This is used for integration testing without requiring VueScan software
    or scanner hardware. It inherits all real workflow logic except for the
    actual scanning step.
    
    Args:
        logger: Logger instance for workflow messages.
        mock_scan_file: Path to a test file that will be copied as "scan output".
    """
    
    def __init__(self, logger: Logger, mock_scan_file: Path) -> None:
        super().__init__(logger)
        self._mock_scan_file = mock_scan_file
    
    def _run_vuescan(self) -> None:
        """Override scanning to copy mock file instead of running VueScan.
        
        This simulates VueScan creating an output file in the configured
        output directory.
        """
        # Get output path from settings (already loaded by parent class)
        output_dir = Path(self._get_workflow_value("vuescan", "output_path"))
        output_name = self._get_workflow_value("vuescan", "output_file_name")
        output_ext = self._get_workflow_value("vuescan", "output_extension_name")
        output_file = output_dir / f"{output_name}.{output_ext}"
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy fake scan file to simulate VueScan output
        import shutil
        shutil.copy2(self._mock_scan_file, output_file)
        
        self._logger.info(
            f"Fake scan: copied {self._mock_scan_file.name} -> {output_file}"
        )
