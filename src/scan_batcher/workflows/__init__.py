import importlib
import pkgutil
import sys
from pathlib import Path
from typing import Callable
from importlib.metadata import entry_points

from scan_batcher.workflow import Workflow  # base class

_workflows: dict[str, type[Workflow]] = {}


def register_workflow(name: str) -> Callable[[type[Workflow]], type[Workflow]]:
    """
    Decorator for registering workflow classes.

    Args:
        name (str): Engine name (e.g., 'vuescan').

    Returns:
        Callable: Class decorator.
    """
    def decorator(cls: type[Workflow]) -> type[Workflow]:
        _workflows[name] = cls
        return cls
    return decorator


def get_workflow(name: str) -> type[Workflow]:
    """
    Get a registered workflow class by engine name.

    Args:
        name (str): Engine name.

    Returns:
        type[Workflow]: Workflow class.

    Raises:
        ValueError: If the workflow is not registered.
    """
    if name not in _workflows:
        raise ValueError(f"Unknown workflow: {name}")
    return _workflows[name]


def load_workflows() -> None:
    """
    Loads all built-in and external workflow plugins.

    1. Imports all workflow modules in subpackages of the current package.
    2. Loads external plugins via entry points (group 'scan_batcher.workflows').
    """
    # Import all built-in workflow modules
    package_dir = Path(__file__).parent
    for _, subpkg, _ in pkgutil.iter_modules([str(package_dir)]):
        subpkg_path = package_dir / subpkg
        if (subpkg_path / "workflow.py").exists():
            importlib.import_module(f".{subpkg}.workflow", package=__name__)

    # Load external plugins via entry points
    try:
        plugin_group = "scan_batcher.workflows"
        
        if sys.version_info >= (3, 10):
            plugins = entry_points(group=plugin_group)
        else:
            eps = entry_points()
            plugins = eps.get(plugin_group, [])  # type: ignore

        for ep in plugins:
            workflow_class = ep.load()
            _workflows[ep.name] = workflow_class
    except ImportError:
        pass


load_workflows()
