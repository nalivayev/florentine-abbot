"""Project-wide shared constants.

These define canonical directory names and other cross-package conventions so
that tools like File Organizer and Preview Maker stay in sync.
"""

# Common set of supported image file extensions (lowercase).
# Used by File Organizer and Preview Maker to detect real image files
# and skip sidecar/auxiliary artifacts such as .log, .icc, etc.
SUPPORTED_IMAGE_EXTENSIONS = {".tif", ".tiff", ".jpg", ".jpeg", ".png"}

# ExifTool timeout for large files (in seconds)
# Large files (>100MB) use one-off mode with timeout to prevent hanging
EXIFTOOL_LARGE_FILE_TIMEOUT = 600  # 10 minutes

# Default metadata field to XMP tag mapping
# Used by ArchiveMetadata when tags.json is not present
DEFAULT_METADATA_TAGS = {
    "description": "XMP-dc:Description",
    "credit": "XMP-photoshop:Credit",
    "rights": "XMP-dc:Rights",
    "terms": "XMP-xmpRights:UsageTerms",
    "source": "XMP-dc:Source",
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

# Default path and filename formatting templates
# Used by Formatter when formats.json is not present
# Path template defines the folder structure from base_path to date folder
DEFAULT_PATH_TEMPLATE = "{year:04d}/{year:04d}.{month:02d}.{day:02d}"

# Filename template defines the normalized filename (without extension)
DEFAULT_FILENAME_TEMPLATE = "{year:04d}.{month:02d}.{day:02d}.{hour:02d}.{minute:02d}.{second:02d}.{modifier}.{group}.{subgroup}.{sequence:04d}.{side}.{suffix}"
