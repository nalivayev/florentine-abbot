"""
File path and filename formatting based on templates.

This module provides the Formatter class which applies configurable templates
to format archive paths and filenames from parsed filename components.
"""

import json
from typing import Optional

from common.config_utils import get_config_dir
from common.logger import Logger
from common.naming import ParsedFilename


# Default path template (kept local to Formatter since it's only used here)
DEFAULT_PATH_TEMPLATE = "{year:04d}/{year:04d}.{month:02d}.{day:02d}"

# Filename template defines the normalized filename (without extension)
DEFAULT_FILENAME_TEMPLATE = "{year:04d}.{month:02d}.{day:02d}.{hour:02d}.{minute:02d}.{second:02d}.{modifier}.{group}.{subgroup}.{sequence:04d}.{side}.{suffix}"
    
class Formatter:
    """
    Formats file paths and names using configurable templates.
    
    Templates use Python string formatting with fields from ParsedFilename:
    - {year}, {month}, {day}, {hour}, {minute}, {second}
    - {modifier}, {group}, {subgroup}, {sequence}, {side}, {suffix}, {extension}
    
    Format specifiers are supported: {month:02d}, {sequence:04d}, etc.
    
    Templates are loaded from formats.json in user config directory,
    or default templates from constants are used.
    """

    def __init__(
        self,
        path_template: Optional[str] = None,
        filename_template: Optional[str] = None,
        logger: Optional[Logger] = None
    ):
        """
        Initialize Formatter with templates.
        
        Args:
            path_template: Template for folder path (e.g., "{year}/{year}.{month:02d}.{day:02d}")
                          If None, loads from formats.json or uses DEFAULT_PATH_TEMPLATE
            filename_template: Template for filename without extension
                              If None, loads from formats.json or uses DEFAULT_FILENAME_TEMPLATE
            logger: Optional logger instance
        """
        self.logger = logger or Logger("formatter")
        
        # Load templates from config or use provided/defaults
        if path_template is None or filename_template is None:
            config_templates = self._load_formats_config()
            self.path_template = path_template or config_templates.get("path_template", DEFAULT_PATH_TEMPLATE)
            self.filename_template = filename_template or config_templates.get("filename_template", DEFAULT_FILENAME_TEMPLATE)
        else:
            self.path_template = path_template
            self.filename_template = filename_template
            
        self.logger.debug(f"Formatter initialized with path_template: {self.path_template}")
        self.logger.debug(f"Formatter initialized with filename_template: {self.filename_template}")
    
    def _load_formats_config(self) -> dict:
        """
        Load formats.json from user config directory.
        
        Returns:
            Dictionary with path_template and filename_template, or empty dict if not found
        """
        config_dir = get_config_dir()
        formats_path = config_dir / "formats.json"
        
        if not formats_path.exists():
            self.logger.debug(f"formats.json not found at {formats_path}, using defaults")
            return {}
        
        try:
            with open(formats_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.logger.info(f"Loaded formats.json from {formats_path}")
                return config
        except Exception as e:
            self.logger.warning(f"Failed to load formats.json: {e}, using defaults")
            return {}
    
    def format_path(self, parsed: ParsedFilename) -> str:
        """
        Format the folder path from parsed filename components.
        
        Args:
            parsed: Parsed filename components
            
        Returns:
            Formatted path string (e.g., "2024/2024.01.15")
        """
        try:
            return self.path_template.format(
                year=parsed.year,
                month=parsed.month,
                day=parsed.day,
                hour=parsed.hour,
                minute=parsed.minute,
                second=parsed.second,
                modifier=parsed.modifier,
                group=parsed.group,
                subgroup=parsed.subgroup,
                sequence=int(parsed.sequence),
                side=parsed.side,
                suffix=parsed.suffix,
                extension=parsed.extension
            )
        except KeyError as e:
            self.logger.error(f"Missing field in path_template: {e}")
            raise ValueError(f"Invalid path_template: missing field {e}")
        except Exception as e:
            self.logger.error(f"Failed to format path: {e}")
            raise
    
    def format_filename(self, parsed: ParsedFilename) -> str:
        """
        Format the filename (without extension) from parsed components.

        Args:
            parsed (ParsedFilename): Parsed filename components.
        Returns:
            str: Formatted filename without extension (e.g., "2024.01.15.10.30.45.E.FAM.POR.0001.A.RAW").
        """
        try:
            return self.filename_template.format(
                year=parsed.year,
                month=parsed.month,
                day=parsed.day,
                hour=parsed.hour,
                minute=parsed.minute,
                second=parsed.second,
                modifier=parsed.modifier,
                group=parsed.group,
                subgroup=parsed.subgroup,
                sequence=int(parsed.sequence),
                side=parsed.side,
                suffix=parsed.suffix,
                extension=parsed.extension
            )
        except KeyError as e:
            self.logger.error(f"Missing field in filename_template: {e}")
            raise ValueError(f"Invalid filename_template: missing field {e}")
        except Exception as e:
            self.logger.error(f"Failed to format filename: {e}")
            raise
