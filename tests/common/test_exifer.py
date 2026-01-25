import pytest
from unittest.mock import patch
from pathlib import Path
from common.exifer import Exifer

class TestExifer:

    @patch.object(Exifer, '_read_json')
    def test_read_success(self, mock_read_json):
        # Setup mock
        mock_read_json.return_value = {
            "SourceFile": "dummy.jpg",
            "ExifTool": "12.50",
            "IFD0:Make": "Canon",
            "ExifIFD:DateTimeOriginal": "2022:01:01 12:00:00",
            "XMP-exif:DateTimeDigitized": "2022:01:01 12:00:00"
        }
        
        tool = Exifer()
        tags_to_read = ["IFD0:Make", "ExifIFD:DateTimeOriginal", "XMP-exif:DateTimeDigitized"]
        result = tool.read(Path("dummy.jpg"), tags_to_read)
        
        assert result["IFD0:Make"] == "Canon"
        assert result["ExifIFD:DateTimeOriginal"] == "2022:01:01 12:00:00"
        assert result["XMP-exif:DateTimeDigitized"] == "2022:01:01 12:00:00"
        # SourceFile and ExifTool should be filtered out
        assert "SourceFile" not in result
        assert "ExifTool" not in result

    @patch.object(Exifer, '_read_json')
    def test_read_scanned_file(self, mock_read_json):
        """Test reading specific tags from a simulated scanned file (e.g. VueScan output)."""
        mock_read_json.return_value = {
            "SourceFile": "scanned.tif",
            "IFD0:Make": "Epson",
            "IFD0:Model": "Perfection V600",
            "ExifIFD:CreateDate": "2023:10:27 14:30:00"
        }
        
        tool = Exifer()
        tags_to_read = ["IFD0:Make", "IFD0:Model", "ExifIFD:CreateDate", "XMP-exif:DateTimeDigitized"]
        result = tool.read(Path("scanned.tif"), tags_to_read)
        
        assert result["IFD0:Make"] == "Epson"
        assert result["IFD0:Model"] == "Perfection V600"
        assert result["ExifIFD:CreateDate"] == "2023:10:27 14:30:00"
        # DateTimeDigitized might not exist in VueScan output
        assert "XMP-exif:DateTimeDigitized" not in result

    @patch.object(Exifer, '_run')
    def test_write(self, mock_run):
        """Test writing tags using exiftool."""
        tool = Exifer()
        tags = {
            "XMP-exif:DateTimeDigitized": "2023:10:27 14:30:00",
            "XMP-dc:Title": "Test Title"
        }
        
        tool.write(Path("dummy.tif"), tags)
        
        # Verify exiftool was called with correct arguments
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "-overwrite_original" in args
        assert "-XMP-exif:DateTimeDigitized=2023:10:27 14:30:00" in args
        assert "-XMP-dc:Title=Test Title" in args
        assert "dummy.tif" in args


    def test_utf8_encoding_persistence(self, tmp_path):
        """
        Integration test to verify that Cyrillic and special characters 
        are correctly preserved when writing/reading via exiftool.
        Also tests multiline values (arrays joined with newlines).
        This ensures regression protection for the stdin/charset encoding issue.
        """
        
        # 1. Create a dummy minimal valid TIFF file
        test_file = tmp_path / "test_encoding.tif"
        with open(test_file, 'wb') as f:
            # Minimal Little-endian TIFF: Header 4 bytes, Offset 4 bytes, empty IFD
            # II (0x4949) + 42 (0x2a00) + offset 8 (0x08000000)
            # IFD at offset 8: count 0 (0x0000), next IFD offset 0 (0x00000000)
            f.write(b'\x49\x49\x2a\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00')
            
        exifer = Exifer()
        
        # 2. Define test data with tricky characters and multiline values
        # 'ў' (U+045E - CYRILLIC SMALL LETTER SHORT U) specific to Belarusian
        # 'і' (U+0456 - CYRILLIC SMALL LETTER BYELORUSSIAN-UKRAINIAN I)
        # Generic Russian Cyrillic
        test_description = "Тэставае апісанне: літары ў і і. Русский текст."
        test_subject = "тэст; test; проба"
        
        # Multiline value with Cyrillic
        test_multiline_rights = "Скан © 2025 Имя\nВсе права защищены.\nКоммерческое использование запрещено."
        
        tags_to_write = {
            "XMP-dc:Description": test_description,
            "XMP-dc:Subject": test_subject,
            "XMP-dc:Rights": test_multiline_rights,
        }
        
        # 3. Write metadata (this exercises the persistent process via _run or _run_one_off)
        exifer.write(test_file, tags_to_write)
        
        # 4. Read back
        result = exifer.read(test_file, ["XMP-dc:Description", "XMP-dc:Subject", "XMP-dc:Rights"])
        
        # 5. Verify equality
        assert result.get("XMP-dc:Description") == test_description
        assert result.get("XMP-dc:Subject") == test_subject
        assert result.get("XMP-dc:Rights") == test_multiline_rights


