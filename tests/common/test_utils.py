"""Common test utilities for creating test fixtures."""

from datetime import datetime
from pathlib import Path

from PIL import Image

from common.constants import (
    TAG_IFD0_MAKE,
    TAG_IFD0_MODEL,
    TAG_IFD0_SOFTWARE,
    TAG_EXIFIFD_CREATE_DATE,
)
from common.exifer import Exifer
from common.logger import Logger
from tests.scan_batcher.fake_metadata_workflow import FakeMetadataWorkflow


def create_test_image(
    path: Path,
    size: tuple[int, int] = (100, 100),
    color: str | tuple = "red",
    format: str | None = None,
    add_ids: bool = True,
    scanner_make: str = "Test Scanner",
    scanner_model: str = "Test Model",
) -> None:
    """Create a test image with optional scanner metadata.
    
    Creates a PIL image and optionally writes scanner metadata that mirrors
    the real scanning workflow:
    1. VueScan EXIF tags (Make, Model, Software, CreateDate without timezone)
    2. scan-batcher metadata via FakeMetadataWorkflow (DocumentID, InstanceID,
       DateTimeDigitized enriched with timezone, XMP History)
    
    Args:
        path: Path where to save the image.
        size: Image size as (width, height).
        color: Fill color (name or RGB tuple).
        format: Image format (TIFF, JPEG, etc). If None, inferred from extension.
        add_ids: If True, add full scanner metadata (VueScan + scan-batcher).
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
    scanner_software: str = "VueScan 9 x64 (9.8.50)",
) -> None:
    """Add scanner metadata matching the real scanning workflow.
    
    Simulates the two-phase metadata writing that happens in production:
    
    Phase 1 — VueScan tags (what the scanner software actually writes):
        - IFD0:Make and IFD0:Model (scanner hardware info)
        - IFD0:Software (scanner software name and version)
        - ExifIFD:CreateDate (scan timestamp without timezone, EXIF format)
    
    Phase 2 — scan-batcher metadata (via FakeMetadataWorkflow):
        - DocumentID and InstanceID (generated if missing)
        - dc:Format (MIME type from file extension)
        - XMP-exif:DateTimeDigitized (enriched with timezone from local time)
        - Exif:OffsetTimeDigitized (timezone offset)
        - XMP History entries (created + edited actions)
    
    This ensures tests use the same code paths as production, so tag formats
    (timestamps, timezone handling, etc.) are identical.
    
    Args:
        path: Path to the file to add metadata to.
        scanner_make: Scanner manufacturer (default: "Test Scanner").
        scanner_model: Scanner model (default: "Test Model").
        scanner_software: Scanner software (default: "VueScan 9 x64 (9.8.50)").
    """
    exifer = Exifer()
    
    # === Phase 1: Simulate VueScan EXIF tags ===
    # VueScan writes CreateDate without timezone, in EXIF format
    now = datetime.now()
    create_date = now.strftime("%Y:%m:%d %H:%M:%S")  # e.g. "2026:02:18 14:30:00"
    
    vuescan_tags = {
        TAG_IFD0_MAKE: scanner_make,
        TAG_IFD0_MODEL: scanner_model,
        TAG_IFD0_SOFTWARE: scanner_software,
        TAG_EXIFIFD_CREATE_DATE: create_date,
    }
    
    exifer.write(path, vuescan_tags)
    
    # === Phase 2: Simulate scan-batcher metadata via real MetadataWorkflow ===
    # Uses the same code path as production: reads existing tags, enriches
    # DateTimeDigitized with timezone, generates IDs, writes XMP History
    logger = Logger("test", console=False)
    workflow = FakeMetadataWorkflow(logger)
    file_datetime = workflow.get_digitized_datetime(path)
    workflow.write_xmp_metadata(path, file_datetime)
