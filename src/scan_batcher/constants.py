"""
Constants and enumerations used throughout the scan_batcher package.

This module defines all constants and enums to avoid magic strings
and improve code maintainability.
"""

from enum import Enum


class RoundingStrategy(str, Enum):
    """
    DPI rounding strategy for scanner resolution calculations.
    
    Attributes:
        NEAREST: Round to the nearest available DPI value.
        MAXIMUM: Round up to the next higher DPI value.
        MINIMUM: Round down to the next lower DPI value.
    """
    NEAREST = "nr"
    MAXIMUM = "mx"
    MINIMUM = "mn"
    
    @classmethod
    def from_string(cls, value: str) -> "RoundingStrategy":
        """
        Convert a string to RoundingStrategy enum.
        
        Args:
            value: String representation ("nr", "mx", or "mn")
            
        Returns:
            RoundingStrategy: Corresponding enum value
            
        Raises:
            ValueError: If value is not a valid rounding strategy
        """
        try:
            return cls(value)
        except ValueError:
            valid_values = ", ".join([e.value for e in cls])
            raise ValueError(
                f"Invalid rounding strategy: {value}. "
                f"Valid values are: {valid_values}"
            )
    
    def __str__(self) -> str:
        """
        Return the string value of the enum.
        """
        return self.value


# Conversion constants
CM_TO_INCH = 2.54  # Conversion factor from centimeters to inches

# EXIF date/time formats
EXIF_DATE_FORMAT = "%Y:%m:%d"
EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"
EXIF_DATETIME_FORMAT_MS = "%Y:%m:%d %H:%M:%S.%f"  # With fractional seconds

# Default workflow engine
DEFAULT_ENGINE = "vuescan"

# MIME type mapping for image file extensions.
# Used when writing dc:Format tag to ensure correct MIME types.
# Keys are lowercase extensions without leading dot.
MIME_TYPE_MAP = {
    "tif": "image/tiff",
    "tiff": "image/tiff",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
}

# ExifTool timeout for large files (in seconds)
# Large files (>100MB) use one-off mode with timeout to prevent hanging
EXIFTOOL_LARGE_FILE_TIMEOUT = 600  # 10 minutes

# EXIF/XMP tag names (used across all components for consistent metadata handling)
# Organized by namespace: EXIF, ExifIFD, IFD0, XMP-xmp, XMP-dc, XMP-exif,
# XMP-tiff, XMP-xmpMM

# EXIF tags
TAG_EXIF_OFFSET_TIME_DIGITIZED = "Exif:OffsetTimeDigitized"

# ExifIFD tags
TAG_EXIFIFD_DATETIME_DIGITIZED = "ExifIFD:DateTimeDigitized"
TAG_EXIFIFD_CREATE_DATE = "ExifIFD:CreateDate"

# IFD0 tags
TAG_IFD0_DATETIME = "IFD0:DateTime"
TAG_IFD0_SOFTWARE = "IFD0:Software"
TAG_IFD0_MAKE = "IFD0:Make"
TAG_IFD0_MODEL = "IFD0:Model"

# XMP-xmp tags
TAG_XMP_XMP_CREATOR_TOOL = "XMP-xmp:CreatorTool"

# XMP-dc (Dublin Core) tags
TAG_XMP_DC_FORMAT = "XMP-dc:Format"

# XMP-exif tags
TAG_XMP_EXIF_DATETIME_DIGITIZED = "XMP-exif:DateTimeDigitized"

# XMP-tiff tags
TAG_XMP_TIFF_MAKE = "XMP-tiff:Make"
TAG_XMP_TIFF_MODEL = "XMP-tiff:Model"
TAG_XMP_TIFF_SOFTWARE = "XMP-tiff:Software"

# XMP-xmpMM (Media Management) tags
TAG_XMP_XMPMM_HISTORY = "XMP-xmpMM:History"
TAG_XMP_XMPMM_INSTANCE_ID = "XMP-xmpMM:InstanceID"
TAG_XMP_XMPMM_DOCUMENT_ID = "XMP-xmpMM:DocumentID"

# XMP-xmpMM History flattened tags (exiftool expands structures)
TAG_XMP_XMPMM_HISTORY_ACTION = "XMP-xmpMM:HistoryAction"
TAG_XMP_XMPMM_HISTORY_WHEN = "XMP-xmpMM:HistoryWhen"
TAG_XMP_XMPMM_HISTORY_SOFTWARE_AGENT = "XMP-xmpMM:HistorySoftwareAgent"
TAG_XMP_XMPMM_HISTORY_CHANGED = "XMP-xmpMM:HistoryChanged"
TAG_XMP_XMPMM_HISTORY_PARAMETERS = "XMP-xmpMM:HistoryParameters"
TAG_XMP_XMPMM_HISTORY_INSTANCE_ID = "XMP-xmpMM:HistoryInstanceID"

# XMP History event field names (stEvt namespace)
# Used when building structured History entries
XMP_FIELD_ACTION = "action"
XMP_FIELD_WHEN = "when"
XMP_FIELD_SOFTWARE_AGENT = "softwareAgent"
XMP_FIELD_CHANGED = "changed"
XMP_FIELD_PARAMETERS = "parameters"
XMP_FIELD_INSTANCE_ID = "instanceID"

# Standard XMP History action types per XMP Specification Part 2 (xmpMM namespace)
# Table 8 — ResourceEvent fields: stEvt:action Open Choice of Text
# https://www.adobe.com/devnet/xmp/library/XMPSpecificationPart2.pdf
XMP_ACTION_CREATED = "created"              # File created from scratch
XMP_ACTION_EDITED = "edited"                # Content modification
