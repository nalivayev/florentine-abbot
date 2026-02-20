from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Sequence

from common.logger import Logger
from scan_batcher.calculator import Calculator
from scan_batcher.constants import RoundingStrategy, CM_TO_INCH


class Batch(ABC):
    """
    Abstract base class for all data sources used in batch processing.
    """

    def __next__(self) -> dict | None:
        """
        Infinitely yield batch parameters.

        Returns:
            dict: Batch parameters.
        """
        return None

    @abstractmethod
    def __iter__(self) -> "Batch":
        """
        Return self as the iterator object.

        Returns:
            Batch: The iterator object itself.
        """
        return self


class Calculate(Batch):
    """
    Batch for a single calculation of optimal scan parameters.
    """

    def __init__(
        self,
        logger: Logger,
        min_dpi: int | None = None,
        max_dpi: int | None = None,
        dpis: Sequence[int] | None = None,
        rounding: RoundingStrategy | str = RoundingStrategy.NEAREST
    ) -> None:
        """
        Initialize the Calculate batch.

        Args:
            logger: Logger instance for this batch.
            min_dpi (int | None, optional): Minimum allowed DPI.
            max_dpi (int | None, optional): Maximum allowed DPI.
            dpis (Sequence[int] | None, optional): List of available DPI values.
            rounding (RoundingStrategy | str, optional): Rounding strategy (default: NEAREST).
        """
        self._logger = logger
        self._calculator = Calculator()
        self._min_dpi = min_dpi
        self._max_dpi = max_dpi
        self._dpis = list(dpis) if dpis is not None else []
        # Convert string to enum if needed
        self._rounding = RoundingStrategy.from_string(rounding) if isinstance(rounding, str) else rounding

    def _get_user_input(self) -> tuple[float, int]:
        """
        Prompt the user for required scan parameters and log the input.

        Returns:
            tuple[float, int]: The photo minimum side (cm) and image minimum side (px).
        """
        self._logger.info("Requesting user input for scan parameters")
        print("\nEnter scan parameters")
        photo_min_side = self._get_float_input("Minimum photo side length in centimeters: ")
        image_min_side = self._get_int_input("Minimum image side length in pixels: ")

        self._logger.debug(f"User input: photo_min_side={photo_min_side}, image_min_side={image_min_side}")
        return photo_min_side, image_min_side

    def _get_float_input(self, prompt: str) -> float:
        """
        Get a float input from the user with error handling.

        Args:
            prompt (str): Prompt to display.

        Returns:
            float: The user input as a float.
        """
        while True:
            try:
                value = float(input(prompt))
                self._logger.debug(f"Float input received: {value}")
                return value
            except ValueError:
                print("Error: Enter a number")
                self._logger.debug("Invalid float input")

    def _get_int_input(self, prompt: str, default: int | None = None) -> int:
        """
        Get an integer input from the user with error handling.

        Args:
            prompt (str): Prompt to display.
            default (int, optional): Default value if input is empty.

        Returns:
            int: The user input as an integer.
        """
        while True:
            try:
                value = input(prompt)
                if default is not None and value == "":
                    self._logger.debug(f"Default integer input used: {default}")
                    return default
                int_value = int(value)
                self._logger.debug(f"Integer input received: {int_value}")
                return int_value
            except ValueError:
                print("Error: Enter an integer")
                self._logger.debug("Invalid integer input")

    def _print_row(self, num: str, dpi: str, px: str, note: str = "") -> None:
        """
        Print a formatted table row with aligned columns.

        Args:
            num (str): Column 1 content (width 3, right-aligned).
            dpi (str): Column 2 content (width 10, left-aligned).
            px (str): Column 3 content (width 10, left-aligned).
            note (str, optional): Column 4 content (width 20, left-aligned).
        """
        print(f"{num:>3}\t{dpi:>10}\t{px:>10}\t{note:<20}")

    def _print_table(self, dpis: Sequence[tuple[int, int]], rec_dpi: float | None = None, calc_dpi: float | None = None) -> None:
        """
        Print a table of DPI calculation results.

        Args:
            dpis (Sequence[tuple[int, int]]): List of (DPI, pixels) tuples.
            rec_dpi (float | None, optional): Recommended DPI value.
            calc_dpi (float | None, optional): Calculated DPI value.
        """
        self._logger.info("Printing calculation results table")
        print("\nCalculation results:")
        self._print_row("", "DPI", "pixels", "Note")
        for index, item in enumerate(dpis, start=1):
            self._print_row(
                f"{index}",
                f"{item[0]:.1f}",
                f"{item[1]}",
                note=(
                    "recommended" if item[0] == rec_dpi else
                    "calculated" if item[0] == calc_dpi else ""
                )
            )

    def _next(self) -> dict[str, Any]:
        """
        Perform a single calculation or data retrieval.

        Returns:
            dict[str, Any]: Dictionary with calculation or file data.
        """
        self._logger.info("Starting calculation step")
        photo_min_side, image_min_side = self._get_user_input()

        # Calculate DPI using internal calculator
        calc_dpi, rec_dpi, dpis = self._calculator(
            float(photo_min_side),
            int(image_min_side),
            int(self._min_dpi) if self._min_dpi is not None else None,
            int(self._max_dpi) if self._max_dpi is not None else None,
            self._dpis,
            self._rounding
        )
        self._logger.debug(f"Calculator returned: calc_dpi={calc_dpi}, rec_dpi={rec_dpi}, dpis={dpis}")

        # Convert dpis to set for uniqueness
        dpis = set(dpis)

        # Add calculated values if not present
        if calc_dpi is not None:
            dpis.add((int(calc_dpi), int(photo_min_side * calc_dpi / CM_TO_INCH)))
        if rec_dpi is not None:
            dpis.add((int(rec_dpi), int(photo_min_side * rec_dpi / CM_TO_INCH)))

        # Sort for display, but work with set
        dpis = sorted(dpis, key=lambda x: x[0])

        self._print_table(dpis, rec_dpi, calc_dpi)

        while True:
            try:
                # Get user input for DPI selection
                if rec_dpi is not None:
                    index = self._get_int_input(
                        "\nSelect a DPI by entering the corresponding # from the table above (press Enter to use the recommended one): ",
                        0
                    )
                else:
                    index = self._get_int_input(
                        "\nSelect a DPI by entering the corresponding # from the table above: "
                    )
                if index == 0:  # Default case
                    dpi = rec_dpi
                    self._logger.info(f"User selected recommended DPI: {dpi}")
                    print("\nUsing recommended DPI:", dpi)
                    break
                elif 1 <= index <= len(dpis):
                    dpi = dpis[index - 1][0]  # Get DPI from the selected index
                    self._logger.info(f"User selected DPI: {dpi}")
                    print("\nSelected DPI:", dpi)
                    break
                else:
                    print("Error: Invalid selection. Please try again.")
                    self._logger.debug("Invalid DPI selection")
            except ValueError:
                print("Error: Invalid number entered.")
                self._logger.debug("Invalid number entered for DPI selection")
        self._logger.info(f"Calculation finished, returning scan_dpi={dpi}")
        return {"scan_dpi": dpi}

    def __iter__(self) -> "Calculate":
        """
        Return self as the iterator object.

        Returns:
            Calculate: The iterator object itself.
        """
        return self

    def __next__(self) -> dict[str, Any] | None:
        """
        Perform a single calculation and raise StopIteration.

        Raises:
            StopIteration: Always raised after one calculation.
        """
        self._next()
        raise StopIteration


