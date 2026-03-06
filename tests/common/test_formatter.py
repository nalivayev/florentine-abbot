"""
Tests for common.formatter module: parsing, validation and formatting.
"""

import pytest

from common.formatter import Formatter, ParsedFilename


class TestParsing:
    """
    Test cases for Formatter.parse().
    """

    def setup_method(self) -> None:
        self.formatter: Formatter = Formatter()

    def test_parse_exact_date_with_time(self):
        """
        Test parsing filename with exact date and time.
        """
        result = self.formatter.parse('1950.06.15.12.30.45.E.FAM.POR.000001.A.MSR.tiff')

        assert result is not None
        assert result.year == 1950
        assert result.month == 6
        assert result.day == 15
        assert result.hour == 12
        assert result.minute == 30
        assert result.second == 45
        assert result.modifier == 'E'
        assert result.group == 'FAM'
        assert result.subgroup == 'POR'
        assert result.sequence == '000001'
        assert result.side == 'A'
        assert result.suffix == 'MSR'
        assert result.extension == 'tiff'

    def test_parse_circa_month(self):
        """
        Test parsing filename with circa month.
        """
        result = self.formatter.parse('1950.06.00.00.00.00.C.FAM.POR.000002.R.WEB.jpg')

        assert result is not None
        assert result.year == 1950
        assert result.month == 6
        assert result.day == 0
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.modifier == 'C'
        assert result.side == 'R'
        assert result.suffix == 'WEB'

    def test_parse_circa_year(self):
        """
        Test parsing filename with circa year only.
        """
        result = self.formatter.parse('1950.00.00.00.00.00.C.TRV.LND.000003.A.RAW.tiff')

        assert result is not None
        assert result.year == 1950
        assert result.month == 0
        assert result.day == 0
        assert result.modifier == 'C'
        assert result.side == 'A'
        assert result.suffix == 'RAW'

    def test_parse_absent_date(self):
        """
        Test parsing filename with absent date.
        """
        result = self.formatter.parse('0000.00.00.00.00.00.A.UNK.000.000001.A.MSR.jpg')

        assert result is not None
        assert result.year == 0
        assert result.month == 0
        assert result.day == 0
        assert result.modifier == 'A'
        assert result.side == 'A'
        assert result.suffix == 'MSR'

    def test_parse_with_suffix_raw(self):
        """
        Test parsing filename with .RAW suffix.
        """
        result = self.formatter.parse('1950.06.15.12.00.00.E.FAM.POR.000001.A.RAW.jpg')

        assert result is not None
        assert result.side == 'A'
        assert result.suffix == 'RAW'
        assert result.extension == 'jpg'

    def test_parse_with_suffix_msr(self):
        """
        Test parsing filename with .MSR suffix.
        """
        result = self.formatter.parse('1950.06.15.12.00.00.E.FAM.POR.000001.R.MSR.tiff')

        assert result is not None
        assert result.side == 'R'
        assert result.suffix == 'MSR'
        assert result.extension == 'tiff'

    def test_parse_invalid_format(self):
        """
        Test parsing invalid filename format.
        """
        result = self.formatter.parse('invalid.jpg')
        assert result is None

    def test_parse_missing_side(self):
        """
        Test parsing filename missing side component.
        """
        result = self.formatter.parse('1950.06.15.12.00.00.E.FAM.POR.000001.MSR.tiff')
        assert result is None

    def test_parse_missing_suffix(self):
        """
        Test parsing filename missing suffix component.
        """
        result = self.formatter.parse('1950.06.15.12.00.00.E.FAM.POR.000001.A.tiff')
        assert result is None

    def test_parse_incomplete_date(self):
        """
        Test parsing filename with incomplete date components.
        """
        result = self.formatter.parse('1950.06.15.tiff')
        assert result is None

    def test_parse_modifier_case_insensitive(self):
        """
        Test that modifier is converted to uppercase.
        """
        result = self.formatter.parse('1950.06.15.12.00.00.e.FAM.POR.000001.a.msr.tiff')
        assert result is not None
        assert result.modifier == 'E'
        assert result.side == 'A'
        assert result.suffix == 'msr'


