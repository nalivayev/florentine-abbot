import json
import logging
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Sequence

from scan_batcher.constants import EXIF_DATE_FORMAT, EXIF_DATETIME_FORMAT

logger = logging.getLogger(__name__)


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

    def __init__(self, executable: str = "exiftool"):
        self.executable = executable

    def _run(self, args: Sequence[str]) -> str:
        """Run exiftool with arguments."""
        if not shutil.which(self.executable):
             raise Exifer.Exception(f"Exiftool executable '{self.executable}' not found in PATH.")

        cmd = [self.executable] + list(args)
        try:
            # Use utf-8 encoding and ignore errors to be safe with weird metadata
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
                errors="replace"
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise Exifer.Exception(f"Exiftool failed: {e.stderr}")
        except Exception as e:
            raise Exifer.Exception(f"Error running exiftool: {e}")

    def read_json(self, file_path: Path, args: Sequence[str] | None = None) -> dict[str, Any]:
        """Read metadata as JSON."""
        cmd_args = ["-json"]
        if args:
            cmd_args.extend(args)
        cmd_args.append(str(file_path))
        
        output = self._run(cmd_args)
        try:
            data = json.loads(output)
            if not data:
                return {}
            return data[0]
        except json.JSONDecodeError as e:
            raise Exifer.Exception(f"Failed to parse exiftool output: {e}")

    def read_structured(self, file_path: Path) -> dict[str, Any]:
        """Read metadata grouped by IFD/Group (using -g1)."""
        return self.read_json(file_path, ["-g1"])

    def read_flat(self, file_path: Path) -> dict[str, Any]:
        """Read metadata with group prefixes (using -G)."""
        return self.read_json(file_path, ["-G"])

    def write(self, file_path: Path, tags: dict[str, Any], overwrite_original: bool = True) -> None:
        """Write metadata tags."""
        args = ["-overwrite_original"] if overwrite_original else []
        for tag, value in tags.items():
            if value is None:
                continue
            args.append(f"-{tag}={value}")
        
        args.append(str(file_path))
        self._run(args)

    @staticmethod
    def gps_values_to_date_time(date_value: str, time_values: Sequence[str | float]) -> datetime:
        """
        Convert EXIF GPS date and time values to a datetime object.

        Args:
            date_value (str): Date string in format 'YYYY:MM:DD'.
            time_values (Sequence[str | float]): List of [hour, minute, second] values.

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
    def extract(path: str | Path) -> dict[str, Any]:
        """
        Extract EXIF tags from an image file.

        Args:
            path (str | Path): Path to the image file.

        Returns:
            dict[str, Any]: Dictionary of EXIF tags grouped by IFD section.

        Raises:
            Exifer.Exception: If the file does not exist or is not a valid image.
        """
        path_obj = Path(path)
        if not path_obj.is_file():
            raise Exifer.Exception(f"File '{path_obj.name}' not found")

        try:
            tool = Exifer()
            exif_data = tool.read_structured(path_obj)
        except Exifer.Exception as e:
            raise Exifer.Exception(f"Error reading EXIF: {e}")
        except Exception as e:
            raise Exifer.Exception(f"Unexpected error: {e}")

        tags = {}
        
        # Copy all groups found by exiftool
        for group, values in exif_data.items():
            tags[group] = values

        # Add compatibility aliases for known groups if they differ from exiftool output
        if "ExifIFD" in tags:
            tags[Exifer.EXIFIFD] = tags["ExifIFD"]
            
        if "GPS" in tags:
            tags[Exifer.GPSIFD] = tags["GPS"]
            
        return tags
