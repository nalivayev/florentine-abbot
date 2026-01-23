"""Configuration management for file organizer."""

from pathlib import Path
from typing import Any

from common.logger import Logger
from common.config_utils import (
    get_config_path,
    get_config_dir,
    ensure_config_exists,
    load_config,
    load_optional_config,
    get_template_path
)
from common.constants import DEFAULT_METADATA_TAGS, DEFAULT_SUFFIX_ROUTING


class Config:
    """Configuration manager for file organizer."""
    
    def __init__(self, logger: Logger, config_path: str | Path | None = None):
        """
        Initialize configuration.
        
        Args:
            logger: Logger instance for this config.
            config_path: Path to JSON config file. If None, uses standard location.
        """
        self.logger = logger
        # Get config path (custom or standard location)
        self.config_path = get_config_path('file-organizer', config_path)
        
        # Ensure config exists, create from template if needed
        template_path = get_template_path('file_organizer', 'config.template.json')
        default_config = {
            "_comment": "Configuration for File Organizer",
            "metadata": {
                "_comment": [
                    "Human-readable metadata texts (see config.template.json for full example).",
                    "languages: keys are BCP-47 codes like 'ru-RU', 'en-US'."
                ],
                "languages": {}
            }
        }
        
        if ensure_config_exists(self.logger, self.config_path, default_config, template_path):
            self.logger.info(f"Created new config at {self.config_path}")
            self.logger.info("Please edit the configuration file and restart")
        
        # Load configuration
        self.data: dict[str, Any] = {}
        self._load()
    
    def _load(self) -> None:
        """Load configuration from file."""
        self.data = load_config(self.logger, self.config_path)
        if self.data:
            self.logger.info(f"Loaded configuration from {self.config_path}")
        else:
            self.logger.warning("Using empty configuration")
    
    def reload(self) -> bool:
        """
        Reload configuration from file.
        
        Returns:
            True if reload was successful, False otherwise.
        """
        old_data = self.data.copy()
        self._load()
        
        if self.data != old_data:
            self.logger.info("Configuration reloaded successfully")
            return True
        else:
            self.logger.debug("Configuration unchanged")
            return False
    
    def get_metadata(self) -> dict[str, Any]:
        """Get metadata configuration block used for XMP fields.

        Returns the raw ``metadata`` section from the config, which is
        expected to contain a ``languages`` mapping. ``ArchiveMetadata`` is
        responsible for interpreting this structure and writing appropriate
        XMP/LangAlt tags.
        """

        metadata = self.data.get("metadata")
        if not isinstance(metadata, dict):
            raise ValueError("File Organizer config must contain a 'metadata' object")

        return metadata
    
    def get_metadata_tags(self) -> dict[str, str]:
        """Get metadata field to XMP tag mapping.
        
        Loads from tags.json if present, otherwise uses DEFAULT_METADATA_TAGS.
        
        Returns:
            Dictionary mapping field names to XMP tag names.
        """
        config_dir = get_config_dir()
        tags_path = config_dir / "tags.json"
        
        # If tags.json doesn't exist, try to copy template from common/
        if not tags_path.exists():
            template_path = get_template_path('common', 'tags.template.json')
            if template_path and template_path.exists():
                self.logger.info(f"Creating {tags_path} from template")
                tags_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(template_path, tags_path)
        
        return load_optional_config(self.logger, tags_path, DEFAULT_METADATA_TAGS)
    
    def get_suffix_routing(self) -> dict[str, str]:
        """Get suffix routing rules.
        
        Loads from routes.json if present, otherwise uses DEFAULT_SUFFIX_ROUTING.
        
        Returns:
            Dictionary mapping file suffixes to subfolder names ('SOURCES', 'DERIVATIVES', '.', etc.).
        """
        config_dir = get_config_dir()
        routes_path = config_dir / "routes.json"
        
        return load_optional_config(self.logger, routes_path, DEFAULT_SUFFIX_ROUTING)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key.
            default: Default value if key not found.
            
        Returns:
            Configuration value or default.
        """
        return self.data.get(key, default)
