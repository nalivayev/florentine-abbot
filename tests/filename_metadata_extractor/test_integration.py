import os
import shutil
import tempfile
import pytest
from pathlib import Path
from PIL import Image
import pyexiv2
from filename_metadata_extractor.plugin import FilenameMetadataExtractor

class TestIntegration:
    @pytest.fixture
    def temp_dir(self):
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        # Cleanup
        shutil.rmtree(temp_dir)

    def create_dummy_image(self, path: Path):
        # Create a simple 100x100 RGB image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(path)

    def test_process_valid_tiff(self, temp_dir):
        # 1. Setup
        filename = "1950.06.15.12.30.45.E.FAM.POR.0001.A.MSR.tiff"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        plugin = FilenameMetadataExtractor()
        
        # 2. Execute
        # config is not used by this plugin currently, passing empty dict
        result = plugin.process(str(file_path), {})
        
        # 3. Verify
        assert result is True
        
        # Check file moved to processed/
        processed_dir = temp_dir / "processed"
        processed_file_path = processed_dir / filename
        
        assert processed_dir.exists()
        assert processed_file_path.exists()
        assert not file_path.exists() # Original should be gone
        
        # Check Metadata
        # We need to close the image handle if pyexiv2 keeps it open? 
        # pyexiv2 usually handles context managers or explicit close.
        # The plugin uses pyexiv2.Image(str(file_path)) and closes it.
        
        img = pyexiv2.Image(str(processed_file_path))
        metadata = img.read_xmp()
        exif_data = img.read_exif()
        img.close()
        
        # Check XMP Identifier
        assert 'Xmp.dc.identifier' in metadata
        assert 'Xmp.xmp.Identifier' in metadata
        
        # Check Date (Exact date E)
        assert 'Exif.Photo.DateTimeOriginal' in exif_data
        assert exif_data['Exif.Photo.DateTimeOriginal'] == '1950:06:15 12:30:45'
        
        assert 'Xmp.photoshop.DateCreated' in metadata
        assert metadata['Xmp.photoshop.DateCreated'] == '1950-06-15T12:30:45'

    def test_process_normalization(self, temp_dir):
        # Test that filename is normalized (sequence 1 -> 0001)
        # Input: 1 digit sequence
        filename = "1950.06.15.12.30.45.E.FAM.POR.1.A.MSR.tiff"
        expected_filename = "1950.06.15.12.30.45.E.FAM.POR.0001.A.MSR.tiff"
        
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        plugin = FilenameMetadataExtractor()
        
        # Execute
        result = plugin.process(str(file_path), {})
        
        assert result is True
        
        # Verify normalized filename in processed folder
        processed_file_path = temp_dir / "processed" / expected_filename
        assert processed_file_path.exists()

    def test_process_circa_date(self, temp_dir):
        # Test processing of Circa date (no time in EXIF)
        filename = "1950.00.00.00.00.00.C.FAM.POR.0002.A.WEB.jpg"
        file_path = temp_dir / filename
        self.create_dummy_image(file_path)
        
        plugin = FilenameMetadataExtractor()
        
        result = plugin.process(str(file_path), {})
        assert result is True
        
        processed_file_path = temp_dir / "processed" / filename
        assert processed_file_path.exists()
        
        img = pyexiv2.Image(str(processed_file_path))
        metadata = img.read_xmp()
        exif_data = img.read_exif()
        img.close()
        
        # Should NOT have DateTimeOriginal for Circa dates
        assert 'Exif.Photo.DateTimeOriginal' not in exif_data
        
        # Should have partial date in Iptc4xmpCore
        # Note: pyexiv2/Exiv2 might map Xmp.Iptc4xmpCore.DateCreated to Xmp.iptc.DateCreated
        date_created = metadata.get('Xmp.Iptc4xmpCore.DateCreated') or metadata.get('Xmp.iptc.DateCreated')
        assert date_created is not None
        assert date_created == '1950'
