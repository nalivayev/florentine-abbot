"""Project-wide shared constants.

These define canonical directory names and other cross-package conventions so
that tools stay in sync.
"""

# Common set of supported image file extensions (lowercase).
# Used to detect real image files
# and skip sidecar/auxiliary artifacts such as .log, .icc, etc.
SUPPORTED_IMAGE_EXTENSIONS = {".tif", ".tiff", ".jpg", ".jpeg", ".png"}

# ExifTool timeout for large files (in seconds)
# Large files (>100MB) use one-off mode with timeout to prevent hanging
EXIFTOOL_LARGE_FILE_TIMEOUT = 600  # 10 minutes