class TestValidation:
    """
    Test cases for Formatter.validate().
    """

    def setup_method(self) -> None:
        self.formatter: Formatter = Formatter()

    def test_valid_exact_date_with_time(self):
        """
        Test validation of valid exact date with time.
        """
        parsed = self.formatter.parse('1950.06.15.12.30.45.E.FAM.POR.000001.A.MSR.tiff')
        assert parsed is not None
        errors = self.formatter.validate(parsed)
        assert len(errors) == 0

    def test_valid_circa_month(self):
        """
        Test validation of valid circa month.
        """
        parsed = self.formatter.parse('1950.06.00.00.00.00.C.FAM.POR.000002.R.WEB.jpg')
        assert parsed is not None
        errors = self.formatter.validate(parsed)
        assert len(errors) == 0

    def test_valid_circa_year(self):
        """
        Test validation of valid circa year.
        """
        parsed = self.formatter.parse('1950.00.00.00.00.00.C.TRV.LND.000003.A.RAW.tiff')
        assert parsed is not None
        errors = self.formatter.validate(parsed)
        assert len(errors) == 0

    def test_invalid_month_over_12(self):
        """
        Test validation rejects month > 12.
        """
        parsed = self.formatter.parse('1950.13.15.00.00.00.E.FAM.POR.000001.A.MSR.tiff')
        assert parsed is not None
        errors = self.formatter.validate(parsed)
        assert len(errors) > 0
        assert any('month' in error.lower() for error in errors)

    def test_invalid_february_30(self):
        """
        Test validation rejects February 30.
        """
        parsed = self.formatter.parse('1950.02.30.00.00.00.E.FAM.POR.000002.A.MSR.tiff')
        assert parsed is not None
        errors = self.formatter.validate(parsed)
        assert len(errors) > 0
        assert any('day' in error.lower() for error in errors)

    def test_invalid_day_over_31(self):
        """
        Test validation rejects day > 31.
        """
        parsed = self.formatter.parse('1950.06.32.00.00.00.E.FAM.POR.000003.A.MSR.tiff')
        assert parsed is not None
        errors = self.formatter.validate(parsed)
        assert len(errors) > 0
        assert any('day' in error.lower() for error in errors)

    def test_invalid_month_zero_day_nonzero(self):
        """
        Test validation rejects month=0 with day!=0.
        """
        parsed = self.formatter.parse('1950.00.15.00.00.00.C.FAM.POR.000004.A.MSR.tiff')
        assert parsed is not None
        errors = self.formatter.validate(parsed)
        assert len(errors) > 0
        assert any('month is 00 but day' in error.lower() for error in errors)

    def test_invalid_day_zero_time_nonzero(self):
        """
        Test validation rejects day=0 with time!=0.
        """
        parsed = self.formatter.parse('1950.06.00.12.00.00.C.FAM.POR.000005.A.MSR.tiff')
        assert parsed is not None
        errors = self.formatter.validate(parsed)
        assert len(errors) > 0
        assert any('day is 00 but time' in error.lower() for error in errors)

    def test_invalid_hour_over_23(self):
        """
        Test validation rejects hour > 23.
        """
        parsed = self.formatter.parse('1950.06.15.25.00.00.E.FAM.POR.000006.A.MSR.tiff')
        assert parsed is not None
        errors = self.formatter.validate(parsed)
        assert len(errors) > 0
        assert any('hour' in error.lower() for error in errors)

    def test_invalid_minute_over_59(self):
        """
        Test validation rejects minute > 59.
        """
        parsed = self.formatter.parse('1950.06.15.12.61.00.E.FAM.POR.000007.A.MSR.tiff')
        assert parsed is not None
        errors = self.formatter.validate(parsed)
        assert len(errors) > 0
        assert any('minute' in error.lower() for error in errors)

    def test_invalid_second_over_59(self):
        """
        Test validation rejects second > 59.
        """
        parsed = self.formatter.parse('1950.06.15.12.30.61.E.FAM.POR.000008.A.MSR.tiff')
        assert parsed is not None
        errors = self.formatter.validate(parsed)
        assert len(errors) > 0
        assert any('second' in error.lower() for error in errors)

    def test_invalid_modifier(self):
        """
        Test validation rejects invalid modifier.
        """
        parsed = ParsedFilename(
            year=1950, month=6, day=15,
            hour=12, minute=30, second=0,
            modifier='X',  # Invalid
            group='FAM', subgroup='POR', sequence='000001',
            side='A', suffix='MSR', extension='tiff'
        )
        errors = self.formatter.validate(parsed)
        assert len(errors) > 0
        assert any('modifier' in error.lower() for error in errors)

    def test_invalid_side(self):
        """
        Test validation rejects invalid side.
        """
        parsed = ParsedFilename(
            year=1950, month=6, day=15,
            hour=12, minute=30, second=0,
            modifier='E',
            group='FAM', subgroup='POR', sequence='000001',
            side='X',  # Invalid
            suffix='MSR', extension='tiff'
        )
        errors = self.formatter.validate(parsed)
        assert len(errors) > 0
        assert any('side' in error.lower() for error in errors)

    def test_invalid_sequence_too_large(self):
        """
        Test validation rejects sequence > 9999.
        """
        parsed = self.formatter.parse('1950.06.15.12.30.45.E.FAM.POR.010000.A.MSR.tiff')
        assert parsed is not None
        errors = self.formatter.validate(parsed)
        assert len(errors) > 0
        assert any('sequence' in error.lower() for error in errors)

    # Leap year validation tests

    def test_valid_leap_year_feb_29(self):
        """
        Test that February 29th is accepted in a leap year (e.g., 2024).
        """
        filename = '2024.02.29.12.00.00.E.TST.GRP.0001.A.RAW.jpg'
        parsed = self.formatter.parse(filename)
        assert parsed is not None

        errors = self.formatter.validate(parsed)
        assert len(errors) == 0, f"Should accept Feb 29 in leap year 2024. Errors: {errors}"

    def test_invalid_non_leap_year_feb_29(self):
        """
        Test that February 29th is rejected in a non-leap year (e.g., 2023).
        """
        filename = '2023.02.29.12.00.00.E.TST.GRP.0001.A.RAW.jpg'
        parsed = self.formatter.parse(filename)
        assert parsed is not None

        errors = self.formatter.validate(parsed)
        assert len(errors) > 0, "Should reject Feb 29 in non-leap year 2023"
        assert any("Invalid day value: 29" in e for e in errors), f"Unexpected error message: {errors}"

    def test_valid_feb_28_non_leap(self):
        """
        Test that February 28th is accepted in a non-leap year.
        """
        filename = '2023.02.28.12.00.00.E.TST.GRP.0001.A.RAW.jpg'
        parsed = self.formatter.parse(filename)
        assert parsed is not None
        errors = self.formatter.validate(parsed)
        assert len(errors) == 0


