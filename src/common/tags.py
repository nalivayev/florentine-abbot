"""
Tag descriptors for :class:`~common.tagger.Tagger`.

Each ``Tag`` knows how to serialise itself for exiftool writes and how to
request / parse data for exiftool reads.  ``Tagger`` works exclusively
with ``Tag`` objects and has **no** domain knowledge about specific tag
formats (e.g. XMP History).

Classes
-------
Tag
    Abstract base.
KeyValueTag
    Simple scalar tag  (``-TagName=value``).
HistoryTag
    Structured XMP History entry (``-XMP-xmpMM:History+={…}``).

Usage — write::

    tagger.write(KeyValueTag(TAG_DOCUMENT_ID, doc_id))
    tagger.write(HistoryTag(action="created", when=dt, ...))

Usage — read::

    tagger.read(KeyValueTag(TAG_DOCUMENT_ID))
    tagger.read(HistoryTag())           # empty = read all history
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from .constants import TAG_XMP_XMPMM_HISTORY, TAG_XMP_XMPMM_HISTORY_ACTION, TAG_XMP_XMPMM_HISTORY_WHEN, TAG_XMP_XMPMM_HISTORY_SOFTWARE_AGENT, TAG_XMP_XMPMM_HISTORY_CHANGED, TAG_XMP_XMPMM_HISTORY_PARAMETERS, TAG_XMP_XMPMM_HISTORY_INSTANCE_ID, XMP_FIELD_ACTION, XMP_FIELD_WHEN, XMP_FIELD_SOFTWARE_AGENT, XMP_FIELD_CHANGED, XMP_FIELD_PARAMETERS, XMP_FIELD_INSTANCE_ID


class Tag(ABC):
    """
    Descriptor that tells :class:`Tagger` *how* to read/write a tag.

    Subclasses must implement four members:

    * :attr:`result_key` — key used in the dict returned by ``end()``
      for read batches.
    * :meth:`read_tags` — exiftool tag names to request.
    * :meth:`parse` — convert raw exiftool output into a value.
    * :meth:`write_args` — ``(tag, value)`` pairs for exiftool write.
    """

    @property
    @abstractmethod
    def result_key(self) -> str:
        """
        Key under which the parsed value appears in the result dict.
        """

    @abstractmethod
    def read_tags(self) -> list[str]:
        """
        Return exiftool tag names needed for reading.
        """

    @abstractmethod
    def parse(self, raw: dict[str, Any]) -> Any:
        """
        Extract and return the value from raw exiftool output.
        """

    @abstractmethod
    def write_args(self) -> list[tuple[str, Any]]:
        """
        Return ``(tag, value)`` pairs for a single exiftool write call.
        """


class KeyValueTag(Tag):
    """
    A simple scalar tag (one exiftool name, one value).

    For **reading** create with just the tag name::

        KeyValueTag(TAG_DOCUMENT_ID)

    For **writing** supply the value as well::

        KeyValueTag(TAG_DOCUMENT_ID, doc_id)
    """

    def __init__(self, tag: str, value: Any = None) -> None:
        self._tag = tag
        self._value = value

    @property
    def result_key(self) -> str:
        return self._tag

    def read_tags(self) -> list[str]:
        return [self._tag]

    def parse(self, raw: dict[str, Any]) -> Any:
        return raw.get(self._tag)

    def write_args(self) -> list[tuple[str, Any]]:
        return [(self._tag, self._value)]


# Flattened tags that exiftool uses for History arrays
_HISTORY_FLATTENED_TAGS = [
    TAG_XMP_XMPMM_HISTORY_ACTION,
    TAG_XMP_XMPMM_HISTORY_WHEN,
    TAG_XMP_XMPMM_HISTORY_SOFTWARE_AGENT,
    TAG_XMP_XMPMM_HISTORY_CHANGED,
    TAG_XMP_XMPMM_HISTORY_PARAMETERS,
    TAG_XMP_XMPMM_HISTORY_INSTANCE_ID,
]

# Mapping: flattened exiftool tag → dict key in parsed entries
_HISTORY_FIELD_MAP = {
    TAG_XMP_XMPMM_HISTORY_ACTION: "action",
    TAG_XMP_XMPMM_HISTORY_WHEN: "when",
    TAG_XMP_XMPMM_HISTORY_SOFTWARE_AGENT: "softwareAgent",
    TAG_XMP_XMPMM_HISTORY_CHANGED: "changed",
    TAG_XMP_XMPMM_HISTORY_PARAMETERS: "parameters",
    TAG_XMP_XMPMM_HISTORY_INSTANCE_ID: "instanceID",
}

# Ordered fields for building exiftool struct strings
_HISTORY_FIELDS_ORDER = (
    XMP_FIELD_ACTION,
    XMP_FIELD_WHEN,
    XMP_FIELD_SOFTWARE_AGENT,
    XMP_FIELD_INSTANCE_ID,
    XMP_FIELD_CHANGED,
    XMP_FIELD_PARAMETERS,
)


class HistoryTag(Tag):
    """
    Structured XMP-xmpMM:History entry.

    For **reading** create with no arguments — returns ``list[dict]``::

        HistoryTag()

    For **writing** supply the event fields::

        HistoryTag(
            action="created",
            when=datetime.now(tz=…),
            software_agent="scan-batcher 1.0",
            instance_id="abc123…",
        )

    Parameters match ``XMP_FIELD_*`` constants from :mod:`common.constants`.
    """

    def __init__(
        self,
        *,
        action: str | None = None,
        when: datetime | None = None,
        software_agent: str | None = None,
        instance_id: str | None = None,
        changed: str | None = None,
        parameters: str | None = None,
    ) -> None:
        self._fields: dict[str, Any] = {}
        if action is not None:
            self._fields[XMP_FIELD_ACTION] = action
        if when is not None:
            self._fields[XMP_FIELD_WHEN] = when
        if software_agent is not None:
            self._fields[XMP_FIELD_SOFTWARE_AGENT] = software_agent
        if instance_id is not None:
            self._fields[XMP_FIELD_INSTANCE_ID] = instance_id
        if changed is not None:
            self._fields[XMP_FIELD_CHANGED] = changed
        if parameters is not None:
            self._fields[XMP_FIELD_PARAMETERS] = parameters

    @property
    def result_key(self) -> str:
        return TAG_XMP_XMPMM_HISTORY

    def read_tags(self) -> list[str]:
        return list(_HISTORY_FLATTENED_TAGS)

    def parse(self, raw: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Parse flattened History arrays into ``list[dict]``.
        """
        arrays: dict[str, list] = {}
        for flat_tag, dict_key in _HISTORY_FIELD_MAP.items():
            val = raw.get(flat_tag, [])
            if not isinstance(val, list):
                val = [val] if val else []
            arrays[dict_key] = val

        max_len = max((len(a) for a in arrays.values()), default=0)

        history: list[dict[str, Any]] = []
        for i in range(max_len):
            entry: dict[str, Any] = {}
            for key, arr in arrays.items():
                if i < len(arr):
                    entry[key] = arr[i]
            if entry:
                history.append(entry)

        return history

    def write_args(self) -> list[tuple[str, Any]]:
        """
        Return a single ``(TAG+, struct_str)`` pair for append.
        """
        parts: list[str] = []
        for field in _HISTORY_FIELDS_ORDER:
            val = self._fields.get(field)
            if val is None:
                continue
            if isinstance(val, datetime):
                val = val.isoformat(timespec="milliseconds")
            parts.append(f"{field}={val}")

        struct_str = "{" + ",".join(parts) + "}"
        append_key = TAG_XMP_XMPMM_HISTORY + "+"
        return [(append_key, struct_str)]
