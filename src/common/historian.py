"""XMP Historian for tracking file operations in xmpMM:History."""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .exifer import Exifer
from .constants import EXIFTOOL_LARGE_FILE_TIMEOUT, TAG_XMP_XMPMM_HISTORY, TAG_XMP_XMPMM_HISTORY_ACTION, TAG_XMP_XMPMM_HISTORY_WHEN, TAG_XMP_XMPMM_HISTORY_SOFTWARE_AGENT, TAG_XMP_XMPMM_HISTORY_CHANGED, TAG_XMP_XMPMM_HISTORY_PARAMETERS, TAG_XMP_XMPMM_HISTORY_INSTANCE_ID, XMP_FIELD_ACTION, XMP_FIELD_WHEN, XMP_FIELD_SOFTWARE_AGENT, XMP_FIELD_CHANGED, XMP_FIELD_PARAMETERS, XMP_FIELD_INSTANCE_ID


class XMPHistorian:
    """
    Manages XMP-xmpMM:History entries for workflow logging.

    XMP History provides technical logging of file operations according to
    XMP Specification Part 2: Additional Properties (xmpMM namespace).

    Standard action constants (imported from common.constants):
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

    def __init__(self, exifer: Optional[Exifer] = None) -> None:
        """
        Initialize XMPHistorian.

        Args:
            exifer (Exifer|None): Exifer instance. If None, creates new instance.
        """
        self._exifer = exifer or Exifer()

    def append_entry(
        self,
        file_path: Path,
        action: str,
        software_agent: str,
        when: datetime,
        changed: Optional[str] = None,
        parameters: Optional[str] = None,
        logger=None,
        instance_id: Optional[str] = None,
        derived_from_instance_id: Optional[str] = None,
        derived_from_document_id: Optional[str] = None,
    ) -> bool:
        """
        Append new entry to XMP-xmpMM:History.

        Args:
            file_path (Path): Path to file.
            action (str): Action performed. Use XMP_ACTION_* constants.
            software_agent (str): Software that performed action.
            when (datetime): Timestamp of operation (should match file modification time).
            changed (str|None): Optional description of what changed.
            parameters (str|None): Optional parameters.
            logger: Optional logger instance for debug/error messages.
            instance_id (str|None): Optional InstanceID for this version.
            derived_from_instance_id (str|None): Not used (compatibility).
            derived_from_document_id (str|None): Not used (compatibility).
        Returns:
            bool: True if successful, False otherwise.
        """
        if not file_path.exists():
            if logger:
                logger.error(f"File not found: {file_path}")
            return False

        # Convert datetime to ISO 8601 format with timezone and milliseconds
        when_iso = when.isoformat(timespec='milliseconds')

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

    def read_history(self, file_path: Path, logger=None) -> list[dict[str, Any]]:
        """
        Read XMP-xmpMM:History from file.

        Args:
            file_path (Path): Path to file.
            logger: Optional logger instance for error messages.
        Returns:
            list[dict[str, Any]]: List of history entries as dictionaries.
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
