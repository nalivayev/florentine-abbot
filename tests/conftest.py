"""
Common pytest fixtures for all tests.
"""

from pathlib import Path
import sys

import pytest


# Ensure local ``src`` packages are imported before any similarly named
# third-party packages installed in the environment.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# Drop any pre-imported ``common`` package so tests always use the
# project-local implementation from ``src/common``.
for module_name in ["common", "common.logger", "common.constants"]:
    sys.modules.pop(module_name, None)

from common.logger import Logger


@pytest.fixture
def logger():
    """
    Create a logger for testing.
    """
    return Logger("test")


@pytest.fixture
def require_exiftool():
    """
    Skip the test if exiftool is not installed or not runnable.
    """
    from tests.common.test_utils import exiftool_available

    if not exiftool_available():
        pytest.skip("ExifTool not found")
