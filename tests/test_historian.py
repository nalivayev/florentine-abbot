import uuid
from datetime import datetime, timezone

import pytest
from PIL import Image

from common.exifer import Exifer
from common.historian import XMPHistorian, XMP_TAG_HISTORY, XMP_ACTION_CREATED


def test_append_and_read_history(tmp_path):
    # Skip if exiftool is not available
    try:
        Exifer()._run(["-ver"])
    except (FileNotFoundError, RuntimeError):
        pytest.skip("ExifTool not found, skipping historian integration test")

    # Create a minimal TIFF file
    file_path = tmp_path / "sample.tiff"
    img = Image.new("RGB", (1, 1), color=(255, 255, 255))
    img.save(file_path, format="TIFF")

    ex = Exifer()
    historian = XMPHistorian(exifer=ex)

    instance = uuid.uuid4().hex
    when = datetime.now(timezone.utc)

    # Append an entry
    ok = historian.append_entry(file_path, XMP_ACTION_CREATED, "test-historian", when, instance_id=instance)
    assert ok is True

    # Read back using Exifer.read: raw History tag may not be present
    # since exiftool often exposes structured history as flattened subfields.
    data = ex.read(file_path, [XMP_TAG_HISTORY])

    # Verify structured read via XMPHistorian.read_history (preferred API)
    structured = historian.read_history(file_path)
    assert isinstance(structured, list)
    assert any(entry.get('instanceID') == instance for entry in structured)
