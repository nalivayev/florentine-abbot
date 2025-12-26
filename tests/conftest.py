"""Common pytest fixtures for all tests."""

import pytest
from common.logger import Logger


@pytest.fixture
def logger():
    """Create a logger for testing."""
    return Logger("test")
