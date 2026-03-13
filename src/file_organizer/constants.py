"""
File Organizer-specific constants.
"""

from typing import Any

from common.constants import (
    TAG_XMP_DC_DESCRIPTION,
    TAG_XMP_DC_CREATOR,
    TAG_XMP_PHOTOSHOP_CREDIT,
    TAG_XMP_DC_RIGHTS,
    TAG_XMP_XMPRIGHTS_USAGE_TERMS,
    TAG_XMP_XMPRIGHTS_MARKED,
    TAG_XMP_DC_SOURCE,
)

# Default metadata configuration (tags + languages).
# Used by ArchiveMetadata as built-in fallback when no metadata section is present.
# The "tags" sub-dict maps friendly field names to XMP tags;
# "languages" holds per-language values for those fields.
DEFAULT_METADATA: dict[str, Any] = {
    "tags": {
        "description": TAG_XMP_DC_DESCRIPTION,
        "creator": TAG_XMP_DC_CREATOR,
        "credit": TAG_XMP_PHOTOSHOP_CREDIT,
        "rights": TAG_XMP_DC_RIGHTS,
        "terms": TAG_XMP_XMPRIGHTS_USAGE_TERMS,
        "marked": TAG_XMP_XMPRIGHTS_MARKED,
        "source": TAG_XMP_DC_SOURCE,
    },
    "languages": {
        "en-US": {
            "default": True,
            "creator": [],
            "credit": [],
            "description": [],
            "rights": [],
            "terms": ["All rights reserved."],
            "source": [],
            "type": "StillImage",
            "marked": "True",
        }
    },
}
