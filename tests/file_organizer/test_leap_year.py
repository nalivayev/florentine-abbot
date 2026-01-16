"""Tests for leap year validation."""

import pytest
from common.naming import FilenameParser, FilenameValidator

class TestLeapYearValidation:
    """Test cases for leap year validation."""

    @pytest.fixture
    def validator(self):
        return FilenameValidator()

    @pytest.fixture
    def parser(self):
        return FilenameParser()

    def test_valid_leap_year_feb_29(self, validator, parser):
        """Test that February 29th is accepted in a leap year (e.g., 2024)."""
        # 2024 is a leap year
        filename = '2024.02.29.12.00.00.E.TST.GRP.0001.A.RAW.jpg'
        parsed = parser.parse(filename)
        assert parsed is not None
        
        errors = validator.validate(parsed)
        assert len(errors) == 0, f"Should accept Feb 29 in leap year 2024. Errors: {errors}"

    def test_invalid_non_leap_year_feb_29(self, validator, parser):
        """Test that February 29th is rejected in a non-leap year (e.g., 2023)."""
        # 2023 is NOT a leap year
        filename = '2023.02.29.12.00.00.E.TST.GRP.0001.A.RAW.jpg'
        parsed = parser.parse(filename)
        assert parsed is not None
        
        errors = validator.validate(parsed)
        assert len(errors) > 0, "Should reject Feb 29 in non-leap year 2023"
        assert any("Invalid day value: 29" in e for e in errors), f"Unexpected error message: {errors}"

    def test_valid_feb_28_non_leap(self, validator, parser):
        """Test that February 28th is accepted in a non-leap year."""
        filename = '2023.02.28.12.00.00.E.TST.GRP.0001.A.RAW.jpg'
        parsed = parser.parse(filename)
        errors = validator.validate(parsed)
        assert len(errors) == 0
