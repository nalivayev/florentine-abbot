"""Common test utilities for creating test fixtures."""

import uuid
from pathlib import Path

from PIL import Image

from common.exifer import Exifer
from common.historian import TAG_XMP_XMPMM_DOCUMENT_ID, TAG_XMP_XMPMM_INSTANCE_ID


def create_test_image(
    path: Path,
    size: tuple[int, int] = (100, 100),
    color: str | tuple = "red",
    format: str | None = None,
    add_ids: bool = True,
) -> None:
    """Create a test image with optional DocumentID/InstanceID.
    
    Args:
        path: Path where to save the image.
        size: Image size as (width, height).
        color: Fill color (name or RGB tuple).
        format: Image format (TIFF, JPEG, etc). If None, inferred from extension.
        add_ids: If True, add DocumentID/InstanceID required by FileProcessor/PreviewMaker.
    """
    img = Image.new("RGB", size, color=color)
    
    save_kwargs = {}
    if format:
        save_kwargs["format"] = format
    
    img.save(path, **save_kwargs)
    
    if add_ids:
        add_required_ids(path)


def add_required_ids(path: Path) -> None:
    """Add DocumentID and InstanceID to a file.
    
    These identifiers are normally set by scan-batcher and are required
    by FileProcessor and PreviewMaker before processing.
    """
    exifer = Exifer()
    exifer.write(path, {
        TAG_XMP_XMPMM_DOCUMENT_ID: uuid.uuid4().hex,
        TAG_XMP_XMPMM_INSTANCE_ID: uuid.uuid4().hex,
    })
