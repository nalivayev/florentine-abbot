"""XMP Historian for tracking file operations in xmpMM:History."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .exifer import Exifer


# XMP-xmpMM namespace tags
XMP_TAG_HISTORY = "XMP-xmpMM:History"

# XMP History event fields (stEvt namespace)
XMP_FIELD_ACTION = "action"
XMP_FIELD_WHEN = "when"
XMP_FIELD_SOFTWARE_AGENT = "softwareAgent"
XMP_FIELD_CHANGED = "changed"
XMP_FIELD_PARAMETERS = "parameters"
XMP_FIELD_INSTANCE_ID = "instanceID"

# Standard XMP History action types per XMP Specification Part 2 (xmpMM namespace)
# Table 8 — ResourceEvent fields: stEvt:action Open Choice of Text
# https://www.adobe.com/devnet/xmp/library/XMPSpecificationPart2.pdf
XMP_ACTION_CONVERTED = "converted"          # Format conversion
XMP_ACTION_COPIED = "copied"                # File copied
XMP_ACTION_CREATED = "created"              # File created from scratch
XMP_ACTION_CROPPED = "cropped"              # Image cropped
XMP_ACTION_EDITED = "edited"                # Content modification
XMP_ACTION_FILTERED = "filtered"            # Filter applied
XMP_ACTION_FORMATTED = "formatted"          # Format/layout changed
XMP_ACTION_VERSION_UPDATED = "version_updated"  # Version updated
XMP_ACTION_PRINTED = "printed"              # File printed
XMP_ACTION_PUBLISHED = "published"          # File published
XMP_ACTION_MANAGED = "managed"              # Metadata management without content change
XMP_ACTION_PRODUCED = "produced"            # File produced/rendered
XMP_ACTION_RESIZED = "resized"              # Image resized
XMP_ACTION_SAVED = "saved"                  # File saved


class XMPHistorian:
    """Manages XMP-xmpMM:History entries for workflow logging.
    
    XMP History provides technical logging of file operations according to
    XMP Specification Part 2: Additional Properties (xmpMM namespace).
    
    Use the XMP_ACTION_* constants for standard action values:
    - XMP_ACTION_CONVERTED: Format conversion
    - XMP_ACTION_COPIED: File copied
    - XMP_ACTION_CREATED: File created from scratch
    - XMP_ACTION_CROPPED: Image cropped
    - XMP_ACTION_EDITED: Content modification
    - XMP_ACTION_FILTERED: Filter applied
    - XMP_ACTION_FORMATTED: Format/layout changed
    - XMP_ACTION_VERSION_UPDATED: Version updated
    - XMP_ACTION_PRINTED: File printed
    - XMP_ACTION_PUBLISHED: File published
    - XMP_ACTION_MANAGED: Metadata management without content change
    - XMP_ACTION_PRODUCED: File produced/rendered
    - XMP_ACTION_RESIZED: Image resized
    - XMP_ACTION_SAVED: File saved
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
        parameters: Optional[str] = None,
        logger = None
    ) -> bool:
        """Append new entry to XMP-xmpMM:History.
        
        Args:
            file_path: Path to file
            action: Action performed. Use XMP_ACTION_* constants (converted, copied, created, cropped,
                   edited, filtered, formatted, version_updated, printed, published, managed, 
                   produced, resized, saved)
            software_agent: Software that performed action, e.g. 'Florentine Abbot/file-organizer 1.0.5'
            when: Timestamp of operation (should match file modification time)
            changed: Optional description of what changed, e.g. '/metadata'
            parameters: Optional parameters, e.g. 'from source.tif'
            logger: Optional logger instance for debug/error messages
        
        Returns:
            True if successful, False otherwise
        """
        if not file_path.exists():
            if logger:
                logger.error(f"File not found: {file_path}")
            return False
        
        # Convert datetime to ISO 8601 format with timezone
        when_iso = when.isoformat()
        
        # Build history entry
        history_entry = {
            XMP_FIELD_ACTION: action,
            XMP_FIELD_WHEN: when_iso,
            XMP_FIELD_SOFTWARE_AGENT: software_agent
        }
        
        if changed:
            history_entry[XMP_FIELD_CHANGED] = changed
        
        if parameters:
            history_entry[XMP_FIELD_PARAMETERS] = parameters
        
        # Use exiftool to append to History array
        # History is a bag of structures, use -struct option
        args = []
        for key, value in history_entry.items():
            args.extend([f"-{XMP_TAG_HISTORY}+={{{key}={value}}}"])
        
        success = self.exifer.write_tags(str(file_path), args)
        
        if logger:
            if success:
                logger.debug(f"Added XMP History entry: {action} for {file_path.name}")
            else:
                logger.error(f"Failed to add XMP History entry for {file_path}")
        
        return success
    
    def read_history(self, file_path: Path, logger = None) -> list[dict]:
        """Read XMP-xmpMM:History from file.
        
        Args:
            file_path: Path to file
            logger: Optional logger instance for error messages
        
        Returns:
            List of history entries as dictionaries
        """
        if not file_path.exists():
            if logger:
                logger.error(f"File not found: {file_path}")
            return []
        
        # Read History field
        result = self.exifer.read_tags(str(file_path), [XMP_TAG_HISTORY])
        
        if not result or XMP_TAG_HISTORY not in result:
            return []
        
        # Parse history entries (exiftool returns structured data)
        # Implementation depends on exiftool output format
        history = result.get(XMP_TAG_HISTORY, [])
        
        if isinstance(history, str):
            # Single entry might be returned as string
            return [{"raw": history}]
        elif isinstance(history, list):
            return history
        else:
            return []
