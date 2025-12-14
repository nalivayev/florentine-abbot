"""Filename parser for structured photo filenames."""

import re
from dataclasses import dataclass
from typing import Pattern


@dataclass
class ParsedFilename:
    """Parsed filename data.
    
    Represents a structured photo filename broken down into its components:
    date, time, modifier, group/subgroup, sequence, side, suffix, and extension.
    """

    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int
    modifier: str
    group: str
    subgroup: str
    sequence: str
    side: str
    suffix: str
    extension: str


class FilenameParser:
    """Parser for structured photo filenames.

    Expected format: YYYY.MM.DD.HH.NN.SS.X.GGG.SSS.NNNN.SIDE.SUFFIX.ext
    
    Components:
        - YYYY.MM.DD: Date
        - HH.NN.SS: Time
        - X: Modifier (A=absent, B=before, C=circa, E=exact, F=after)
        - GGG: Group identifier
        - SSS: Subgroup identifier
        - NNNN: Sequence number (0001-9999)
        - SIDE: A (avers) or R (revers)
        - SUFFIX: Additional identifier (e.g., RAW, MSR)
        - ext: File extension
    """

    # Pattern to match the filename format
    # First 10 components are required, plus Side (A/R), Suffix, and Extension
    PATTERN: Pattern[str] = re.compile(
        r"^(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)\.([a-zA-Z])\.([^.]+)\.([^.]+)\.(\d+)"
        r"\.([ARar])"       # Side (A/R)
        r"\.([^.]+)"        # Suffix
        r"\.([a-zA-Z]+)$",  # Extension
        re.IGNORECASE
    )

    def __init__(self) -> None:
        """Initialize the parser."""
        pass

    def parse(self, filename: str) -> ParsedFilename | None:
        """Parse a filename into components.

        Args:
            filename: Filename to parse.

        Returns:
            ParsedFilename object if parsing successful, None otherwise.
        """
        match = self.PATTERN.match(filename)
        if not match:
            return None

        try:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            second = int(match.group(6))
            modifier = match.group(7)
            group = match.group(8)
            subgroup = match.group(9)
            sequence = match.group(10)
            side = match.group(11)
            suffix = match.group(12)
            extension = match.group(13)

            return ParsedFilename(
                year=year,
                month=month,
                day=day,
                hour=hour,
                minute=minute,
                second=second,
                modifier=modifier.upper(),  # Normalize to uppercase
                group=group,
                subgroup=subgroup,
                sequence=sequence,
                side=side.upper(),          # Normalize to uppercase
                suffix=suffix,
                extension=extension.lower()  # Normalize to lowercase
            )

        except (ValueError, IndexError):
            return None