class TestFormatting:
    """
    Tests for Formatter.format_path() and Formatter.format_filename().
    """

    def _create_parsed(
        self,
        year: int = 2024,
        month: int = 1,
        day: int = 15,
        hour: int = 10,
        minute: int = 30,
        second: int = 45,
        modifier: str = "E",
        group: str = "FAM",
        subgroup: str = "POR",
        sequence: str = "0001",
        side: str = "A",
        suffix: str = "RAW",
        extension: str = "tif"
    ) -> ParsedFilename:
        """
        Create a ParsedFilename for testing.
        """
        return ParsedFilename(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            second=second,
            modifier=modifier,
            group=group,
            subgroup=subgroup,
            sequence=sequence,
            side=side,
            suffix=suffix,
            extension=extension
        )

    def test_default_path_template(self):
        """
        Default path template should format as YYYY/YYYY.MM.DD.
        """
        formatter = Formatter()
        parsed = self._create_parsed()

        path = formatter.format_path(parsed)

        assert path == "2024/2024.01.15"

    def test_default_filename_template(self):
        """
        Default filename template should format with all components.
        """
        formatter = Formatter()
        parsed = self._create_parsed()

        filename = formatter.format_filename(parsed)

        assert filename == "2024.01.15.10.30.45.E.FAM.POR.0001.A.RAW"

    def test_custom_path_template_flat(self):
        """
        Custom path template can create flat structure.
        """
        formatter = Formatter(archive_path_template="{year}.{month:02d}.{day:02d}")
        parsed = self._create_parsed()

        path = formatter.format_path(parsed)

        assert path == "2024.01.15"

    def test_custom_path_template_by_month(self):
        """
        Custom path template can group by year and month.
        """
        formatter = Formatter(archive_path_template="{year}/{year}.{month:02d}")
        parsed = self._create_parsed()

        path = formatter.format_path(parsed)

        assert path == "2024/2024.01"

    def test_custom_path_template_by_group(self):
        """
        Custom path template can include group component.
        """
        formatter = Formatter(archive_path_template="{group}/{year}/{year}.{month:02d}.{day:02d}")
        parsed = self._create_parsed()

        path = formatter.format_path(parsed)

        assert path == "FAM/2024/2024.01.15"

    def test_custom_filename_template_compact(self):
        """
        Custom filename template can be compact.
        """
        formatter = Formatter(
            archive_filename_template="{year}{month:02d}{day:02d}_{hour:02d}{minute:02d}{second:02d}_{group}_{suffix}"
        )
        parsed = self._create_parsed()

        filename = formatter.format_filename(parsed)

        assert filename == "20240115_103045_FAM_RAW"

    def test_custom_filename_template_iso_style(self):
        """
        Custom filename template can use ISO-style separators.
        """
        formatter = Formatter(
            archive_filename_template="{year}-{month:02d}-{day:02d}_{hour:02d}-{minute:02d}-{second:02d}_{modifier}_{group}_{subgroup}_{sequence:04d}_{side}_{suffix}"
        )
        parsed = self._create_parsed()

        filename = formatter.format_filename(parsed)

        assert filename == "2024-01-15_10-30-45_E_FAM_POR_0001_A_RAW"

    def test_sequence_formatting(self):
        """
        Sequence should be formatted as integer with leading zeros.
        """
        formatter = Formatter()
        parsed = self._create_parsed(sequence="42")

        filename = formatter.format_filename(parsed)

        assert "0042" in filename

    def test_different_dates(self):
        """
        Formatter should handle different date values correctly.
        """
        formatter = Formatter()

        # Test December 31
        parsed_dec = self._create_parsed(year=2023, month=12, day=31)
        path_dec = formatter.format_path(parsed_dec)
        assert path_dec == "2023/2023.12.31"

        # Test February 1
        parsed_feb = self._create_parsed(year=2024, month=2, day=1)
        path_feb = formatter.format_path(parsed_feb)
        assert path_feb == "2024/2024.02.01"

    def test_all_components_available(self):
        """
        All ParsedFilename components should be available in templates.
        """
        template = "{year}.{month}.{day}.{hour}.{minute}.{second}.{modifier}.{group}.{subgroup}.{sequence}.{side}.{suffix}.{extension}"
        formatter = Formatter(archive_filename_template=template)
        parsed = self._create_parsed()

        filename = formatter.format_filename(parsed)

        assert "2024" in filename
        assert "1" in filename  # month without padding
        assert "15" in filename
        assert "10" in filename
        assert "30" in filename
        assert "45" in filename
        assert "E" in filename
        assert "FAM" in filename
        assert "POR" in filename
        assert "1" in filename  # sequence without padding
        assert "A" in filename
        assert "RAW" in filename
        assert "tif" in filename

    def test_path_template_without_year_folder(self):
        """
        Path template can omit year folder for flat structure.
        """
        formatter = Formatter(archive_path_template="{year}.{month:02d}.{day:02d}")
        parsed = self._create_parsed()

        path = formatter.format_path(parsed)

        assert "/" not in path
        assert path == "2024.01.15"

    def test_filename_template_suffix_first(self):
        """
        Filename template can put suffix first.
        """
        formatter = Formatter(
            archive_filename_template="{suffix}_{year}.{month:02d}.{day:02d}_{group}_{sequence:04d}"
        )
        parsed = self._create_parsed()

        filename = formatter.format_filename(parsed)

        assert filename == "RAW_2024.01.15_FAM_0001"


