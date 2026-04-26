"""
Base classes for content importers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from common.tags import Tag


@dataclass
class ValidationResult:
    """Validation result for a single file."""
    source: Path
    dest: Path | None = None                    # relative path inside archive (folder/filename.ext)
    valid: bool = False
    copied: bool = False
    errors: list[str] = field(default_factory=list[str])


@dataclass
class ValidationReport:
    """Summary report for a batch import operation."""
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total: int = 0
    valid: int = 0
    succeeded: int = 0
    failed: int = 0
    results: list[ValidationResult] = field(default_factory=list[ValidationResult])


@dataclass
class OrganizationResult:
    source: Path
    dest: Path | None = None
    success: bool = False
    copied_at: datetime | None = None
    error: str | None = None


@dataclass
class OrganizationReport:
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    results: list[OrganizationResult] = field(default_factory=list[OrganizationResult])


class Validator(ABC):
    """Abstract base for content-type-specific validators."""

    @abstractmethod
    def validate(self, file_path: Path) -> ValidationResult:
        """Validate a single file and compute its archive destination.

        Args:
            file_path: Path to the source file.

        Returns:
            ValidationResult with valid=True and dest set on success,
            or valid=False with errors describing what is wrong.
        """


class Organizer(ABC):
    """Abstract base for content-type-specific file organizers."""

    @abstractmethod
    def organize(
        self,
        mapping: list[tuple[Path, Path, list[Tag]]],
        *,
        copy_mode: bool = True,
        protect: bool = False,
    ) -> OrganizationReport:
        """Organize files according to the mapping.

        Args:
            mapping: List of (source_path, dest_path, tags) tuples.
            copy_mode: If True, keep source files. If False, delete after success.
            protect: If True, make destination read-only after placement.

        Returns:
            OrganizationReport with per-file results.
        """


class Importer(ABC):
    """Abstract base for content-type-specific importers."""

    @abstractmethod
    def run(self, source_path: Path, archive_path: Path) -> ValidationReport:
        """Import files from source_path into archive_path.

        Args:
            source_path: Folder containing files to import.
            archive_path: Archive root directory.

        Returns:
            ValidationReport with batch summary and per-file results.
        """
