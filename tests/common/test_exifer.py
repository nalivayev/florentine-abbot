import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from common.exifer import Exifer

class TestExifer(unittest.TestCase):

    @patch.object(Exifer, 'read_structured')
    def test_extract_success(self, mock_read_structured):
        # Setup mock
        mock_read_structured.return_value = {
            "IFD0": {"Make": "Canon"},
            "ExifIFD": {"DateTimeOriginal": "2022:01:01 12:00:00"},
            "GPS": {"GPSLatitude": "40 deg 42' 46.00\" N"},
            "IFD1": {}
        }
        
        # Create a dummy file so Path.is_file() returns True
        with patch('pathlib.Path.is_file', return_value=True):
            tags = Exifer.extract("dummy.jpg")
            
        self.assertEqual(tags[Exifer.IFD0]["Make"], "Canon")
        self.assertEqual(tags[Exifer.EXIFIFD]["DateTimeOriginal"], "2022:01:01 12:00:00")
        self.assertEqual(tags[Exifer.GPSIFD]["GPSLatitude"], "40 deg 42' 46.00\" N")

    @patch.object(Exifer, 'read_structured')
    def test_extract_error(self, mock_read_structured):
        mock_read_structured.side_effect = Exifer.Exception("Exiftool failed")
        
        with patch('pathlib.Path.is_file', return_value=True):
            with self.assertRaises(Exifer.Exception):
                Exifer.extract("dummy.jpg")

    def test_file_not_found(self):
        with self.assertRaises(Exifer.Exception):
            Exifer.extract("non_existent.jpg")

    @patch.object(Exifer, 'read_structured')
    def test_extract_scanned_file(self, mock_read_structured):
        """Test extraction from a simulated scanned file (e.g. VueScan output)."""
        # Setup mock with typical scanner metadata
        mock_read_structured.return_value = {
            "IFD0": {
                "Make": "Epson",
                "Model": "Perfection V600",
                "Software": "VueScan 9.7.99"
            },
            "ExifIFD": {
                "DateTimeDigitized": "2023:10:27 14:30:00",
                "CreateDate": "2023:10:27 14:30:00"
            }
        }
        
        with patch('pathlib.Path.is_file', return_value=True):
            tags = Exifer.extract("scanned_image.jpg")
            
        # Verify we got the tags back
        self.assertEqual(tags[Exifer.IFD0]["Make"], "Epson")
        self.assertEqual(tags[Exifer.EXIFIFD]["DateTimeDigitized"], "2023:10:27 14:30:00")
        
        # Verify GPS is missing (as expected for a scanner)
        self.assertNotIn(Exifer.GPSIFD, tags)
