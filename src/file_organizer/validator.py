"""Validator for parsed filename data."""

import calendar
from file_organizer.parser import ParsedFilename


class FilenameValidator:
    """Validator for parsed filename data.
    
    Validates structured photo filenames against date/time rules,
    modifier constraints, and sequence number limits.
    """

    VALID_MODIFIERS: set[str] = {"A", "B", "C", "E", "F"}
    VALID_SIDES: set[str] = {"A", "R"}
    DAYS_IN_MONTH: dict[int, int] = {
        1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
        7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
    }

    def __init__(self) -> None:
        """Initialize the validator."""
        pass

    def validate(self, parsed: ParsedFilename) -> list[str]:
        """Validate parsed filename data.

        Args:
            parsed: Parsed filename data.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        # Validate modifier
        if parsed.modifier not in self.VALID_MODIFIERS:
            errors.append(
                f"Invalid modifier: '{parsed.modifier}' (must be one of: {', '.join(sorted(self.VALID_MODIFIERS))})"
            )

        # Validate side
        if parsed.side not in self.VALID_SIDES:
            errors.append(
                f"Invalid side: '{parsed.side}' (must be one of: {', '.join(sorted(self.VALID_SIDES))})"
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
                errors.append(f"Invalid sequence value: {parsed.sequence} (must be <= 9999)")
        except ValueError:
            # Should be caught by parser regex, but safe to ignore here if not a number
            pass

        return errors

    def _validate_date(self, parsed: ParsedFilename) -> list[str]:
        """Validate date components.

        Args:
            parsed: Parsed filename data.

        Returns:
            List of validation error messages.
        """
        errors = []

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
                    f"Invalid day value: {parsed.day} for month {parsed.month} "
                    f"(must be 00-{max_days})"
                )
        elif parsed.day > 31:
            errors.append(f"Invalid day value: {parsed.day} (must be 00-31)")

        return errors

    def _validate_time(self, parsed: ParsedFilename) -> list[str]:
        """Validate time components.

        Args:
            parsed: Parsed filename data.

        Returns:
            List of validation error messages.
        """
        errors = []

        if parsed.hour > 23:
            errors.append(f"Invalid hour value: {parsed.hour} (must be 00-23)")

        if parsed.minute > 59:
            errors.append(f"Invalid minute value: {parsed.minute} (must be 00-59)")

        if parsed.second > 59:
            errors.append(f"Invalid second value: {parsed.second} (must be 00-59)")

        return errors

    def _validate_zero_sequence(self, parsed: ParsedFilename) -> list[str]:
        """Validate that if a component is 00, all more precise components are also 00.

        Rule: If month=00, then day=00 and time=00:00:00
              If day=00, then time=00:00:00
              If hour=00, then minute=00 and second=00
              If minute=00, then second=00

        Args:
            parsed: Parsed filename data.

        Returns:
            List of validation error messages.
        """
        errors = []

        # If month is 00, day and time must be 00
        if parsed.month == 0:
            if parsed.day != 0:
                errors.append(
                    f"Invalid date: month is 00 but day is {parsed.day:02d} "
                    f"(when month=00, day must also be 00)"
                )
            if parsed.hour != 0 or parsed.minute != 0 or parsed.second != 0:
                errors.append(
                    f"Invalid date: month is 00 but time is {parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d} "
                    f"(when month=00, time must be 00:00:00)"
                )

        # If day is 00, time must be 00:00:00
        if parsed.day == 0:
            if parsed.hour != 0 or parsed.minute != 0 or parsed.second != 0:
                errors.append(
                    f"Invalid date: day is 00 but time is {parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d} "
                    f"(when day=00, time must be 00:00:00)"
                )

        # If hour is 00, minute and second must be 00
        if parsed.hour == 0:
            if parsed.minute != 0 or parsed.second != 0:
                errors.append(
                    f"Invalid time: hour is 00 but minutes/seconds are {parsed.minute:02d}:{parsed.second:02d} "
                    f"(when hour=00, minutes and seconds must also be 00)"
                )

        # If minute is 00, second must be 00
        if parsed.minute == 0 and parsed.second != 0:
            errors.append(
                f"Invalid time: minute is 00 but second is {parsed.second:02d} "
                f"(when minute=00, second must also be 00)"
            )

        return errors
