"""
Constants and enumerations used throughout the scan_batcher package.

This module defines all constants and enums to avoid magic strings
and improve code maintainability.
"""

from enum import Enum


class RoundingStrategy(str, Enum):
    """
    DPI rounding strategy for scanner resolution calculations.
    
    Attributes:
        NEAREST: Round to the nearest available DPI value.
        MAXIMUM: Round up to the next higher DPI value.
        MINIMUM: Round down to the next lower DPI value.
    """
    NEAREST = "nr"
    MAXIMUM = "mx"
    MINIMUM = "mn"
    
    @classmethod
    def from_string(cls, value: str) -> "RoundingStrategy":
        """
        Convert a string to RoundingStrategy enum.
        
        Args:
            value: String representation ("nr", "mx", or "mn")
            
        Returns:
            RoundingStrategy: Corresponding enum value
            
        Raises:
            ValueError: If value is not a valid rounding strategy
        """
        try:
            return cls(value)
        except ValueError:
            valid_values = ", ".join([e.value for e in cls])
            raise ValueError(
                f"Invalid rounding strategy: {value}. "
                f"Valid values are: {valid_values}"
            )
    
    def __str__(self) -> str:
        """
        Return the string value of the enum.
        """
        return self.value


# Conversion constants
CM_TO_INCH = 2.54  # Conversion factor from centimeters to inches

# EXIF date/time formats
EXIF_DATE_FORMAT = "%Y:%m:%d"
EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"
EXIF_DATETIME_FORMAT_MS = "%Y:%m:%d %H:%M:%S.%f"  # With fractional seconds

# Default workflow engine
DEFAULT_ENGINE = "vuescan"
