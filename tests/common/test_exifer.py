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

