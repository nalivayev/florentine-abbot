"""Tests for common.router module."""

import pytest
from pathlib import Path

from common.router import Router
from common.naming import ParsedFilename


class TestRouter:
    """Tests for Router class."""
    
    def _create_parsed(self, suffix: str, extension: str = "tif") -> ParsedFilename:
        """Create a ParsedFilename for testing."""
        return ParsedFilename(
            year=2020,
            month=1,
            day=15,
            hour=10,
            minute=0,
            second=0,
            modifier="E",
            group="FAM",
            subgroup="POR",
            sequence="0001",
            side="A",
            suffix=suffix,
            extension=extension
        )
    
    def test_default_routing_raw_to_sources(self):
        """RAW files should go to SOURCES/ with default routing."""
        router = Router()
        parsed = self._create_parsed("RAW")
        base_path = Path("/archive")
        
        target = router.get_target_folder(parsed, base_path)
        
        assert target == Path("/archive/2020/2020.01.15/SOURCES")
    
    def test_default_routing_msr_to_sources(self):
        """MSR files should go to SOURCES/ with default routing."""
        router = Router()
        parsed = self._create_parsed("MSR")
        base_path = Path("/archive")
        
        target = router.get_target_folder(parsed, base_path)
        
        assert target == Path("/archive/2020/2020.01.15/SOURCES")
    
    def test_default_routing_prv_to_date_root(self):
        """PRV files should go to date folder root with default routing."""
        router = Router()
        parsed = self._create_parsed("PRV", "jpg")
        base_path = Path("/archive")
        
        target = router.get_target_folder(parsed, base_path)
        
        assert target == Path("/archive/2020/2020.01.15")
    
    def test_default_routing_unknown_to_derivatives(self):
        """Unknown suffix should default to DERIVATIVES/."""
        router = Router()
        parsed = self._create_parsed("UNKNOWN")
        base_path = Path("/archive")
        
        target = router.get_target_folder(parsed, base_path)
        
        assert target == Path("/archive/2020/2020.01.15/DERIVATIVES")
    
    def test_custom_routing(self):
        """Custom routing rules should be respected."""
        custom_routing = {
            "RAW": "SOURCES",
            "MSR": "SOURCES",
            "PRV": ".",
            "COR": "MASTERS",
            "EDT": "EXPORTS"
        }
        router = Router(suffix_routing=custom_routing)
        
        cor_parsed = self._create_parsed("COR")
        edt_parsed = self._create_parsed("EDT")
        base_path = Path("/archive")
        
        cor_target = router.get_target_folder(cor_parsed, base_path)
        edt_target = router.get_target_folder(edt_parsed, base_path)
        
        assert cor_target == Path("/archive/2020/2020.01.15/MASTERS")
        assert edt_target == Path("/archive/2020/2020.01.15/EXPORTS")
    
    def test_case_insensitive_suffix_matching(self):
        """Suffix matching should be case-insensitive."""
        router = Router()
        
        raw_upper = self._create_parsed("RAW")
        raw_lower = self._create_parsed("raw")
        raw_mixed = self._create_parsed("Raw")
        base_path = Path("/archive")
        
        target_upper = router.get_target_folder(raw_upper, base_path)
        target_lower = router.get_target_folder(raw_lower, base_path)
        target_mixed = router.get_target_folder(raw_mixed, base_path)
        
        assert target_upper == Path("/archive/2020/2020.01.15/SOURCES")
        assert target_lower == Path("/archive/2020/2020.01.15/SOURCES")
        assert target_mixed == Path("/archive/2020/2020.01.15/SOURCES")
    
    def test_get_normalized_filename(self):
        """Normalized filename should have leading zeros."""
        router = Router()
        parsed = ParsedFilename(
            year=2020,
            month=1,
            day=5,
            hour=9,
            minute=8,
            second=7,
            modifier="E",
            group="FAM",
            subgroup="POR",
            sequence="1",
            side="A",
            suffix="RAW",
            extension="tif"
        )
        
        normalized = router.get_normalized_filename(parsed)
        
        assert normalized == "2020.01.05.09.08.07.E.FAM.POR.0001.A.RAW"
    
    def test_year_month_day_folder_structure(self):
        """Target folder should follow YYYY/YYYY.MM.DD structure."""
        router = Router()
        
        # Test different dates
        parsed_jan = self._create_parsed("RAW")
        parsed_dec = ParsedFilename(
            year=2020,
            month=12,
            day=31,
            hour=23,
            minute=59,
            second=59,
            modifier="E",
            group="FAM",
            subgroup="POR",
            sequence="0001",
            side="A",
            suffix="RAW",
            extension="tif"
        )
        base_path = Path("/archive")
        
        target_jan = router.get_target_folder(parsed_jan, base_path)
        target_dec = router.get_target_folder(parsed_dec, base_path)
        
        assert target_jan == Path("/archive/2020/2020.01.15/SOURCES")
        assert target_dec == Path("/archive/2020/2020.12.31/SOURCES")
    
    def test_get_folders_for_suffixes_default_routing(self):
        """get_folders_for_suffixes should return correct folders for default routing."""
        router = Router()
        
        # RAW and MSR should both be in SOURCES
        folders = router.get_folders_for_suffixes(["RAW", "MSR"])
        assert folders == {"SOURCES"}
        
        # Unknown suffixes should be in DERIVATIVES
        folders = router.get_folders_for_suffixes(["COR", "EDT"])
        assert folders == {"DERIVATIVES"}
        
        # PRV is in date root (.), should be excluded
        folders = router.get_folders_for_suffixes(["PRV"])
        assert folders == set()
    
    def test_get_folders_for_suffixes_custom_routing(self):
        """get_folders_for_suffixes should respect custom routing rules."""
        custom_routing = {
            "RAW": "SOURCES",
            "MSR": "MASTERS",
            "COR": "MASTERS",
            "EDT": "DERIVATIVES",
            "PRV": "."
        }
        router = Router(suffix_routing=custom_routing)
        
        # RAW and MSR are in different folders
        folders = router.get_folders_for_suffixes(["RAW", "MSR"])
        assert folders == {"SOURCES", "MASTERS"}
        
        # COR (corrected) and EDT (edited): both processed but in different folders
        folders = router.get_folders_for_suffixes(["COR", "EDT"])
        assert folders == {"MASTERS", "DERIVATIVES"}
        
        # PRV is in date root, should be excluded
        folders = router.get_folders_for_suffixes(["PRV"])
        assert folders == set()
