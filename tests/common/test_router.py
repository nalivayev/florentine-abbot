"""
Tests for common.router module (pattern-based routing).
"""

from pathlib import Path

from common.router import Router
from common.formatter import ParsedFilename


class TestRouter:
    """Tests for Router with pattern-based routing rules."""

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
            extension=extension,
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
        """Unknown suffix should fall through to catch-all DERIVATIVES/."""
        router = Router()
        parsed = self._create_parsed("UNKNOWN")
        base_path = Path("/archive")

        target = router.get_target_folder(parsed, base_path)

        assert target == Path("/archive/2020/2020.01.15/DERIVATIVES")

    def test_custom_routing(self):
        """Custom routing rules should be respected."""
        custom_routes = {"rules": [
            ["*.RAW.*", "SOURCES"],
            ["*.MSR.*", "SOURCES"],
            ["*.COR.*", "MASTERS"],
            ["*.EDT.*", "EXPORTS"],
            ["*.PRV.*", "."],
            ["*", "DERIVATIVES"],
        ]}
        router = Router(routes=custom_routes)

        cor_parsed = self._create_parsed("COR")
        edt_parsed = self._create_parsed("EDT")
        base_path = Path("/archive")

        cor_target = router.get_target_folder(cor_parsed, base_path)
        edt_target = router.get_target_folder(edt_parsed, base_path)

        assert cor_target == Path("/archive/2020/2020.01.15/MASTERS")
        assert edt_target == Path("/archive/2020/2020.01.15/EXPORTS")

    def test_custom_catch_all(self):
        """Router should use the catch-all rule for unmatched filenames."""
        custom_routes = {"rules": [
            ["*.RAW.*", "SOURCES"],
            ["*.MSR.*", "SOURCES"],
            ["*.PRV.*", "."],
            ["*", "CUSTOM_DEFAULT"],
        ]}
        router = Router(routes=custom_routes)
        parsed = self._create_parsed("UNKNOWN")
        base_path = Path("/archive")

        target = router.get_target_folder(parsed, base_path)

        assert target == Path("/archive/2020/2020.01.15/CUSTOM_DEFAULT")

    def test_case_insensitive_pattern_matching(self):
        """Pattern matching should be case-insensitive."""
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

    def test_filename_parameter_overrides_reconstruction(self):
        """When filename is provided, it is used for pattern matching."""
        custom_routes = {"rules": [
            ["scan_*.tif", "SCANS"],
            ["*", "OTHER"],
        ]}
        router = Router(routes=custom_routes)
        parsed = self._create_parsed("RAW")
        base_path = Path("/archive")

        # Pattern won't match the reconstructed name, but will match explicit filename
        target = router.get_target_folder(parsed, base_path, filename="scan_001.tif")

        assert target == Path("/archive/2020/2020.01.15/SCANS")

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
            extension="tif",
        )

        normalized = router.get_normalized_filename(parsed)

        assert normalized == "2020.01.05.09.08.07.E.FAM.POR.0001.A.RAW"

    def test_year_month_day_folder_structure(self):
        """Target folder should follow YYYY/YYYY.MM.DD structure."""
        router = Router()

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
            extension="tif",
        )
        base_path = Path("/archive")

        target_jan = router.get_target_folder(parsed_jan, base_path)
        target_dec = router.get_target_folder(parsed_dec, base_path)

        assert target_jan == Path("/archive/2020/2020.01.15/SOURCES")
        assert target_dec == Path("/archive/2020/2020.12.31/SOURCES")

    def test_get_folders_for_patterns_default(self):
        """get_folders_for_patterns should return correct folders for default routes."""
        router = Router()

        # MSR and RAW patterns → SOURCES
        folders = router.get_folders_for_patterns(["*.MSR.*", "*.RAW.*"])
        assert folders == {"SOURCES"}

        # Unknown pattern → catch-all (DERIVATIVES)
        folders = router.get_folders_for_patterns(["*.COR.*"])
        assert folders == {"DERIVATIVES"}

        # PRV pattern → "." (date root) → excluded from results
        folders = router.get_folders_for_patterns(["*.PRV.*"])
        assert folders == set()

    def test_get_folders_for_patterns_custom(self):
        """get_folders_for_patterns should respect custom routing rules."""
        custom_routes = {"rules": [
            ["*.RAW.*", "SOURCES"],
            ["*.MSR.*", "MASTERS"],
            ["*.COR.*", "MASTERS"],
            ["*.EDT.*", "DERIVATIVES"],
            ["*.PRV.*", "."],
            ["*", "OTHER"],
        ]}
        router = Router(routes=custom_routes)

        folders = router.get_folders_for_patterns(["*.RAW.*", "*.MSR.*"])
        assert folders == {"SOURCES", "MASTERS"}

        folders = router.get_folders_for_patterns(["*.COR.*", "*.EDT.*"])
        assert folders == {"MASTERS", "DERIVATIVES"}

        folders = router.get_folders_for_patterns(["*.PRV.*"])
        assert folders == set()

    def test_first_matching_rule_wins(self):
        """When multiple rules could match, the first one wins."""
        custom_routes = {"rules": [
            ["*.RAW.*", "RAW_FOLDER"],
            ["*.*.*", "CATCH_MORE"],
            ["*", "CATCH_ALL"],
        ]}
        router = Router(routes=custom_routes)
        parsed = self._create_parsed("RAW")
        base_path = Path("/archive")

        target = router.get_target_folder(parsed, base_path)

        assert target == Path("/archive/2020/2020.01.15/RAW_FOLDER")

    def test_fallback_when_no_pattern_matches(self):
        """When no rule matches, Router falls back to DERIVATIVES."""
        routes_without_catchall = {"rules": [
            ["*.RAW.*", "SOURCES"],
        ]}
        router = Router(routes=routes_without_catchall)
        parsed = self._create_parsed("UNKNOWN")
        base_path = Path("/archive")

        target = router.get_target_folder(parsed, base_path)

        assert target == Path("/archive/2020/2020.01.15/DERIVATIVES")

