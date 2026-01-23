"""File routing logic for organizing files in the archive structure.

This module provides the Router class that determines target folders
for files based on parsed filename data and routing configuration.
Used by both file-organizer and preview-maker.
"""

from pathlib import Path
from typing import Optional

from common.naming import ParsedFilename
from common.constants import DERIVATIVES_DIR_NAME, DEFAULT_SUFFIX_ROUTING


class Router:
    """Determines target folders for files based on routing rules.
    
    The Router uses suffix-based routing rules to determine where files
    should be placed in the archive structure:
    
    Archive structure:
        archive_root/YYYY/YYYY.MM.DD/
            ├── SOURCES/      - Raw scans and master files
            ├── DERIVATIVES/  - Processed derivatives
            └── (date folder)  - Preview files stored directly here
    
    Routing is configured via a suffix mapping (suffix -> subfolder):
        - "SOURCES": File goes to SOURCES/ subfolder
        - "DERIVATIVES": File goes to DERIVATIVES/ subfolder
        - ".": File goes directly to date folder root
    """
    
    def __init__(self, suffix_routing: Optional[dict[str, str]] = None, logger = None):
        """Initialize Router.
        
        Args:
            suffix_routing: Optional suffix routing rules (suffix -> 'SOURCES'/'DERIVATIVES'/'.').  
                           If None, loads from routes.json or uses DEFAULT_SUFFIX_ROUTING.
            logger: Optional logger for diagnostic messages.
        """
        if suffix_routing is not None:
            self._suffix_routing = suffix_routing
        else:
            # Load from routes.json if available
            from common.config_utils import get_config_dir, load_optional_config
            config_dir = get_config_dir()
            routes_path = config_dir / "routes.json"
            
            # Try to copy template if routes.json doesn't exist
            if not routes_path.exists():
                from common.config_utils import get_template_path
                template_path = get_template_path('common', 'routes.template.json')
                if template_path and template_path.exists():
                    if logger:
                        logger.info(f"Creating {routes_path} from template")
                    routes_path.parent.mkdir(parents=True, exist_ok=True)
                    import shutil
                    shutil.copy2(template_path, routes_path)
            
            self._suffix_routing = load_optional_config(logger, routes_path, DEFAULT_SUFFIX_ROUTING)
    
    def get_target_folder(self, parsed: ParsedFilename, base_path: Path) -> Path:
        """Determine target folder for a file based on parsed filename.
        
        Args:
            parsed: Parsed filename data
            base_path: Base path (e.g., archive root or processed root)
        
        Returns:
            Full path to target folder where file should be placed
        """
        # Build folder structure: YYYY/YYYY.MM.DD/[SOURCES|DERIVATIVES]/
        year_dir = f"{parsed.year:04d}"
        date_dir = f"{parsed.year:04d}.{parsed.month:02d}.{parsed.day:02d}"
        
        suffix_upper = parsed.suffix.upper()
        
        date_root_dir = base_path / year_dir / date_dir
        
        # Get subfolder name from routing rules
        subfolder = self._suffix_routing.get(suffix_upper, DERIVATIVES_DIR_NAME)
        
        # "." means store directly in date folder root (e.g., preview files)
        if subfolder == ".":
            return date_root_dir
        else:
            return date_root_dir / subfolder
    
    def get_normalized_filename(self, parsed: ParsedFilename) -> str:
        """Get normalized filename with leading zeros.
        
        Args:
            parsed: Parsed filename data
        
        Returns:
            Normalized filename (without extension)
        """
        return (
            f"{parsed.year:04d}.{parsed.month:02d}.{parsed.day:02d}."
            f"{parsed.hour:02d}.{parsed.minute:02d}.{parsed.second:02d}."
            f"{parsed.modifier}.{parsed.group}.{parsed.subgroup}.{int(parsed.sequence):04d}."
            f"{parsed.side}.{parsed.suffix}"
        )
    
    def get_folders_for_suffixes(self, suffixes: list[str]) -> set[str]:
        """Get unique folder names where files with given suffixes are stored.
        
        Args:
            suffixes: List of file suffixes (e.g., ['RAW', 'MSR'])
        
        Returns:
            Set of folder names (e.g., {'SOURCES', 'MASTERS'}). 
            '.' is excluded as it represents date root, not a subfolder.
        """
        folders = set()
        for suffix in suffixes:
            suffix_upper = suffix.upper()
            folder = self._suffix_routing.get(suffix_upper, DERIVATIVES_DIR_NAME)
            if folder != ".":  # Exclude date root
                folders.add(folder)
        return folders
