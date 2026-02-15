"""Filename parsing and validation utilities shared across tools.

Provides :class:`ParsedFilename`, :class:`FilenameParser` and
 :class:`FilenameValidator` implementing the canonical Florentine Abbot
 naming scheme, used by both File Organizer and Preview Maker.
"""

import calendar
import re
from dataclasses import dataclass
from typing import Pattern


@dataclass
class ParsedFilename:
    """
    Parsed filename data for structured photo filenames.

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

    Expected format: ``YYYY.MM.DD.HH.NN.SS.X.GGG.SSS.NNNN.SIDE.SUFFIX.ext``.

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

    PATTERN: Pattern[str] = re.compile(
        r"^(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)\.([a-zA-Z])\.([^.]+)\.([^.]+)\.(\d+)"  # noqa: E501
        r"\.([ARar])"       # Side (A/R)
        r"\.([^.]+)"        # Suffix
        r"\.([a-zA-Z]+)$",  # Extension
        re.IGNORECASE,
    )

    def parse(self, filename: str) -> ParsedFilename | None:
        """
        Parse a filename into components.

        Args:
            filename (str): Filename to parse.

        Returns:
            ParsedFilename: Parsed filename object if parsing successful, None otherwise.
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
                extension=extension.lower(),  # Normalize to lowercase
            )
        except (ValueError, IndexError):
            return None


class FilenameValidator:
    """Validator for parsed filename data.

    Validates structured photo filenames against date/time rules,
    modifier constraints, and sequence number limits.
    """

    VALID_MODIFIERS: set[str] = {"A", "B", "C", "E", "F"}
    VALID_SIDES: set[str] = {"A", "R"}
    DAYS_IN_MONTH: dict[int, int] = {
        1: 31,
        2: 28,
        3: 31,
        4: 30,
        5: 31,
        6: 30,
        7: 31,
        8: 31,
        9: 30,
        10: 31,
        11: 30,
        12: 31,
    }

    def __init__(self) -> None:
        """Initialize the validator."""

    def validate(self, parsed: ParsedFilename) -> list[str]:
        """
        Validate parsed filename data.

        Args:
            parsed (ParsedFilename): Parsed filename data.

        Returns:
            list[str]: List of validation error messages (empty if valid).
        """
        errors: list[str] = []

        # Validate modifier
        if parsed.modifier not in self.VALID_MODIFIERS:
            errors.append(
                "Invalid modifier: "
                f"'{parsed.modifier}' (must be one of: {', '.join(sorted(self.VALID_MODIFIERS))})"
            )

        # Validate side
        if parsed.side not in self.VALID_SIDES:
            errors.append(
                "Invalid side: "
                f"'{parsed.side}' (must be one of: {', '.join(sorted(self.VALID_SIDES))})"
            )

        # Validate date components
        errors.extend(self._validate_date(parsed))

        # Validate time components
        errors.extend(self._validate_time(parsed))

        # Validate zero sequence rule
        errors.extend(self._validate_zero_sequence(parsed))

        # Validate sequence length
        try:
            if int(parsed.sequence) > 9999:
                errors.append(
                    f"Invalid sequence value: {parsed.sequence} (must be <= 9999)"
                )
        except ValueError:
            # Should be caught by parser regex, but safe to ignore here if not a number
            pass
        return errors

    def _validate_date(self, parsed: ParsedFilename) -> list[str]:
        """Validate date components."""

        errors: list[str] = []

        # Month validation
        if parsed.month > 12:
            errors.append(f"Invalid month value: {parsed.month} (must be 00-12)")

        # Day validation
        if parsed.month > 0 and parsed.day > 0:
            # Check if day is valid for the given month
            max_days = self.DAYS_IN_MONTH.get(parsed.month, 0)

            # Handle leap years for February
            if parsed.month == 2 and calendar.isleap(parsed.year):
                max_days = 29

            if parsed.day > max_days:
                errors.append(
                    "Invalid day value: "
                    f"{parsed.day} for month {parsed.month} (must be 00-{max_days})"
                )
        elif parsed.day > 31:
            errors.append(f"Invalid day value: {parsed.day} (must be 00-31)")

        return errors

    def _validate_time(self, parsed: ParsedFilename) -> list[str]:
        """Validate time components."""

        errors: list[str] = []

        if parsed.hour > 23:
            errors.append(f"Invalid hour value: {parsed.hour} (must be 00-23)")

        if parsed.minute > 59:
            errors.append(f"Invalid minute value: {parsed.minute} (must be 00-59)")

        if parsed.second > 59:
            errors.append(f"Invalid second value: {parsed.second} (must be 00-59)")

        return errors

    def _validate_zero_sequence(self, parsed: ParsedFilename) -> list[str]:
        """Validate that if a component is 00, all more precise components are also 00."""

        errors: list[str] = []

        # If month is 00, day and time must be 00
        if parsed.month == 0:
            if parsed.day != 0:
                errors.append(
                    "Invalid date: month is 00 but day is "
                    f"{parsed.day:02d} (when month=00, day must also be 00)"
                )
            if parsed.hour != 0 or parsed.minute != 0 or parsed.second != 0:
                errors.append(
                    "Invalid date: month is 00 but time is "
                    f"{parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d} "
                    "(when month=00, time must be 00:00:00)"
                )

        # If day is 00, time must be 00:00:00
        if parsed.day == 0:
            if parsed.hour != 0 or parsed.minute != 0 or parsed.second != 0:
                errors.append(
                    "Invalid date: day is 00 but time is "
                    f"{parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d} "
                    "(when day=00, time must be 00:00:00)"
                )

        # If hour is 00, minute and second must be 00
        if parsed.hour == 0:
            if parsed.minute != 0 or parsed.second != 0:
                errors.append(
                    "Invalid time: hour is 00 but minutes/seconds are "
                    f"{parsed.minute:02d}:{parsed.second:02d} "
                    "(when hour=00, minutes and seconds must also be 00)"
                )

        # If minute is 00, second must be 00
        if parsed.minute == 0 and parsed.second != 0:
            errors.append(
                "Invalid time: minute is 00 but second is "
                f"{parsed.second:02d} (when minute=00, second must also be 00)"
            )

        return errors

