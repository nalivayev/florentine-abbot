from abc import ABC, abstractmethod


class Workflow(ABC):
    """
    Abstract base class for all workflow plugins.
    All workflow classes must inherit from this class and implement the __call__ method.
    """

    def __init__(self) -> None:
        """Initialize the workflow."""
        pass

    @abstractmethod
    def __call__(self, workflow_path: str, templates: dict[str, str]) -> None:
        """
        Execute the workflow.

        Args:
            workflow_path: Path to the workflow configuration directory.
            templates: Dictionary of template values.

        Raises:
            RuntimeError: For workflow-specific errors.
        """
        pass
