"""
Tests for common.formatter module.
"""

import pytest
from pathlib import Path

from common.formatter import Formatter
from common.naming import ParsedFilename


class TestFormatter:
    """
    Tests for Formatter class.
    """
    
    def _create_parsed(
        self,
        year=2024,
        month=1,
        day=15,
        hour=10,
        minute=30,
        second=45,
        modifier="E",
        group="FAM",
        subgroup="POR",
        sequence="0001",
        side="A",
        suffix="RAW",
        extension="tif"
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
        formatter = Formatter(path_template="{year}.{month:02d}.{day:02d}")
        parsed = self._create_parsed()
        
        path = formatter.format_path(parsed)
        
        assert path == "2024.01.15"
    
    def test_custom_path_template_by_month(self):
        """
        Custom path template can group by year and month.
        """
        formatter = Formatter(path_template="{year}/{year}.{month:02d}")
        parsed = self._create_parsed()
        
        path = formatter.format_path(parsed)
        
        assert path == "2024/2024.01"
    
    def test_custom_path_template_by_group(self):
        """
        Custom path template can include group component.
        """
        formatter = Formatter(path_template="{group}/{year}/{year}.{month:02d}.{day:02d}")
        parsed = self._create_parsed()
        
        path = formatter.format_path(parsed)
        
        assert path == "FAM/2024/2024.01.15"
    
    def test_custom_filename_template_compact(self):
        """
        Custom filename template can be compact.
        """
        formatter = Formatter(
            filename_template="{year}{month:02d}{day:02d}_{hour:02d}{minute:02d}{second:02d}_{group}_{suffix}"
        )
        parsed = self._create_parsed()
        
        filename = formatter.format_filename(parsed)
        
        assert filename == "20240115_103045_FAM_RAW"
    
    def test_custom_filename_template_iso_style(self):
        """
        Custom filename template can use ISO-style separators.
        """
        formatter = Formatter(
            filename_template="{year}-{month:02d}-{day:02d}_{hour:02d}-{minute:02d}-{second:02d}_{modifier}_{group}_{subgroup}_{sequence:04d}_{side}_{suffix}"
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
        formatter = Formatter(filename_template=template)
        parsed = self._create_parsed()
        
        filename = formatter.format_filename(parsed)
        
        # Should not raise any errors and should contain all values
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
        formatter = Formatter(path_template="{year}.{month:02d}.{day:02d}")
        parsed = self._create_parsed()
        
        path = formatter.format_path(parsed)
        
        assert "/" not in path
        assert path == "2024.01.15"
    
    def test_filename_template_suffix_first(self):
        """
        Filename template can put suffix first.
        """
        formatter = Formatter(
            filename_template="{suffix}_{year}.{month:02d}.{day:02d}_{group}_{sequence:04d}"
        )
        parsed = self._create_parsed()
        
        filename = formatter.format_filename(parsed)
        
        assert filename == "RAW_2024.01.15_FAM_0001"
