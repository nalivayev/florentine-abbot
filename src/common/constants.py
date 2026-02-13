"""Project-wide shared constants.

These define canonical directory names and other cross-package conventions so
that tools like File Organizer and Preview Maker stay in sync.
"""

# Common set of supported image file extensions (lowercase).
# Used by File Organizer and Preview Maker to detect real image files
# and skip sidecar/auxiliary artifacts such as .log, .icc, etc.
SUPPORTED_IMAGE_EXTENSIONS = {".tif", ".tiff", ".jpg", ".jpeg", ".png"}

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

# EXIF/XMP tag names
# Used across all components for consistent metadata handling
# Organized by namespace: EXIF, ExifIFD, IFD0, XMP-xmp, XMP-dc, XMP-exif,
# XMP-photoshop, XMP-xmpRights, XMP-tiff, XMP-xmpMM

# EXIF tags
TAG_EXIF_DATETIME_ORIGINAL = "Exif:DateTimeOriginal"
TAG_EXIF_OFFSET_TIME_DIGITIZED = "Exif:OffsetTimeDigitized"

# ExifIFD tags
TAG_EXIFIFD_DATETIME_DIGITIZED = "ExifIFD:DateTimeDigitized"
TAG_EXIFIFD_CREATE_DATE = "ExifIFD:CreateDate"

# IFD0 tags
TAG_IFD0_SOFTWARE = "IFD0:Software"
TAG_IFD0_MAKE = "IFD0:Make"
TAG_IFD0_MODEL = "IFD0:Model"

# XMP-xmp tags
TAG_XMP_XMP_IDENTIFIER = "XMP-xmp:Identifier"
TAG_XMP_XMP_CREATOR_TOOL = "XMP-xmp:CreatorTool"

# XMP-dc (Dublin Core) tags
TAG_XMP_DC_IDENTIFIER = "XMP-dc:Identifier"
TAG_XMP_DC_DESCRIPTION = "XMP-dc:Description"
TAG_XMP_DC_TITLE = "XMP-dc:Title"
TAG_XMP_DC_CREATOR = "XMP-dc:Creator"
TAG_XMP_DC_RIGHTS = "XMP-dc:Rights"
TAG_XMP_DC_SOURCE = "XMP-dc:Source"
TAG_XMP_DC_RELATION = "XMP-dc:Relation"
TAG_XMP_DC_FORMAT = "XMP-dc:Format"

# XMP-exif tags
TAG_XMP_EXIF_DATETIME_DIGITIZED = "XMP-exif:DateTimeDigitized"

# XMP-photoshop tags
TAG_XMP_PHOTOSHOP_DATE_CREATED = "XMP-photoshop:DateCreated"
TAG_XMP_PHOTOSHOP_CREDIT = "XMP-photoshop:Credit"

# XMP-xmpRights tags
TAG_XMP_XMPRIGHTS_USAGE_TERMS = "XMP-xmpRights:UsageTerms"

# XMP-tiff tags
TAG_XMP_TIFF_MAKE = "XMP-tiff:Make"
TAG_XMP_TIFF_MODEL = "XMP-tiff:Model"

# XMP-xmpMM (Media Management) tags
TAG_XMP_XMPMM_HISTORY = "XMP-xmpMM:History"
TAG_XMP_XMPMM_INSTANCE_ID = "XMP-xmpMM:InstanceID"
TAG_XMP_XMPMM_DOCUMENT_ID = "XMP-xmpMM:DocumentID"
TAG_XMP_XMPMM_DERIVED_FROM_DOCUMENT_ID = "XMP-xmpMM:DerivedFromDocumentID"
TAG_XMP_XMPMM_DERIVED_FROM_INSTANCE_ID = "XMP-xmpMM:DerivedFromInstanceID"

# XMP-xmpMM History flattened tags (exiftool expands structures)
TAG_XMP_XMPMM_HISTORY_ACTION = "XMP-xmpMM:HistoryAction"
TAG_XMP_XMPMM_HISTORY_WHEN = "XMP-xmpMM:HistoryWhen"
TAG_XMP_XMPMM_HISTORY_SOFTWARE_AGENT = "XMP-xmpMM:HistorySoftwareAgent"
TAG_XMP_XMPMM_HISTORY_CHANGED = "XMP-xmpMM:HistoryChanged"
TAG_XMP_XMPMM_HISTORY_PARAMETERS = "XMP-xmpMM:HistoryParameters"
TAG_XMP_XMPMM_HISTORY_INSTANCE_ID = "XMP-xmpMM:HistoryInstanceID"

# Tag groupings for easier reuse
IDENTIFIER_TAGS = (TAG_XMP_DC_IDENTIFIER, TAG_XMP_XMP_IDENTIFIER)
DATE_TAGS = (
    TAG_EXIF_DATETIME_ORIGINAL,
    TAG_XMP_PHOTOSHOP_DATE_CREATED,
    TAG_XMP_EXIF_DATETIME_DIGITIZED,
)

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

# Default metadata field to XMP tag mapping
# Used by ArchiveMetadata when tags.json is not present
DEFAULT_METADATA_TAGS = {
    "description": TAG_XMP_DC_DESCRIPTION,
    "creator": TAG_XMP_DC_CREATOR,
    "credit": TAG_XMP_PHOTOSHOP_CREDIT,
    "rights": TAG_XMP_DC_RIGHTS,
    "terms": TAG_XMP_XMPRIGHTS_USAGE_TERMS,
    "source": TAG_XMP_DC_SOURCE,
}

# Default metadata configuration
# Used by ArchiveMetadata when metadata.json is not present
DEFAULT_METADATA = {
    "languages": {}
}

# Default suffix routing rules
# Used by FileProcessor when routes.json is not present
# Maps file suffix (uppercase) to subdirectory name:
#   "." = date root (no subfolder)
#   "SOURCES" = SOURCES/ subfolder
#   "DERIVATIVES" = DERIVATIVES/ subfolder
#   "*" = default for unknown suffixes
DEFAULT_SUFFIX_ROUTING = {
    "RAW": "SOURCES",
    "MSR": "SOURCES",
    "PRV": ".",
    "*": "DERIVATIVES",
}