class TestSourceTemplate:
    """
    Test cases for configurable source_filename_template parsing.
    """

    def test_default_template_parses_standard_filename(self):
        """
        Default source template should parse the standard 13-field filename.
        """
        formatter = Formatter()
        result = formatter.parse("2024.01.15.10.30.45.E.FAM.POR.0001.A.RAW.tiff")

        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 45
        assert result.modifier == "E"
        assert result.group == "FAM"
        assert result.subgroup == "POR"
        assert result.sequence == "0001"
        assert result.side == "A"
        assert result.suffix == "RAW"
        assert result.extension == "tiff"

    def test_template_without_time(self):
        """
        Source template without time fields should parse and default time to 0.
        """
        formatter = Formatter(
            source_filename_template="{year}.{month}.{day}.{modifier}.{group}.{subgroup}.{sequence}.{side}.{suffix}.{extension}"
        )
        result = formatter.parse("2024.01.15.E.FAM.POR.0001.A.RAW.tiff")

        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.modifier == "E"
        assert result.group == "FAM"

    def test_template_with_underscore_separators(self):
        """
        Source template with underscores should parse underscore-separated names.
        """
        formatter = Formatter(
            source_filename_template="{year}_{month}_{day}_{modifier}_{group}_{sequence}.{extension}"
        )
        result = formatter.parse("2024_01_15_E_FAM_0001.tiff")

        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.modifier == "E"
        assert result.group == "FAM"
        assert result.sequence == "0001"
        assert result.extension == "tiff"
        # Missing fields should get defaults
        assert result.subgroup == ""
        assert result.side == ""
        assert result.suffix == ""

    def test_template_with_mixed_separators(self):
        """
        Source template with mixed separators (dots, underscores, dashes).
        """
        formatter = Formatter(
            source_filename_template="{year}-{month}-{day}_{group}_{suffix}.{extension}"
        )
        result = formatter.parse("2024-01-15_FAM_RAW.tiff")

        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.group == "FAM"
        assert result.suffix == "RAW"
        assert result.extension == "tiff"

    def test_template_multi_char_modifier(self):
        """
        Non-single-letter modifiers should parse correctly (string field, not single char).
        """
        formatter = Formatter(
            source_filename_template="{year}.{month}.{day}.{modifier}.{group}.{sequence}.{extension}"
        )
        result = formatter.parse("2024.01.15.EX.FAM.0001.tiff")

        assert result is not None
        assert result.modifier == "EX"

    def test_template_rejects_non_matching_filename(self):
        """
        Filename that doesn't match the template should return None.
        """
        formatter = Formatter(
            source_filename_template="{year}_{month}_{day}.{extension}"
        )
        result = formatter.parse("2024.01.15.tiff")

        assert result is None

    def test_unknown_field_raises_error(self):
        """
        Unknown field in source template should raise ValueError.
        """
        with pytest.raises(ValueError, match="Unknown field 'camera'"):
            Formatter(source_filename_template="{year}.{camera}.{extension}")

    def test_template_minimal_fields(self):
        """
        Template with only year and extension should work.
        """
        formatter = Formatter(
            source_filename_template="{year}.{extension}"
        )
        result = formatter.parse("2024.tiff")

        assert result is not None
        assert result.year == 2024
        assert result.extension == "tiff"
        # All other fields default
        assert result.month == 0
        assert result.group == ""


