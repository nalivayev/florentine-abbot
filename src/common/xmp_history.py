"""XMP History for tracking file operations in xmpMM:History."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .exifer import Exifer
from .logger import get_logger

logger = get_logger(__name__)


class XmpHistory:
    """Manages XMP-xmpMM:History entries for workflow logging.
    
    XMP History provides technical logging of file operations according to
    XMP Specification Part 2: Additional Properties (xmpMM namespace).
    
    Standard action values:
    - 'created': File created from scratch (scan-batcher)
    - 'converted': Format conversion
    - 'edited': Content modification
    - 'managed': Metadata management without content change (file-organizer)
    - 'derived': New file derived from source (preview-maker)
    """
    
    def __init__(self, exifer: Optional[Exifer] = None):
        """Initialize XMP History.
        
        Args:
            exifer: Exifer instance. If None, creates new instance.
        """
        self.exifer = exifer or Exifer()
    
    def append_entry(
        self,
        file_path: Path,
        action: str,
        software_agent: str,
        when: datetime,
        changed: Optional[str] = None,
        parameters: Optional[str] = None
    ) -> bool:
        """Append new entry to XMP-xmpMM:History.
        
        Args:
            file_path: Path to file
            action: Action performed (created, converted, edited, managed, derived)
            software_agent: Software that performed action, e.g. 'Florentine Abbot/file-organizer 1.0.5'
            when: Timestamp of operation (should match file modification time)
            changed: Optional description of what changed, e.g. '/metadata'
            parameters: Optional parameters, e.g. 'from source.tif'
        
        Returns:
            True if successful, False otherwise
        """
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False
        
        # Convert datetime to ISO 8601 format with timezone
        when_iso = when.isoformat()
        
        # Build history entry
        history_entry = {
            "action": action,
            "when": when_iso,
            "softwareAgent": software_agent
        }
        
        if changed:
            history_entry["changed"] = changed
        
        if parameters:
            history_entry["parameters"] = parameters
        
        # Use exiftool to append to History array
        # History is a bag of structures, use -struct option
        args = []
        for key, value in history_entry.items():
            args.extend([f"-xmp-xmpMM:History+={{{key}={value}}}"])
        
        success = self.exifer.write_tags(str(file_path), args)
        
        if success:
            logger.debug(f"Added XMP History entry: {action} for {file_path.name}")
        else:
            logger.error(f"Failed to add XMP History entry for {file_path}")
        
        return success
    
    def read_history(self, file_path: Path) -> list[dict]:
        """Read XMP-xmpMM:History from file.
        
        Args:
            file_path: Path to file
        
        Returns:
            List of history entries as dictionaries
        """
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return []
        
        # Read History field
        result = self.exifer.read_tags(str(file_path), ["xmp-xmpMM:History"])
        
        if not result or "xmp-xmpMM:History" not in result:
            return []
        
        # Parse history entries (exiftool returns structured data)
        # Implementation depends on exiftool output format
        history = result.get("xmp-xmpMM:History", [])
        
        if isinstance(history, str):
            # Single entry might be returned as string
            return [{"raw": history}]
        elif isinstance(history, list):
            return history
        else:
            return []
