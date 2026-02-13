"""Common test utilities for creating test fixtures."""

import uuid
from datetime import datetime
from pathlib import Path

from PIL import Image

from common.constants import (
    MIME_TYPE_MAP,
    XMP_ACTION_CREATED,
    XMP_ACTION_EDITED,
    TAG_XMP_XMPMM_DOCUMENT_ID,
    TAG_XMP_XMPMM_INSTANCE_ID,
    TAG_XMP_DC_FORMAT,
    TAG_IFD0_MAKE,
    TAG_IFD0_MODEL,
    TAG_XMP_TIFF_MAKE,
    TAG_XMP_TIFF_MODEL,
    TAG_IFD0_SOFTWARE,
    TAG_EXIFIFD_CREATE_DATE,
    TAG_XMP_EXIF_DATETIME_DIGITIZED,
    TAG_EXIF_OFFSET_TIME_DIGITIZED,
)
from common.exifer import Exifer
from common.historian import XMPHistorian


def create_test_image(
    path: Path,
    size: tuple[int, int] = (100, 100),
    color: str | tuple = "red",
    format: str | None = None,
    add_ids: bool = True,
    scanner_make: str = "Test Scanner",
    scanner_model: str = "Test Model",
) -> None:
    """Create a test image with optional DocumentID/InstanceID.
    
    Args:
        path: Path where to save the image.
        size: Image size as (width, height).
        color: Fill color (name or RGB tuple).
        format: Image format (TIFF, JPEG, etc). If None, inferred from extension.
        add_ids: If True, add DocumentID/InstanceID required by FileProcessor/PreviewMaker.
        scanner_make: Scanner manufacturer (default: "Test Scanner").
        scanner_model: Scanner model (default: "Test Model").
    """
    img = Image.new("RGB", size, color=color)
    
    save_kwargs = {}
    if format:
        save_kwargs["format"] = format
    
    img.save(path, **save_kwargs)
    
    if add_ids:
        add_scanner_metadata(path, scanner_make=scanner_make, scanner_model=scanner_model)


def add_scanner_metadata(
    path: Path,
    scanner_make: str = "Test Scanner",
    scanner_model: str = "Test Model",
) -> None:
    """Add comprehensive scanner metadata matching scan-batcher output.
    
    Writes all metadata tags that scan-batcher normally adds:
    - DocumentID and InstanceID (required by FileProcessor/PreviewMaker)
    - dc:Format (MIME type from file extension)
    - DateTimeDigitized and OffsetTimeDigitized (scan timestamp)
    - IFD0:Software (scanner software name, e.g., VueScan)
    - ExifIFD:CreateDate (scan date in EXIF format, shows as "Дата съемки" in Windows)
    - IFD0:Make and IFD0:Model (scanner metadata)
    - XMP-tiff:Make and XMP-tiff:Model (XMP versions visible in Windows Properties)
    - XMP History entries (created + edited actions)
    
    Args:
        path: Path to the file to add metadata to.
        scanner_make: Scanner manufacturer (default: "Test Scanner").
        scanner_model: Scanner model (default: "Test Model").
    """
    exifer = Exifer()
    document_id = uuid.uuid4().hex
    instance_id = uuid.uuid4().hex
    
    # Get MIME type from extension
    extension = path.suffix.lower().lstrip('.')
    dc_format = MIME_TYPE_MAP.get(extension)
    
    # Get current timestamp with timezone for DateTimeDigitized
    now = datetime.now().astimezone()
    dt_digitized = now.isoformat(timespec='milliseconds')  # Format: 2026-02-12T23:03:26.000+03:00
    offset_digitized = now.strftime("%z")
    offset_digitized = f"{offset_digitized[:3]}:{offset_digitized[3:]}"  # Format: +03:00
    
    # Format CreateDate in EXIF format (without timezone)
    create_date = now.strftime("%Y:%m:%d %H:%M:%S")  # Format: 2026:02:13 12:34:56
    
    # Build tags dictionary
    tags = {
        TAG_XMP_XMPMM_DOCUMENT_ID: document_id,
        TAG_XMP_XMPMM_INSTANCE_ID: instance_id,
        TAG_IFD0_MAKE: scanner_make,
        TAG_IFD0_MODEL: scanner_model,
        TAG_XMP_TIFF_MAKE: scanner_make,
        TAG_XMP_TIFF_MODEL: scanner_model,
        TAG_IFD0_SOFTWARE: "VueScan 9 x64 (9.8.50)",
        TAG_EXIFIFD_CREATE_DATE: create_date,
        TAG_XMP_EXIF_DATETIME_DIGITIZED: dt_digitized,
        TAG_EXIF_OFFSET_TIME_DIGITIZED: offset_digitized,
    }
    if dc_format:
        tags[TAG_XMP_DC_FORMAT] = dc_format
    
    exifer.write(path, tags)
    
    # Add XMP History
    historian = XMPHistorian(exifer=exifer)
    now_local = datetime.now().astimezone()
    historian.append_entry(path, XMP_ACTION_CREATED, "scan-batcher", now_local, instance_id=instance_id)
    historian.append_entry(path, XMP_ACTION_EDITED, "scan-batcher", now_local, changed="metadata", instance_id=instance_id)
