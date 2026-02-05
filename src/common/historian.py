"""XMP Historian for tracking file operations in xmpMM:History."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .exifer import Exifer
from .constants import EXIFTOOL_LARGE_FILE_TIMEOUT

# XMP-xmpMM namespace tags
TAG_XMP_XMPMM_HISTORY = "XMP-xmpMM:History"
TAG_XMP_XMPMM_INSTANCE_ID = "XMP-xmpMM:InstanceID"
TAG_XMP_XMPMM_DOCUMENT_ID = "XMP-xmpMM:DocumentID"
TAG_XMP_XMP_CREATOR_TOOL = "XMP-xmp:CreatorTool"

# XMP History flattened tags (exiftool expands structures)
TAG_XMP_XMPMM_HISTORY_ACTION = "XMP-xmpMM:HistoryAction"
TAG_XMP_XMPMM_HISTORY_WHEN = "XMP-xmpMM:HistoryWhen"
TAG_XMP_XMPMM_HISTORY_SOFTWARE_AGENT = "XMP-xmpMM:HistorySoftwareAgent"
TAG_XMP_XMPMM_HISTORY_CHANGED = "XMP-xmpMM:HistoryChanged"
TAG_XMP_XMPMM_HISTORY_PARAMETERS = "XMP-xmpMM:HistoryParameters"
TAG_XMP_XMPMM_HISTORY_INSTANCE_ID = "XMP-xmpMM:HistoryInstanceID"

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
        # Keep Exifer as an implementation detail (private)
        self._exifer = exifer or Exifer()
    
    def append_entry(
        self,
        file_path: Path,
        action: str,
        software_agent: str,
        when: datetime,
        changed: Optional[str] = None,
        parameters: Optional[str] = None,
        logger = None,
        instance_id: Optional[str] = None,
        derived_from_instance_id: Optional[str] = None,
        derived_from_document_id: Optional[str] = None,
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
            instance_id: Optional InstanceID for this version
            derived_from_instance_id: Not used (kept for compatibility)
            derived_from_document_id: Not used (kept for compatibility)
        
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

        if instance_id:
            history_entry[XMP_FIELD_INSTANCE_ID] = instance_id

        if changed:
            history_entry[XMP_FIELD_CHANGED] = changed

        if parameters:
            history_entry[XMP_FIELD_PARAMETERS] = parameters
        
        # Use exiftool to append a single structured History entry.
        # Build a struct like: {action=...,when=...,softwareAgent=...,...}
        struct_items = []
        for key, value in history_entry.items():
            # Ensure values are serialized as strings without surrounding braces
            struct_items.append(f"{key}={value}")

        struct_value = "{" + ",".join(struct_items) + "}"

        # ExifTool append operator is represented by a trailing '+' on the tag name
        tag_name = TAG_XMP_XMPMM_HISTORY + "+"

        # Exifer.write expects a mapping of tag -> value (or list of values)
        success = self._exifer.write(file_path, {tag_name: struct_value}, timeout=EXIFTOOL_LARGE_FILE_TIMEOUT)
        
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
        
        # ExifTool flattens structured History into separate array tags:
        # XMP-xmpMM:HistoryAction, XMP-xmpMM:HistoryWhen, etc.
        # Read all History-related tags
        history_tags = [
            TAG_XMP_XMPMM_HISTORY_ACTION,
            TAG_XMP_XMPMM_HISTORY_WHEN,
            TAG_XMP_XMPMM_HISTORY_SOFTWARE_AGENT,
            TAG_XMP_XMPMM_HISTORY_CHANGED,
            TAG_XMP_XMPMM_HISTORY_PARAMETERS,
            TAG_XMP_XMPMM_HISTORY_INSTANCE_ID,
        ]
        
        result = self._exifer.read(file_path, history_tags)
        
        # Extract arrays (exiftool returns lists for repeated tags)
        actions = result.get(TAG_XMP_XMPMM_HISTORY_ACTION, [])
        whens = result.get(TAG_XMP_XMPMM_HISTORY_WHEN, [])
        agents = result.get(TAG_XMP_XMPMM_HISTORY_SOFTWARE_AGENT, [])
        changeds = result.get(TAG_XMP_XMPMM_HISTORY_CHANGED, [])
        parameters = result.get(TAG_XMP_XMPMM_HISTORY_PARAMETERS, [])
        instance_ids = result.get(TAG_XMP_XMPMM_HISTORY_INSTANCE_ID, [])
        
        # Ensure all are lists
        if not isinstance(actions, list):
            actions = [actions] if actions else []
        if not isinstance(whens, list):
            whens = [whens] if whens else []
        if not isinstance(agents, list):
            agents = [agents] if agents else []
        if not isinstance(changeds, list):
            changeds = [changeds] if changeds else []
        if not isinstance(parameters, list):
            parameters = [parameters] if parameters else []
        if not isinstance(instance_ids, list):
            instance_ids = [instance_ids] if instance_ids else []
        
        # Build history entries by index
        max_len = max(len(actions), len(whens), len(agents), len(changeds), len(parameters), len(instance_ids))
        history = []
        for i in range(max_len):
            entry = {}
            if i < len(actions):
                entry["action"] = actions[i]
            if i < len(whens):
                entry["when"] = whens[i]
            if i < len(agents):
                entry["softwareAgent"] = agents[i]
            if i < len(changeds):
                entry["changed"] = changeds[i]
            if i < len(parameters):
                entry["parameters"] = parameters[i]
            if i < len(instance_ids):
                entry["instanceID"] = instance_ids[i]
            if entry:  # Only add non-empty entries
                history.append(entry)
        
        return history