class Scan(Calculate):
    """
    Data source from scanner (infinite) with built-in DPI calculation.
    """

    def __next__(self) -> dict[str, Any] | None:
        """
        Infinitely yield scan parameters with calculated DPI.

        Returns:
            dict[str, Any]: Scan parameters with calculated DPI.
        """
        return self._next()


class Process(Batch):
    """
    Data source from a folder (original version).

    Iterates over files in a directory matching a filter and yields file info.
    """

    def __init__(self, logger: Logger, path: str | Path, file_filter: str = "*.*") -> None:
        """
        Initialize the Process batch.

        Args:
            logger: Logger instance for this batch.
            path (str | Path): Path to the folder.
            file_filter (str, optional): File filter pattern (default: "*.*").
        """
        self._logger = logger
        self._path = Path(path)
        self._file_filter = file_filter
        self._validate_path()
        self._files = self._get_matching_files()
        self._index = 0  # Current index for iteration

    def _validate_path(self) -> None:
        """
        Validate that the specified path exists and is a directory.

        Raises:
            ValueError: If the folder does not exist.
        """
        if not self._path.is_dir():
            raise ValueError(f"Folder doesn't exist: {self._path}")

    def _get_matching_files(self) -> list[str]:
        """
        Get a list of files in the directory matching the filter.

        Returns:
            list[str]: List of matching file names.
        """
        return [
            f.name for f in self._path.iterdir()
            if self._matches_filter(f.name) and f.is_file()
        ]

    def _matches_filter(self, filename: str) -> bool:
        """
        Check if a filename matches the file filter.

        Args:
            filename (str): The filename to check.

        Returns:
            bool: True if the file matches the filter, False otherwise.
        """
        if self._file_filter == "*.*":
            return True
        ext = Path(filename).suffix.lower()
        filter_ext = self._file_filter.lower()
        if filter_ext.startswith("*"):
            return ext == filter_ext[1:] or ext == filter_ext[2:]
        return ext == filter_ext if filter_ext.startswith(".") else filename.lower().endswith(filter_ext.lower())

    def __iter__(self) -> "Process":
        """
        Return self as the iterator object and reset the index.

        Returns:
            Process: The iterator object itself.
        """
        self._index = 0  # Reset index for each new iterator
        return self

    def __next__(self) -> dict[str, str]:
        """
        Return the next file info or raise StopIteration when done.

        Returns:
            dict[str, str]: Dictionary with file path and filename.

        Raises:
            StopIteration: When all files have been processed.
        """
        if self._index < len(self._files):
            filename = self._files[self._index]
            self._index += 1
            return {
                "path": str(self._path / filename),
                "filename": filename
            }
        raise StopIteration
