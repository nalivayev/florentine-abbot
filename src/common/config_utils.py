"""Configuration utilities for florentine-abbot tools."""

import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def get_config_dir() -> Path:
    """
    Get the standard configuration directory for florentine-abbot.
    
    Returns:
        Path to the configuration directory.
    """
    if sys.platform == 'win32':
        # Windows: %APPDATA%\florentine-abbot
        config_dir = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming')) / 'florentine-abbot'
    else:
        # Linux/Unix: ~/.config/florentine-abbot
        config_dir = Path.home() / '.config' / 'florentine-abbot'
    
    return config_dir


def get_config_path(tool_name: str, custom_path: str | Path | None = None) -> Path:
    """
    Get the path to a tool's configuration file.
    
    Args:
        tool_name: Name of the tool (e.g., 'file-organizer', 'archive-keeper').
        custom_path: Optional custom path to config file.
        
    Returns:
        Path object for the config file.
    """
    if custom_path:
        return Path(custom_path)
    
    config_dir = get_config_dir()
    return config_dir / f"{tool_name}.json"


def ensure_config_exists(
    config_path: Path,
    template_content: dict[str, Any] | None = None,
    template_path: Path | None = None
) -> bool:
    """
    Ensure configuration file exists, creating it from template if needed.
    
    Args:
        config_path: Path where config should exist.
        template_content: Dictionary with default config (if no template file).
        template_path: Path to template file to copy from.
        
    Returns:
        True if config was created, False if it already existed.
    """
    if config_path.exists():
        return False
    
    logger.info(f"Config not found at {config_path}, creating from template")
    
    # Create parent directory
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Try to copy from template file
    if template_path and template_path.exists():
        try:
            shutil.copy2(template_path, config_path)
            logger.info(f"Created config from template: {template_path}")
            return True
        except Exception as e:
            logger.warning(f"Failed to copy template: {e}")
    
    # Fall back to template content
    if template_content:
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(template_content, f, indent=2, ensure_ascii=False)
            logger.info(f"Created default config at {config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create default config: {e}")
            return False
    
    logger.error("No template content or file provided")
    return False


def load_config(config_path: Path) -> dict[str, Any]:
    """
    Load configuration from JSON file.
    
    Args:
        config_path: Path to config file.
        
    Returns:
        Configuration dictionary, or empty dict if loading fails.
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.debug(f"Loaded config from {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}


def get_template_path(module_name: str, filename: str = "config.template.json") -> Path | None:
    """
    Get path to template file from installed package.
    
    Args:
        module_name: Name of the module (e.g., 'file_organizer').
        filename: Template filename.
        
    Returns:
        Path to template file, or None if not found.
    """
    try:
        import importlib.resources as resources
        # Python 3.9+ approach
        try:
            package = resources.files(module_name)
            template = package / filename
            if template.is_file():
                return Path(str(template))
        except AttributeError:
            # Fallback for older Python
            pass
    except Exception:
        pass
    
    # Fallback: try to find in source tree
    try:
        import sys
        for path in sys.path:
            candidate = Path(path) / module_name / filename
            if candidate.exists():
                return candidate
    except Exception:
        pass
    
    return None
