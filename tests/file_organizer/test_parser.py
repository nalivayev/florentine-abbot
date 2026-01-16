"""Unit tests for filename parser."""

import pytest
from common.naming import FilenameParser, ParsedFilename


class TestFilenameParser:
    """Test cases for FilenameParser."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return FilenameParser()

    def test_parse_exact_date_with_time(self, parser):
        """Test parsing filename with exact date and time."""
        result = parser.parse('1950.06.15.12.30.45.E.FAM.POR.000001.A.MSR.tiff')
        
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

    def test_parse_circa_month(self, parser):
        """Test parsing filename with circa month."""
        result = parser.parse('1950.06.00.00.00.00.C.FAM.POR.000002.R.WEB.jpg')
        
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

    def test_parse_circa_year(self, parser):
        """Test parsing filename with circa year only."""
        result = parser.parse('1950.00.00.00.00.00.C.TRV.LND.000003.A.RAW.tiff')
        
        assert result is not None
        assert result.year == 1950
        assert result.month == 0
        assert result.day == 0
        assert result.modifier == 'C'
        assert result.side == 'A'
        assert result.suffix == 'RAW'

    def test_parse_absent_date(self, parser):
        """Test parsing filename with absent date."""
        result = parser.parse('0000.00.00.00.00.00.A.UNK.000.000001.A.MSR.jpg')
        
        assert result is not None
        assert result.year == 0
        assert result.month == 0
        assert result.day == 0
        assert result.modifier == 'A'
        assert result.side == 'A'
        assert result.suffix == 'MSR'

    def test_parse_with_suffix_raw(self, parser):
        """Test parsing filename with .RAW suffix."""
        result = parser.parse('1950.06.15.12.00.00.E.FAM.POR.000001.A.RAW.jpg')
        
        assert result is not None
        assert result.side == 'A'
        assert result.suffix == 'RAW'
        assert result.extension == 'jpg'

    def test_parse_with_suffix_msr(self, parser):
        """Test parsing filename with .MSR suffix."""
        result = parser.parse('1950.06.15.12.00.00.E.FAM.POR.000001.R.MSR.tiff')
        
        assert result is not None
        assert result.side == 'R'
        assert result.suffix == 'MSR'
        assert result.extension == 'tiff'

    def test_parse_invalid_format(self, parser):
        """Test parsing invalid filename format."""
        result = parser.parse('invalid.jpg')
        assert result is None

    def test_parse_missing_side(self, parser):
        """Test parsing filename missing side component."""
        result = parser.parse('1950.06.15.12.00.00.E.FAM.POR.000001.MSR.tiff')
        assert result is None

    def test_parse_missing_suffix(self, parser):
        """Test parsing filename missing suffix component."""
        result = parser.parse('1950.06.15.12.00.00.E.FAM.POR.000001.A.tiff')
        assert result is None

    def test_parse_incomplete_date(self, parser):
        """Test parsing filename with incomplete date components."""
        result = parser.parse('1950.06.15.tiff')
        assert result is None

    def test_parse_modifier_case_insensitive(self, parser):
        """Test that modifier is converted to uppercase."""
        result = parser.parse('1950.06.15.12.00.00.e.FAM.POR.000001.a.msr.tiff')
        assert result.modifier == 'E'
        assert result.side == 'A'
        assert result.suffix == 'msr'
