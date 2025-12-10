"""Unit tests for FilenameMetadataExtractor."""

import pytest
from pathlib import Path
from filename_metadata_extractor.plugin import FilenameMetadataExtractor
from filename_metadata_extractor.parser import FilenameParser


class TestFilenameMetadataExtractor:
    """Test cases for FilenameMetadataExtractor."""

    @pytest.fixture
    def plugin(self):
        """Create plugin instance."""
        return FilenameMetadataExtractor()

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return FilenameParser()

    def test_plugin_name(self, plugin):
        """Test plugin name."""
        assert plugin.name == 'naming_exif'

    def test_plugin_version(self, plugin):
        """Test plugin version."""
        assert plugin.version == '0.1.0'

    def test_can_handle_valid_tiff(self, plugin):
        """Test can_handle accepts valid TIFF file."""
        assert plugin.can_handle('1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff') is True

    def test_can_handle_valid_jpg(self, plugin):
        """Test can_handle accepts valid JPG file."""
        assert plugin.can_handle('1950.06.00.00.00.00.C.FAM.POR.000002.R.WEB.jpg') is True

    def test_can_handle_invalid_extension(self, plugin):
        """Test can_handle rejects invalid extension."""
        assert plugin.can_handle('1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.png') is False

    def test_can_handle_invalid_filename(self, plugin):
        """Test can_handle rejects invalid filename format."""
        assert plugin.can_handle('invalid.jpg') is False

    def test_can_handle_invalid_date(self, plugin):
        """Test can_handle rejects invalid date."""
        assert plugin.can_handle('1950.13.15.00.00.00.E.FAM.POR.000001.A.MSR.tiff') is False

    def test_can_handle_case_insensitive_extension(self, plugin):
        """Test can_handle works with uppercase extensions."""
        assert plugin.can_handle('1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.TIFF') is True
        assert plugin.can_handle('1950.06.15.12.00.00.E.FAM.POR.000001.A.WEB.JPG') is True

    def test_can_handle_skips_processed_folder(self, plugin):
        """Test can_handle skips files in 'processed' subfolder."""
        assert plugin.can_handle('C:/watch/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff') is True
        assert plugin.can_handle('C:/watch/processed/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff') is False
        assert plugin.can_handle('C:/watch/subfolder/processed/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff') is False
        assert plugin.can_handle('C:/watch/processed/subfolder/1950.06.15.12.00.00.E.FAM.POR.000001.A.WEB.jpg') is False

    def test_can_handle_processes_similar_folder_names(self, plugin):
        """Test can_handle processes files in folders with similar names to 'processed'."""
        # These should be processed - only exact 'processed' folder name is skipped
        assert plugin.can_handle('C:/watch/my_processed_files/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff') is True
        assert plugin.can_handle('C:/watch/not_processed/1950.06.15.12.00.00.E.FAM.POR.000001.A.WEB.jpg') is True
        assert plugin.can_handle('C:/watch/preprocessed/1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff') is True

    def test_parse_and_validate_valid_file(self, plugin):
        """Test _parse_and_validate with valid filename."""
        result = plugin._parse_and_validate('1950.06.15.12.00.00.E.FAM.POR.000001.A.MSR.tiff')
        assert result is not None
        assert result.year == 1950

    def test_parse_and_validate_invalid_file(self, plugin):
        """Test _parse_and_validate with invalid filename."""
        result = plugin._parse_and_validate('invalid.jpg')
        assert result is None

    def test_parse_and_validate_invalid_date(self, plugin):
        """Test _parse_and_validate with invalid date."""
        result = plugin._parse_and_validate('1950.13.15.00.00.00.E.FAM.POR.000001.A.MSR.tiff')
        assert result is None

    def test_build_metadata_dict_exact_date(self, plugin, parser):
        """Test _build_metadata_dict for exact date."""
        parsed = parser.parse('1950.06.15.12.30.00.E.FAM.POR.000001.A.MSR.tiff')
        exif_dict, iptc_dict, xmp_dict = plugin._build_metadata_dict(parsed)
        
        assert 'Xmp.dc.identifier' in xmp_dict
        assert 'Exif.Photo.DateTimeOriginal' in exif_dict
        assert 'Xmp.Iptc4xmpCore.DateCreated' in xmp_dict
        assert 'Xmp.photoshop.DateCreated' in xmp_dict
        assert exif_dict['Exif.Photo.DateTimeOriginal'] == '1950:06:15 12:30:00'
        assert xmp_dict['Xmp.Iptc4xmpCore.DateCreated'] == '1950-06-15'
        assert xmp_dict['Xmp.photoshop.DateCreated'] == '1950-06-15T12:30:00'  # Only for exact dates

    def test_build_metadata_dict_circa_date(self, plugin, parser):
        """Test _build_metadata_dict for circa date."""
        parsed = parser.parse('1950.06.00.00.00.00.C.FAM.POR.000002.R.WEB.jpg')
        exif_dict, iptc_dict, xmp_dict = plugin._build_metadata_dict(parsed)
        
        assert 'Xmp.dc.identifier' in xmp_dict
        assert 'Exif.Photo.DateTimeOriginal' not in exif_dict
        assert 'Xmp.Iptc4xmpCore.DateCreated' in xmp_dict
        assert 'Xmp.photoshop.DateCreated' not in xmp_dict
        assert xmp_dict['Xmp.Iptc4xmpCore.DateCreated'] == '1950-06'
