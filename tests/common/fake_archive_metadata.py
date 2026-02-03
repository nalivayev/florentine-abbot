"""Fake ArchiveMetadata for testing."""

from typing import Any, Optional

from common.metadata import ArchiveMetadata
from common.constants import DEFAULT_METADATA_TAGS, DEFAULT_METADATA
from common.logger import Logger


class FakeArchiveMetadata(ArchiveMetadata):
    """Fake ArchiveMetadata that accepts custom config for testing.
    
    Since ArchiveMetadata is now a thin configuration provider (no Exifer),
    this fake just allows injecting custom metadata_config and metadata_tags
    without loading from files.
    """
    
    def __init__(
        self,
        metadata_config: Optional[dict[str, Any]] = None,
        metadata_tags: Optional[dict[str, str]] = None,
        logger: Optional[Logger] = None,
    ):
        """Initialize FakeArchiveMetadata with custom config.
        
        Args:
            metadata_config: Custom metadata configuration for testing.
            metadata_tags: Custom metadata tags mapping for testing.
            logger: Optional logger for testing.
        """
        # Don't call super().__init__() - it would load real configs
        self._logger = logger
        self._metadata_tags = metadata_tags if metadata_tags is not None else DEFAULT_METADATA_TAGS
        self._metadata_config = metadata_config if metadata_config is not None else DEFAULT_METADATA
