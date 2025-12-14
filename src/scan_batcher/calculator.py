from typing import Sequence

from scan_batcher.constants import RoundingStrategy, CM_TO_INCH


class Calculator:
    """
    Calculator for determining optimal DPI (dots per inch) values for image printing.

    This class computes the required DPI to print an image of a given pixel size
    on a photo of a given physical size, taking into account available DPI options
    and rounding strategies.

    Example:
        >>> from scan_batcher.constants import RoundingStrategy
        >>> calc = Calculator()
        >>> calc(15.0, 3000, 150, 600, [150, 300, 600], RoundingStrategy.NEAREST)
        (508.0, 300, [(150, 1772), (300, 3543), (600, 7087)])
    """

    def __init__(self) -> None:
        """Initialize the calculator."""
        pass

    def __call__(
        self,
        photo_min_side: float,
        image_min_side: int,
        min_dpi: int | None,
        max_dpi: int | None,
        dpi_list: Sequence[int] | None,
        rounding: RoundingStrategy | str
    ) -> tuple[float, int, list[tuple[int, int]]]:
        """
        Calculate the optimal DPI values for printing an image on a photo with given dimensions.

        Args:
            photo_min_side (float): Minimum length of the photo's shorter side (in centimeters).
            image_min_side (int): Minimum length of the image's shorter side (in pixels).
            min_dpi (int | None): Minimum allowed DPI value (None if not specified).
            max_dpi (int | None): Maximum allowed DPI value (None if not specified).
            dpi_list (Sequence[int] | None): List of available DPI values to choose from (None if not specified).
            rounding (RoundingStrategy | str): Rounding strategy (RoundingStrategy enum or string):
                RoundingStrategy.NEAREST or 'nr' - nearest DPI value,
                RoundingStrategy.MAXIMUM or 'mx' - maximum possible DPI value,
                RoundingStrategy.MINIMUM or 'mn' - minimum possible DPI value.

        Returns:
            tuple[float, int, list[tuple[int, int]]]: A tuple containing:
                - calculated_dpi (float): The raw calculated DPI value.
                - recommended_dpi (int): The recommended DPI after applying constraints and rounding.
                - dpi_options (list[tuple[int, int]]): List of tuples with available DPI options and corresponding pixel dimensions.

        Raises:
            ValueError: If parameters are invalid or constraints conflict.
        """
        # Validate input parameters
        if photo_min_side <= 0 or image_min_side <= 0:
            raise ValueError("Photo and image dimensions must be positive")

        # Convert string to enum if needed
        if isinstance(rounding, str):
            try:
                rounding = RoundingStrategy.from_string(rounding)
            except ValueError as e:
                raise ValueError(str(e))

        # Validate min/max constraints
        if min_dpi is not None and max_dpi is not None and min_dpi > max_dpi:
            raise ValueError("min_dpi cannot be greater than max_dpi")

        dpi_list = sorted(dpi_list) if dpi_list else []

        # Calculate base DPI
        calculated_dpi = image_min_side / (photo_min_side / CM_TO_INCH)
        recommended_dpi = calculated_dpi

        dpi_options: list[tuple[int, int]] = []

        # Handle empty dpi_list case
        if dpi_list:

            # Find appropriate DPI from the list
            for index, value in enumerate(dpi_list):
                if value > 0:
                    if recommended_dpi < value:
                        if index == 0:
                            recommended_dpi = value
                        else:
                            match rounding:
                                case RoundingStrategy.NEAREST:
                                    recommended_dpi = value if (value - recommended_dpi) <= (recommended_dpi - dpi_list[index-1]) else dpi_list[index-1]
                                case RoundingStrategy.MAXIMUM:
                                    recommended_dpi = value
                                case RoundingStrategy.MINIMUM:
                                    recommended_dpi = dpi_list[index-1]
                        break
                else:
                    raise ValueError("All DPI values in dpi_list must be positive")
            else:  # if calculated_dpi is larger than all values in dpi_list
                recommended_dpi = dpi_list[-1]

            # Prepare DPI options
            dpi_options = [
                (dpi, int(dpi * photo_min_side / CM_TO_INCH))
                for dpi in dpi_list
            ]

        # Apply min/max constraints
        if min_dpi is not None:
            recommended_dpi = max(min_dpi, recommended_dpi)
        if max_dpi is not None:
            recommended_dpi = min(max_dpi, recommended_dpi)

        return (
            calculated_dpi,
            int(recommended_dpi),
            dpi_options
        )
