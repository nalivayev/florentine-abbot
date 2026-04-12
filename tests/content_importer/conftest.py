import pytest

from common.constants import DEFAULT_CONFIG
from common.project_config import ProjectConfig


@pytest.fixture(autouse=True)
def reset_project_config():
    """Ensure ProjectConfig is initialized with DEFAULT_CONFIG for every test."""
    ProjectConfig.instance(data=DEFAULT_CONFIG)