class TestTemplateAwareValidation:
    """
    Test that validate() skips checks for fields absent from source template.
    """

    def test_no_modifier_in_template_skips_modifier_check(self):
        """
        When modifier is not in source template, empty default should not fail.
        """
        formatter = Formatter(
            source_filename_template="{year}.{month}.{day}.{group}.{extension}"
        )
        parsed = formatter.parse("2024.01.15.FAM.tiff")

        assert parsed is not None
        assert parsed.modifier == ""
        errors = formatter.validate(parsed)
        assert not any("modifier" in e.lower() for e in errors)

    def test_no_side_in_template_skips_side_check(self):
        """
        When side is not in source template, empty default should not fail.
        """
        formatter = Formatter(
            source_filename_template="{year}.{month}.{day}.{modifier}.{group}.{extension}"
        )
        parsed = formatter.parse("2024.01.15.E.FAM.tiff")

        assert parsed is not None
        assert parsed.side == ""
        errors = formatter.validate(parsed)
        assert not any("side" in e.lower() for e in errors)

    def test_no_sequence_in_template_skips_sequence_check(self):
        """
        When sequence is not in source template, default '0' should not fail.
        """
        formatter = Formatter(
            source_filename_template="{year}.{modifier}.{group}.{side}.{extension}"
        )
        parsed = formatter.parse("2024.E.FAM.A.tiff")

        assert parsed is not None
        errors = formatter.validate(parsed)
        assert not any("sequence" in e.lower() for e in errors)

    def test_no_date_fields_skips_date_validation(self):
        """
        When year/month/day are absent, date validation is skipped entirely.
        """
        formatter = Formatter(
            source_filename_template="{modifier}.{group}.{side}.{suffix}.{extension}"
        )
        parsed = formatter.parse("E.FAM.A.RAW.tiff")

        assert parsed is not None
        errors = formatter.validate(parsed)
        assert not any("month" in e.lower() or "day" in e.lower() for e in errors)

    def test_no_time_fields_skips_time_validation(self):
        """
        When hour/minute/second are absent, time validation is skipped entirely.
        """
        formatter = Formatter(
            source_filename_template="{year}.{month}.{day}.{modifier}.{group}.{side}.{suffix}.{extension}"
        )
        parsed = formatter.parse("2024.01.15.E.FAM.A.RAW.tiff")

        assert parsed is not None
        errors = formatter.validate(parsed)
        assert not any("hour" in e.lower() or "minute" in e.lower() or "second" in e.lower() for e in errors)

    def test_minimal_template_validates_clean(self):
        """
        Template with only year+extension should validate with zero errors.
        """
        formatter = Formatter(
            source_filename_template="{year}.{extension}"
        )
        parsed = formatter.parse("2024.tiff")

        assert parsed is not None
        errors = formatter.validate(parsed)
        assert errors == []

    def test_full_template_still_validates_normally(self):
        """
        Default full template should still catch invalid modifier.
        """
        formatter = Formatter()
        parsed = formatter.parse("2024.01.15.10.30.45.X.FAM.POR.0001.A.RAW.tiff")

        assert parsed is not None
        errors = formatter.validate(parsed)
        assert any("modifier" in e.lower() for e in errors)

    def test_partial_date_template_validates_month(self):
        """
        Template with month but no day should still validate month range.
        """
        formatter = Formatter(
            source_filename_template="{year}.{month}.{modifier}.{group}.{side}.{extension}"
        )
        parsed = formatter.parse("2024.13.E.FAM.A.tiff")

        assert parsed is not None
        errors = formatter.validate(parsed)
        assert any("month" in e.lower() for e in errors)
