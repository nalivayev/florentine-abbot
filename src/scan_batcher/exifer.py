import pyexiv2
from datetime import datetime, timedelta
from pathlib import Path

from scan_batcher.constants import EXIF_DATE_FORMAT, EXIF_DATETIME_FORMAT


class Exifer:
    """
    Utility class for extracting and converting EXIF metadata from images.

    Provides static methods for parsing GPS coordinates, altitude, date/time, and extracting EXIF tags.
    """

    IFD0 = "IFD0"
    IFD1 = "IFD1"
    EXIFIFD = "EXIFIFD"
    GPSIFD = "GPSIFD"

    class Exception(Exception):
        """Exception raised for EXIF-related errors."""
        pass

    @staticmethod
    def _exif_geo_values_to_value(values: list| None) -> float:
        """
        Convert a list of EXIF GPS coordinate values (degrees, minutes, seconds) to a float.

        Args:
            values (List): List of coordinate components (usually 3 elements).

        Returns:
            float: The coordinate as a float.

        Raises:
            Exifer.Exception: If input is empty or contains invalid values.
        """
        result = 0
        if values and len(values) > 0:
            try:
                result = float(values[0])
            except (ValueError, OverflowError):
                raise Exifer.Exception(f"Invalid input value: {values[0]}")
            if len(values) > 1:
                try:
                    result = result + float(values[1]) / 60
                except (ValueError, OverflowError):
                    raise Exifer.Exception(f"Invalid input value: {values[1]}")
            if len(values) > 2:
                try:
                    result = result + float(values[2]) / 3600
                except (ValueError, OverflowError):
                    raise Exifer.Exception(f"Invalid input value: {values[2]}")
            return result
        else:
            raise Exifer.Exception("Empty input value")

    @staticmethod
    def _exif_values_to_latitude(values: list | None = None, reference: str | None = None) -> float:
        """
        Convert EXIF GPS latitude values and reference to a signed float.

        Args:
            values (List): List of latitude components.
            reference (str): 'N' for north, 'S' for south.

        Returns:
            float: Latitude as a signed float.
        """
        result = Exifer._exif_geo_values_to_value(values)
        if result and reference == "S":
            result = -result
        return result

    @staticmethod
    def _exif_values_to_longitude(values: list | None = None, reference: str | None = None) -> float:
        """
        Convert EXIF GPS longitude values and reference to a signed float.

        Args:
            values (List): List of longitude components.
            reference (str): 'E' for east, 'W' for west.

        Returns:
            float: Longitude as a signed float.
        """
        result = Exifer._exif_geo_values_to_value(values)
        if result and reference == "W":
            result = -result
        return result

    @staticmethod
    def _exif_value_to_altitude(value: str | None = None) -> float:
        """
        Convert EXIF altitude value to float.

        Args:
            value (str): Altitude value as string.

        Returns:
            float: Altitude.

        Raises:
            Exifer.Exception: If the value cannot be converted or is None.
        """
        if not value:
            raise Exifer.Exception(f"Invalid input value: {value}")
        
        try:
            return float(value)
        except (ValueError, OverflowError):
            raise Exifer.Exception(f"Invalid input value: {value}")
        
    @staticmethod
    def gps_values_to_date_time(date_value: str, time_values: list) -> datetime:
        """
        Convert EXIF GPS date and time values to a datetime object.

        Args:
            date_value (str): Date string in format 'YYYY:MM:DD'.
            time_values (List): List of [hour, minute, second] values.

        Returns:
            datetime: Combined date and time.

        Raises:
            Exifer.Exception: If date or time values are invalid.
        """
        try:
            date = datetime.strptime(date_value, EXIF_DATE_FORMAT)
        except ValueError:
            raise Exifer.Exception(f"Invalid date input value: {date_value}")
        try:
            time = timedelta(
                hours=int(float(time_values[0])),
                minutes=int(float(time_values[1])),
                seconds=int(float(time_values[2]))
            )
        except (ValueError, OverflowError):
            raise Exifer.Exception(f"Invalid time input value: {time_values}")
        return date + time

    @staticmethod
    def convert_value_to_datetime(value: str) -> datetime:
        """
        Convert EXIF date/time string to a datetime object.

        Args:
            value (str): Date/time string in format 'YYYY:MM:DD HH:MM:SS'.

        Returns:
            datetime: Parsed datetime object.

        Raises:
            Exifer.Exception: If the value cannot be parsed.
        """
        try:
            return datetime.strptime(value, EXIF_DATETIME_FORMAT)
        except ValueError:
            raise Exifer.Exception(f"Invalid input value: {value}")

    @staticmethod
    def extract(path: str) -> dict:
        """
        Extract EXIF tags from an image file.

        Args:
            path (str): Path to the image file.

        Returns:
            dict: Dictionary of EXIF tags grouped by IFD section.

        Raises:
            Exifer.Exception: If the file does not exist or is not a valid image.
        """
        if not Path(path).is_file():
            raise Exifer.Exception(f"File '{Path(path).name}' not found")

        try:
            with pyexiv2.Image(path) as img:
                exif_data = img.read_exif()
        except Exception as e:
            raise Exifer.Exception(f"Invalid image file format or error reading EXIF: {e}")

        tags = {
            Exifer.IFD0: {},
            Exifer.EXIFIFD: {},
            Exifer.GPSIFD: {},
            Exifer.IFD1: {}
        }

        for key, value in exif_data.items():
            # key is like "Exif.Image.Make"
            parts = key.split('.')
            if len(parts) < 3:
                continue
            
            group = parts[1] # Image, Photo, GPSInfo
            tag_name = parts[-1]

            if group == "Image":
                tags[Exifer.IFD0][tag_name] = value
            elif group == "Photo":
                tags[Exifer.EXIFIFD][tag_name] = value
            elif group == "GPSInfo":
                tags[Exifer.GPSIFD][tag_name] = value
            
        return tags
