"""Project-wide shared constants.

These define canonical directory names and other cross-package conventions so
that tools stay in sync.
"""

# Common set of supported image file extensions (lowercase).
# Used to detect real image files
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
