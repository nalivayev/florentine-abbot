import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from common.exifer import Exifer
from common.tagger import Tagger
from common.tags import KeyValueTag, HistoryTag
from common.constants import TAG_XMP_XMPMM_DOCUMENT_ID, TAG_XMP_XMPMM_INSTANCE_ID, XMP_ACTION_CREATED
from tests.common.test_utils import create_test_image


@pytest.mark.usefixtures("require_exiftool")
class TestTagger:
    """
    Integration tests for Tagger with Tag descriptors.
    """

    def _create_image(self, tmp_path: Path) -> Path:
        """
        Create a minimal test image without scan-batcher metadata.
        """
        file_path = tmp_path / "sample.tiff"
        create_test_image(file_path, size=(1, 1), format="TIFF", add_ids=False)
        return file_path

    def test_write_and_read_history(self, tmp_path):
        """
        Write a History entry via Tagger batch and read it back.
        """
        file_path = self._create_image(tmp_path)

        ex = Exifer()
        instance = uuid.uuid4().hex
        when = datetime.now(timezone.utc)

        # Write via batch
        tagger = Tagger(file_path, exifer=ex)
        tagger.begin()
        tagger.write(HistoryTag(
            action=XMP_ACTION_CREATED,
            when=when,
            software_agent="test-tagger",
            instance_id=instance,
        ))
        tagger.end()

        # Read back via Tagger
        tagger2 = Tagger(file_path, exifer=ex)
        history = tagger2.read(HistoryTag())
        assert isinstance(history, list)
        assert any(entry.get("instanceID") == instance for entry in history)

    def test_batch_read(self, tmp_path):
        """
        Batch-read multiple tags in a single call.
        """
        file_path = self._create_image(tmp_path)

        ex = Exifer()
        doc_id = uuid.uuid4().hex
        inst_id = uuid.uuid4().hex

        # Write IDs first
        tagger = Tagger(file_path, exifer=ex)
        tagger.begin()
        tagger.write(KeyValueTag(TAG_XMP_XMPMM_DOCUMENT_ID, doc_id))
        tagger.write(KeyValueTag(TAG_XMP_XMPMM_INSTANCE_ID, inst_id))
        tagger.end()

        # Batch-read them back
        tagger2 = Tagger(file_path, exifer=ex)
        tagger2.begin()
        tagger2.read(KeyValueTag(TAG_XMP_XMPMM_DOCUMENT_ID))
        tagger2.read(KeyValueTag(TAG_XMP_XMPMM_INSTANCE_ID))
        result = tagger2.end()

        assert result is not None
        assert result[TAG_XMP_XMPMM_DOCUMENT_ID] == doc_id
        assert result[TAG_XMP_XMPMM_INSTANCE_ID] == inst_id

    def test_batch_mode_errors(self):
        """
        Verify batch mode raises on misuse.
        """
        tagger = Tagger(Path("dummy.tif"))

        # end() without begin()
        with pytest.raises(RuntimeError, match="Not in batch mode"):
            tagger.end()

        # Double begin()
        tagger.begin()
        with pytest.raises(RuntimeError, match="Already in batch mode"):
            tagger.begin()

        # Mixing reads and writes
        tagger2 = Tagger(Path("dummy.tif"))
        tagger2.begin()
        tagger2.read(KeyValueTag("SomeTag"))
        with pytest.raises(RuntimeError, match="Cannot mix"):
            tagger2.write(KeyValueTag("SomeTag", "value"))
