"""
Base classes for content importers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Result:
    """Validation result for a single file."""
    source: Path
    dest: Path | None = None                    # relative path inside archive (folder/filename.ext)
    valid: bool = False
    copied: bool = False
    errors: list[str] = field(default_factory=list[str])


@dataclass
class Report:
    """Summary report for a batch import operation."""
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total: int = 0
    valid: int = 0
    succeeded: int = 0
    failed: int = 0
    results: list[Result] = field(default_factory=list[Result])


class Validator(ABC):
    """Abstract base for content-type-specific validators."""

    @abstractmethod
    def validate(self, file_path: Path) -> Result:
        """Validate a single file and compute its archive destination.

        Args:
            file_path: Path to the source file.

        Returns:
            Result with valid=True and dest set on success,
            or valid=False with errors describing what is wrong.
        """


class Importer(ABC):
    """Abstract base for content-type-specific importers."""

    @abstractmethod
    def run(self, source_path: Path, archive_path: Path) -> Report:
        """Import files from source_path into archive_path.

        Args:
            source_path: Folder containing files to import.
            archive_path: Archive root directory.

        Returns:
            Report with batch summary and per-file results.
        """
