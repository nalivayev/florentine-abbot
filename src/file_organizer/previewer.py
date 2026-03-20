"""
Previewer — formats dry-run results for display.
"""

from typing import Any


class Previewer:
    """Formats the result of a dry-run batch into a human-readable structure."""

    def __init__(self, result: dict[str, Any]) -> None:
        self._result = result

    def sample(self, n: int = 20) -> list[dict[str, str]]:
        """Return up to *n* preview entries (source → destination)."""
        return self._result["preview"][:n]

    def errors(self) -> list[dict[str, str]]:
        """Return all files that could not be routed."""
        return self._result["errors"]

    def summary(self) -> dict[str, int]:
        """Return counts: total, succeeded, failed."""
        return {
            "total": self._result["total"],
            "succeeded": self._result["succeeded"],
            "failed": self._result["failed"],
        }
