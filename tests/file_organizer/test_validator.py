"""
Unit tests for filename validator.
"""

from common.naming import FilenameParser, ParsedFilename, FilenameValidator


class TestFilenameValidator:
    """
    Test cases for FilenameValidator.
    """

    def setup_method(self):
        """
        Setup for each test method.
        """
        self.validator = FilenameValidator()
        self.parser = FilenameParser()

    def test_valid_exact_date_with_time(self):
        """
        Test validation of valid exact date with time.
        """
        parsed = self.parser.parse('1950.06.15.12.30.45.E.FAM.POR.000001.A.MSR.tiff')
        errors = self.validator.validate(parsed)
        assert len(errors) == 0

    def test_valid_circa_month(self):
        """
        Test validation of valid circa month.
        """
        parsed = self.parser.parse('1950.06.00.00.00.00.C.FAM.POR.000002.R.WEB.jpg')
        errors = self.validator.validate(parsed)
        assert len(errors) == 0

    def test_valid_circa_year(self):
        """
        Test validation of valid circa year.
        """
        parsed = self.parser.parse('1950.00.00.00.00.00.C.TRV.LND.000003.A.RAW.tiff')
        errors = self.validator.validate(parsed)
        assert len(errors) == 0

    def test_invalid_month_over_12(self):
        """
        Test validation rejects month > 12.
        """
        parsed = self.parser.parse('1950.13.15.00.00.00.E.FAM.POR.000001.A.MSR.tiff')
        errors = self.validator.validate(parsed)
        assert len(errors) > 0
        assert any('month' in error.lower() for error in errors)

    def test_invalid_february_30(self):
        """
        Test validation rejects February 30.
        """
        parsed = self.parser.parse('1950.02.30.00.00.00.E.FAM.POR.000002.A.MSR.tiff')
        errors = self.validator.validate(parsed)
        assert len(errors) > 0
        assert any('day' in error.lower() for error in errors)

    def test_invalid_day_over_31(self):
        """
        Test validation rejects day > 31.
        """
        parsed = self.parser.parse('1950.06.32.00.00.00.E.FAM.POR.000003.A.MSR.tiff')
        errors = self.validator.validate(parsed)
        assert len(errors) > 0
        assert any('day' in error.lower() for error in errors)

    def test_invalid_month_zero_day_nonzero(self):
        """
        Test validation rejects month=0 with day≠0.
        """
        parsed = self.parser.parse('1950.00.15.00.00.00.C.FAM.POR.000004.A.MSR.tiff')
        errors = self.validator.validate(parsed)
        assert len(errors) > 0
        assert any('month is 00 but day' in error.lower() for error in errors)

    def test_invalid_day_zero_time_nonzero(self):
        """
        Test validation rejects day=0 with time≠0.
        """
        parsed = self.parser.parse('1950.06.00.12.00.00.C.FAM.POR.000005.A.MSR.tiff')
        errors = self.validator.validate(parsed)
        assert len(errors) > 0
        assert any('day is 00 but time' in error.lower() for error in errors)

    def test_invalid_hour_over_23(self):
        """
        Test validation rejects hour > 23.
        """
        parsed = self.parser.parse('1950.06.15.25.00.00.E.FAM.POR.000006.A.MSR.tiff')
        errors = self.validator.validate(parsed)
        assert len(errors) > 0
        assert any('hour' in error.lower() for error in errors)

    def test_invalid_minute_over_59(self):
        """
        Test validation rejects minute > 59.
        """
        parsed = self.parser.parse('1950.06.15.12.61.00.E.FAM.POR.000007.A.MSR.tiff')
        errors = self.validator.validate(parsed)
        assert len(errors) > 0
        assert any('minute' in error.lower() for error in errors)

    def test_invalid_second_over_59(self):
        """
        Test validation rejects second > 59.
        """
        parsed = self.parser.parse('1950.06.15.12.30.61.E.FAM.POR.000008.A.MSR.tiff')
        errors = self.validator.validate(parsed)
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
        errors = self.validator.validate(parsed)
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
        errors = self.validator.validate(parsed)
        assert len(errors) > 0
        assert any('side' in error.lower() for error in errors)

    def test_invalid_sequence_too_large(self):
        """
        Test validation rejects sequence > 9999.
        """
        parsed = self.parser.parse('1950.06.15.12.30.45.E.FAM.POR.010000.A.MSR.tiff')
        errors = self.validator.validate(parsed)
        assert len(errors) > 0
        assert any('sequence' in error.lower() for error in errors)

    # Leap year validation tests

    def test_valid_leap_year_feb_29(self):
        """
        Test that February 29th is accepted in a leap year (e.g., 2024).
        """
        # 2024 is a leap year
        filename = '2024.02.29.12.00.00.E.TST.GRP.0001.A.RAW.jpg'
        parsed = self.parser.parse(filename)
        assert parsed is not None
        
        errors = self.validator.validate(parsed)
        assert len(errors) == 0, f"Should accept Feb 29 in leap year 2024. Errors: {errors}"

    def test_invalid_non_leap_year_feb_29(self):
        """
        Test that February 29th is rejected in a non-leap year (e.g., 2023).
        """
        # 2023 is NOT a leap year
        filename = '2023.02.29.12.00.00.E.TST.GRP.0001.A.RAW.jpg'
        parsed = self.parser.parse(filename)
        assert parsed is not None
        
        errors = self.validator.validate(parsed)
        assert len(errors) > 0, "Should reject Feb 29 in non-leap year 2023"
        assert any("Invalid day value: 29" in e for e in errors), f"Unexpected error message: {errors}"

    def test_valid_feb_28_non_leap(self):
        """
        Test that February 28th is accepted in a non-leap year.
        """
        filename = '2023.02.28.12.00.00.E.TST.GRP.0001.A.RAW.jpg'
        parsed = self.parser.parse(filename)
        errors = self.validator.validate(parsed)
        assert len(errors) == 0
