"""
Tagger — unified metadata read/write interface.

Wraps :class:`Exifer` and provides a file-centric API with optional
batch mode (``begin`` / ``end``) so that multiple writes are flushed
to disk in a single exiftool invocation.

``Tagger`` is **generic** — it has no knowledge of specific tag formats.
All serialisation / parsing logic lives in :class:`~common.tags.Tag`
subclasses (``KeyValueTag``, ``HistoryTag``, …).

Usage — immediate mode::

    tagger = Tagger(file_path)
    value  = tagger.read(KeyValueTag(TAG_DOCUMENT_ID))
    tagger.write(KeyValueTag(TAG_DOCUMENT_ID, value))

Usage — batch write::

    tagger = Tagger(file_path)
    tagger.begin()
    tagger.write(KeyValueTag(TAG_DOCUMENT_ID, doc_id))
    tagger.write(HistoryTag(action="created", when=dt, ...))
    tagger.write(HistoryTag(action="edited", when=dt, ...))
    tagger.end()          # one exiftool call

Usage — batch read::

    tagger = Tagger(file_path)
    tagger.begin()
    tagger.read(KeyValueTag(TAG_DOCUMENT_ID))
    tagger.read(HistoryTag())
    result = tagger.end()  # one exiftool call → dict
    doc_id = result[TAG_DOCUMENT_ID]
    history = result[TAG_XMP_XMPMM_HISTORY]
"""

from pathlib import Path
from typing import Any, Optional

from .exifer import Exifer
from .tags import Tag


class Tagger:
    """
    File-centric metadata reader/writer with optional batching.

    Each ``Tagger`` instance is bound to a single *file_path*.

    Args:
        file_path: Path to the image file.
        exifer: Optional :class:`Exifer` instance (shared across taggers).
        timeout: exiftool timeout in seconds for large files.
    """

    def __init__(
        self,
        file_path: Path,
        exifer: Optional[Exifer] = None,
        timeout: int | None = None,
    ) -> None:
        self._file_path = file_path
        self._exifer = exifer or Exifer()
        self._timeout = timeout

        # Batch state
        self._batch = False
        self._batch_mode: str | None = None   # "read" or "write"
        self._read_buffer: list[Tag] = []
        self._write_buffer: list[Tag] = []

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    @property
    def file_path(self) -> Path:
        """
        The file this tagger is bound to.
        """
        return self._file_path

    def begin(self) -> None:
        """
        Enter batch mode.

        Subsequent ``read`` / ``write`` calls are buffered until ``end``.
        Mixing reads and writes in the same batch is not allowed.

        Raises:
            RuntimeError: If already in batch mode.
        """
        if self._batch:
            raise RuntimeError("Already in batch mode — call end() first")
        self._batch = True
        self._batch_mode = None
        self._read_buffer.clear()
        self._write_buffer.clear()

    def end(self) -> dict[str, Any] | None:
        """
        Flush the batch and leave batch mode.

        For a **read** batch the accumulated tags are read in a single
        exiftool call and the result dict is returned.

        For a **write** batch all accumulated tags are written in a
        single exiftool call.

        Returns:
            ``dict`` of tag values for read batches, ``None`` for write
            batches.

        Raises:
            RuntimeError: If not in batch mode.
        """
        if not self._batch:
            raise RuntimeError("Not in batch mode — call begin() first")

        if self._batch_mode is None:
            self._batch = False
            return None

        try:
            if self._batch_mode == "read":
                return self._flush_read()
            else:
                self._flush_write()
                return None
        finally:
            self._batch = False
            self._batch_mode = None
            self._read_buffer.clear()
            self._write_buffer.clear()

    def read(self, tag: Tag) -> Any:
        """
        Read a tag value.

        In immediate mode the value is returned directly.
        In batch mode the tag is buffered; call ``end()`` to get results.

        Args:
            tag: A :class:`Tag` descriptor (e.g. ``KeyValueTag(…)``).

        Returns:
            Parsed value (immediate mode) or ``None`` (batch mode).
        """
        if self._batch:
            self._set_batch_mode("read")
            self._read_buffer.append(tag)
            return None

        # Immediate mode — single exiftool call
        raw = self._exifer.read(self._file_path, tag.read_tags())
        return tag.parse(raw)

    def write(self, tag: Tag) -> None:
        """
        Write a tag value.

        In immediate mode the tag is written to disk immediately.
        In batch mode the tag is buffered; call ``end()`` to flush.

        Args:
            tag: A :class:`Tag` descriptor with a value
                 (e.g. ``KeyValueTag(name, val)``).
        """
        if self._batch:
            self._set_batch_mode("write")
            self._write_buffer.append(tag)
            return

        # Immediate mode — single exiftool call
        tags_dict = self._collect_write_args([tag])
        self._exifer.write(
            self._file_path,
            tags_dict,
            timeout=self._timeout,
        )

    def _set_batch_mode(self, mode: str) -> None:
        """
        Lock the batch to *mode* or raise if mixed.
        """
        if self._batch_mode is None:
            self._batch_mode = mode
        elif self._batch_mode != mode:
            raise RuntimeError(
                f"Cannot mix read and write in a single batch "
                f"(batch is '{self._batch_mode}', attempted '{mode}')"
            )

    def _flush_read(self) -> dict[str, Any]:
        """
        Execute a batched read — one exiftool call.
        """
        # Collect all exiftool tag names, de-duplicating
        all_tags: list[str] = []
        seen: set[str] = set()
        for tag in self._read_buffer:
            for t in tag.read_tags():
                if t not in seen:
                    all_tags.append(t)
                    seen.add(t)

        raw = self._exifer.read(self._file_path, all_tags)

        # Let each Tag parse its portion of the result
        result: dict[str, Any] = {}
        for tag in self._read_buffer:
            result[tag.result_key] = tag.parse(raw)

        return result

    def _flush_write(self) -> None:
        """
        Execute a batched write — one exiftool call.
        """
        tags_dict = self._collect_write_args(self._write_buffer)
        self._exifer.write(
            self._file_path,
            tags_dict,
            timeout=self._timeout,
        )

    @staticmethod
    def _collect_write_args(tags: list[Tag]) -> dict[str, Any]:
        """
        Merge ``write_args()`` from all tags into a single dict.

        When multiple tags produce the same key (e.g. History append),
        values are collected into a list so that Exifer emits multiple
        ``-key=value`` arguments.
        """
        result: dict[str, Any] = {}
        for tag in tags:
            for key, value in tag.write_args():
                if key in result:
                    existing = result[key]
                    if isinstance(existing, list):
                        existing.append(value)
                    else:
                        result[key] = [existing, value]
                else:
                    result[key] = value
        return result
