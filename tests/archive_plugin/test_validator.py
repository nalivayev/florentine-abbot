"""Unit tests for filename validator."""

import pytest
from archive_plugin.parser import FilenameParser, ParsedFilename
from archive_plugin.validator import FilenameValidator


class TestFilenameValidator:
    """Test cases for FilenameValidator."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return FilenameValidator()

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return FilenameParser()

    def test_valid_exact_date_with_time(self, validator, parser):
        """Test validation of valid exact date with time."""
        parsed = parser.parse('1950.06.15.12.30.45.E.FAM.POR.000001.A.MSR.tiff')
        errors = validator.validate(parsed)
        assert len(errors) == 0

    def test_valid_circa_month(self, validator, parser):
        """Test validation of valid circa month."""
        parsed = parser.parse('1950.06.00.00.00.00.C.FAM.POR.000002.R.WEB.jpg')
        errors = validator.validate(parsed)
        assert len(errors) == 0

    def test_valid_circa_year(self, validator, parser):
        """Test validation of valid circa year."""
        parsed = parser.parse('1950.00.00.00.00.00.C.TRV.LND.000003.A.RAW.tiff')
        errors = validator.validate(parsed)
        assert len(errors) == 0

    def test_invalid_month_over_12(self, validator, parser):
        """Test validation rejects month > 12."""
        parsed = parser.parse('1950.13.15.00.00.00.E.FAM.POR.000001.A.MSR.tiff')
        errors = validator.validate(parsed)
        assert len(errors) > 0
        assert any('month' in error.lower() for error in errors)

    def test_invalid_february_30(self, validator, parser):
        """Test validation rejects February 30."""
        parsed = parser.parse('1950.02.30.00.00.00.E.FAM.POR.000002.A.MSR.tiff')
        errors = validator.validate(parsed)
        assert len(errors) > 0
        assert any('day' in error.lower() for error in errors)

    def test_invalid_day_over_31(self, validator, parser):
        """Test validation rejects day > 31."""
        parsed = parser.parse('1950.06.32.00.00.00.E.FAM.POR.000003.A.MSR.tiff')
        errors = validator.validate(parsed)
        assert len(errors) > 0
        assert any('day' in error.lower() for error in errors)

    def test_invalid_month_zero_day_nonzero(self, validator, parser):
        """Test validation rejects month=0 with day≠0."""
        parsed = parser.parse('1950.00.15.00.00.00.C.FAM.POR.000004.A.MSR.tiff')
        errors = validator.validate(parsed)
        assert len(errors) > 0
        assert any('month is 00 but day' in error.lower() for error in errors)

    def test_invalid_day_zero_time_nonzero(self, validator, parser):
        """Test validation rejects day=0 with time≠0."""
        parsed = parser.parse('1950.06.00.12.00.00.C.FAM.POR.000005.A.MSR.tiff')
        errors = validator.validate(parsed)
        assert len(errors) > 0
        assert any('day is 00 but time' in error.lower() for error in errors)

    def test_invalid_hour_over_23(self, validator, parser):
        """Test validation rejects hour > 23."""
        parsed = parser.parse('1950.06.15.25.00.00.E.FAM.POR.000006.A.MSR.tiff')
        errors = validator.validate(parsed)
        assert len(errors) > 0
        assert any('hour' in error.lower() for error in errors)

    def test_invalid_minute_over_59(self, validator, parser):
        """Test validation rejects minute > 59."""
        parsed = parser.parse('1950.06.15.12.61.00.E.FAM.POR.000007.A.MSR.tiff')
        errors = validator.validate(parsed)
        assert len(errors) > 0
        assert any('minute' in error.lower() for error in errors)

    def test_invalid_second_over_59(self, validator, parser):
        """Test validation rejects second > 59."""
        parsed = parser.parse('1950.06.15.12.30.61.E.FAM.POR.000008.A.MSR.tiff')
        errors = validator.validate(parsed)
        assert len(errors) > 0
        assert any('second' in error.lower() for error in errors)

    def test_invalid_modifier(self, validator):
        """Test validation rejects invalid modifier."""
        parsed = ParsedFilename(
            year=1950, month=6, day=15,
            hour=12, minute=30, second=0,
            modifier='X',  # Invalid
            group='FAM', subgroup='POR', sequence='000001',
            side='A', suffix='MSR', extension='tiff'
        )
        errors = validator.validate(parsed)
        assert len(errors) > 0
        assert any('modifier' in error.lower() for error in errors)

    def test_invalid_side(self, validator):
        """Test validation rejects invalid side."""
        parsed = ParsedFilename(
            year=1950, month=6, day=15,
            hour=12, minute=30, second=0,
            modifier='E',
            group='FAM', subgroup='POR', sequence='000001',
            side='X',  # Invalid
            suffix='MSR', extension='tiff'
        )
        errors = validator.validate(parsed)
        assert len(errors) > 0
        assert any('side' in error.lower() for error in errors)

    def test_invalid_sequence_too_large(self, validator, parser):
        """Test validation rejects sequence > 9999."""
        parsed = parser.parse('1950.06.15.12.30.45.E.FAM.POR.010000.A.MSR.tiff')
        errors = validator.validate(parsed)
        assert len(errors) > 0
        assert any('sequence' in error.lower() for error in errors)
