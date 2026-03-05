"""Filename parsing, validation and formatting utilities shared across tools.

Provides :class:`ParsedFilename` and :class:`Formatter` implementing the
canonical Florentine Abbot naming scheme, used by both File Organizer and
Preview Maker.
"""

import calendar
import re
from dataclasses import dataclass
from typing import Any, Optional, Pattern

from common.constants import DEFAULT_SOURCE_FILENAME_TEMPLATE, DEFAULT_ARCHIVE_PATH_TEMPLATE, DEFAULT_ARCHIVE_FILENAME_TEMPLATE
from common.logger import Logger


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


class Formatter:
    """Parses, validates and formats structured photo filenames.

    Combines three concerns around the canonical naming scheme:

    **Parsing** — extracts components from a filename using a configurable
    ``source_filename_template``.  Each ``{field}`` placeholder is converted
    to a regex capture group automatically:

    - Numeric fields (``year``, ``month``, …, ``sequence``) → ``(\\d+)``
    - ``extension`` → ``([a-zA-Z0-9]+)``
    - All other fields (``modifier``, ``group``, …) → ``([^<sep>]+)``
      where ``<sep>`` is the literal character following the field in the
      template.

    **Validation** — checks date/time consistency, modifier and side values,
    sequence limits.

    **Formatting** — builds folder paths and filenames from
    :class:`ParsedFilename` using configurable Python format-string templates
    loaded from ``formats.json`` or supplied at construction time.

    Templates use fields from :class:`ParsedFilename`:
    ``{year}``, ``{month}``, ``{day}``, ``{hour}``, ``{minute}``, ``{second}``,
    ``{modifier}``, ``{group}``, ``{subgroup}``, ``{sequence}``, ``{side}``,
    ``{suffix}``, ``{extension}``.
    Format specifiers are supported: ``{month:02d}``, ``{sequence:04d}``, etc.
    """

    _NUMERIC_FIELDS = frozenset({
        "year", "month", "day", "hour", "minute", "second", "sequence",
    })

    _ALL_FIELDS = frozenset({
        "year", "month", "day", "hour", "minute", "second",
        "modifier", "group", "subgroup", "sequence", "side", "suffix", "extension",
    })

    _FIELD_DEFAULTS: dict[str, int | str] = {
        "year": 0, "month": 0, "day": 0,
        "hour": 0, "minute": 0, "second": 0,
        "modifier": "", "group": "", "subgroup": "",
        "sequence": "0", "side": "", "suffix": "",
        "extension": "",
    }

    _VALID_MODIFIERS: set[str] = {"A", "B", "C", "E", "F"}
    _VALID_SIDES: set[str] = {"A", "R"}
    _DAYS_IN_MONTH: dict[int, int] = {
        1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
        7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31,
    }

    def __init__(
        self,
        source_filename_template: Optional[str] = None,
        archive_path_template: Optional[str] = None,
        archive_filename_template: Optional[str] = None,
        logger: Optional[Logger] = None,
        formats: Optional[dict[str, Any]] = None,
    ):
        """Initialize Formatter with templates.

        Args:
            source_filename_template: Template for incoming filenames
                (e.g., ``"{year}.{month}.{day}.{modifier}.{extension}"``).
                Each ``{field}`` is converted to a regex group for parsing.
                If *None*, taken from *formats* or uses the built-in default.
            archive_path_template: Template for folder path in archive
                (e.g., ``"{year}/{year}.{month:02d}.{day:02d}"``).
                If *None*, taken from *formats* or uses the built-in default.
            archive_filename_template: Template for filename (without
                extension) in archive.
                If *None*, taken from *formats* or uses the built-in default.
            logger: Optional logger instance.
            formats: ``formats`` section from :class:`ProjectConfig`.
                When *None* all templates fall back to built-in defaults.
        """
        self._logger = logger or Logger("formatter")

        fmt = formats or {}

        self._source_filename_template = (
            source_filename_template
            or fmt.get(
                "source_filename_template", DEFAULT_SOURCE_FILENAME_TEMPLATE
            )
        )
        self._archive_path_template = (
            archive_path_template
            or fmt.get(
                "archive_path_template", DEFAULT_ARCHIVE_PATH_TEMPLATE
            )
        )
        self._archive_filename_template = (
            archive_filename_template
            or fmt.get(
                "archive_filename_template", DEFAULT_ARCHIVE_FILENAME_TEMPLATE
            )
        )

        # Compile source template into a regex pattern.
        self._source_pattern, self._source_fields = self._compile_source_template(
            self._source_filename_template
        )

        self._logger.debug(
            f"Source pattern: {self._source_pattern.pattern}"
        )
        self._logger.debug(
            f"Archive path template: {self._archive_path_template}"
        )
        self._logger.debug(
            f"Archive filename template: {self._archive_filename_template}"
        )

    def parse(self, filename: str) -> ParsedFilename | None:
        """Parse a structured filename into components.

        Uses the compiled ``source_filename_template`` regex to extract
        field values.  Fields not present in the template receive defaults.

        Args:
            filename: Filename to parse.

        Returns:
            :class:`ParsedFilename` on success, *None* if the name does not
            match the expected pattern.
        """
        match = self._source_pattern.match(filename)
        if not match:
            return None

        try:
            # Start with defaults for fields not in template.
            values: dict[str, int | str] = dict(self._FIELD_DEFAULTS)

            # Overwrite with matched groups.
            for i, field in enumerate(self._source_fields, 1):
                values[field] = match.group(i)

            return ParsedFilename(
                year=int(values["year"]),
                month=int(values["month"]),
                day=int(values["day"]),
                hour=int(values["hour"]),
                minute=int(values["minute"]),
                second=int(values["second"]),
                modifier=str(values["modifier"]).upper(),
                group=str(values["group"]),
                subgroup=str(values["subgroup"]),
                sequence=str(values["sequence"]),
                side=str(values["side"]).upper(),
                suffix=str(values["suffix"]),
                extension=str(values["extension"]).lower(),
            )
        except (ValueError, IndexError, KeyError):
            return None

    def validate(self, parsed: ParsedFilename) -> list[str]:
        """Validate parsed filename data.

        Only fields present in the ``source_filename_template`` are checked.
        Fields that were not captured from the filename keep their defaults
        and are silently skipped.

        Args:
            parsed: Parsed filename data.

        Returns:
            List of validation error messages (empty if valid).
        """
        fields = frozenset(self._source_fields)
        errors: list[str] = []

        if "modifier" in fields and parsed.modifier not in self._VALID_MODIFIERS:
            errors.append(
                "Invalid modifier: "
                f"'{parsed.modifier}' (must be one of: "
                f"{', '.join(sorted(self._VALID_MODIFIERS))})"
            )

        if "side" in fields and parsed.side not in self._VALID_SIDES:
            errors.append(
                "Invalid side: "
                f"'{parsed.side}' (must be one of: "
                f"{', '.join(sorted(self._VALID_SIDES))})"
            )

        if fields & {"year", "month", "day"}:
            errors.extend(self._validate_date(parsed, fields))
        if fields & {"hour", "minute", "second"}:
            errors.extend(self._validate_time(parsed, fields))
        if fields & {"month", "day", "hour", "minute", "second"}:
            errors.extend(self._validate_zero_sequence(parsed, fields))

        if "sequence" in fields:
            try:
                if int(parsed.sequence) > 9999:
                    errors.append(
                        f"Invalid sequence value: {parsed.sequence} (must be <= 9999)"
                    )
            except ValueError:
                pass

        return errors

    def format_path(self, parsed: ParsedFilename) -> str:
        """Format the folder path from parsed filename components.

        Args:
            parsed: Parsed filename components.

        Returns:
            Formatted path string (e.g., ``"2024/2024.01.15"``).
        """
        try:
            return self._archive_path_template.format(**self._template_kwargs(parsed))
        except KeyError as e:
            self._logger.error(f"Missing field in archive_path_template: {e}")
            raise ValueError(f"Invalid archive_path_template: missing field {e}")
        except Exception as e:
            self._logger.error(f"Failed to format path: {e}")
            raise

    def format_filename(self, parsed: ParsedFilename) -> str:
        """Format the filename (without extension) from parsed components.

        Args:
            parsed: Parsed filename components.

        Returns:
            Formatted filename without extension
            (e.g., ``"2024.01.15.10.30.45.E.FAM.POR.0001.A.RAW"``).
        """
        try:
            return self._archive_filename_template.format(**self._template_kwargs(parsed))
        except KeyError as e:
            self._logger.error(f"Missing field in archive_filename_template: {e}")
            raise ValueError(f"Invalid archive_filename_template: missing field {e}")
        except Exception as e:
            self._logger.error(f"Failed to format filename: {e}")
            raise

    @staticmethod
    def _template_kwargs(parsed: ParsedFilename) -> dict:
        """Build keyword arguments dict for ``str.format()``."""
        return dict(
            year=parsed.year,
            month=parsed.month,
            day=parsed.day,
            hour=parsed.hour,
            minute=parsed.minute,
            second=parsed.second,
            modifier=parsed.modifier,
            group=parsed.group,
            subgroup=parsed.subgroup,
            sequence=int(parsed.sequence),
            side=parsed.side,
            suffix=parsed.suffix,
            extension=parsed.extension,
        )

    def _compile_source_template(self, template: str) -> tuple[Pattern[str], list[str]]:
        """Compile a source filename template into a regex pattern.

        Splits the template into alternating *literal* / ``{field}``
        segments.  Literals are escaped; fields become capture groups
        whose character class depends on the field type:

        * Numeric → ``(\\d+)``
        * ``extension`` → ``([a-zA-Z0-9]+)``
        * Other string fields → ``([^<sep>]+)`` where ``<sep>`` is the
          first character of the next literal segment (or ``(.+)`` when
          the field is the last token in the template).

        Args:
            template: Source filename template, e.g.
                ``"{year}.{month}.{day}.{extension}"``.

        Returns:
            Tuple of *(compiled regex, ordered field names)*.

        Raises:
            ValueError: If the template contains unknown field names.
        """
        # re.split on {word} keeps the captured group names in odd positions.
        parts = re.split(r"\{(\w+)\}", template)
        # parts = [literal0, field1, literal1, field2, ..., literalN]

        regex_parts: list[str] = ["^"]
        field_names: list[str] = []

        for i, part in enumerate(parts):
            if i % 2 == 0:
                # Literal segment — escape for regex.
                regex_parts.append(re.escape(part))
            else:
                # Field name.
                field_name = part
                if field_name not in self._ALL_FIELDS:
                    raise ValueError(
                        f"Unknown field '{field_name}' in source_filename_template. "
                        f"Allowed fields: {', '.join(sorted(self._ALL_FIELDS))}"
                    )
                field_names.append(field_name)

                if field_name in self._NUMERIC_FIELDS:
                    regex_parts.append(r"(\d+)")
                elif field_name == "extension":
                    regex_parts.append(r"([a-zA-Z0-9]+)")
                else:
                    # String field — derive negated character class from the
                    # first character of the *next* literal segment.
                    next_literal = parts[i + 1] if i + 1 < len(parts) else ""
                    if next_literal:
                        sep_char = next_literal[0]
                        regex_parts.append(
                            f"([^{re.escape(sep_char)}]+)"
                        )
                    else:
                        regex_parts.append(r"(.+)")

        regex_parts.append("$")
        pattern = re.compile("".join(regex_parts), re.IGNORECASE)
        return pattern, field_names

    def _validate_date(
        self, parsed: ParsedFilename, fields: frozenset[str],
    ) -> list[str]:
        errors: list[str] = []

        if "month" in fields and parsed.month > 12:
            errors.append(f"Invalid month value: {parsed.month} (must be 00-12)")

        if (
            "month" in fields
            and "day" in fields
            and parsed.month > 0
            and parsed.day > 0
        ):
            max_days = self._DAYS_IN_MONTH.get(parsed.month, 0)
            if parsed.month == 2 and calendar.isleap(parsed.year):
                max_days = 29
            if parsed.day > max_days:
                errors.append(
                    "Invalid day value: "
                    f"{parsed.day} for month {parsed.month} (must be 00-{max_days})"
                )
        elif "day" in fields and parsed.day > 31:
            errors.append(f"Invalid day value: {parsed.day} (must be 00-31)")

        return errors

    def _validate_time(
        self, parsed: ParsedFilename, fields: frozenset[str],
    ) -> list[str]:
        errors: list[str] = []
        if "hour" in fields and parsed.hour > 23:
            errors.append(f"Invalid hour value: {parsed.hour} (must be 00-23)")
        if "minute" in fields and parsed.minute > 59:
            errors.append(f"Invalid minute value: {parsed.minute} (must be 00-59)")
        if "second" in fields and parsed.second > 59:
            errors.append(f"Invalid second value: {parsed.second} (must be 00-59)")
        return errors

    def _validate_zero_sequence(
        self, parsed: ParsedFilename, fields: frozenset[str],
    ) -> list[str]:
        errors: list[str] = []

        if "month" in fields and parsed.month == 0:
            if "day" in fields and parsed.day != 0:
                errors.append(
                    "Invalid date: month is 00 but day is "
                    f"{parsed.day:02d} (when month=00, day must also be 00)"
                )
            if (
                fields & {"hour", "minute", "second"}
                and (parsed.hour != 0 or parsed.minute != 0 or parsed.second != 0)
            ):
                errors.append(
                    "Invalid date: month is 00 but time is "
                    f"{parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d} "
                    "(when month=00, time must be 00:00:00)"
                )

        if "day" in fields and parsed.day == 0:
            if (
                fields & {"hour", "minute", "second"}
                and (parsed.hour != 0 or parsed.minute != 0 or parsed.second != 0)
            ):
                errors.append(
                    "Invalid date: day is 00 but time is "
                    f"{parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d} "
                    "(when day=00, time must be 00:00:00)"
                )

        if "hour" in fields and parsed.hour == 0:
            if (
                fields & {"minute", "second"}
                and (parsed.minute != 0 or parsed.second != 0)
            ):
                errors.append(
                    "Invalid time: hour is 00 but minutes/seconds are "
                    f"{parsed.minute:02d}:{parsed.second:02d} "
                    "(when hour=00, minutes and seconds must also be 00)"
                )

        if "minute" in fields and parsed.minute == 0 and parsed.second != 0:
            errors.append(
                "Invalid time: minute is 00 but second is "
                f"{parsed.second:02d} (when minute=00, second must also be 00)"
            )

        return errors
