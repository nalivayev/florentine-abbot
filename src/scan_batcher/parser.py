from argparse import ArgumentParser, Action
from typing import Any, Sequence

from scan_batcher.constants import RoundingStrategy, DEFAULT_ENGINE


class KeyValueAction(Action):
    """
    Custom argparse action to parse key-value pairs from command-line arguments.

    Converts input strings in the format 'key=value' into dictionary entries
    and stores them in the namespace.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the KeyValueAction."""
        super().__init__(*args, **kwargs)

    def __call__(self, parser: ArgumentParser, namespace: Any, values: str | Sequence[Any] | None, option_string: str | None = None) -> None:
        """
        Parse key-value pairs and store as a dictionary in the namespace.

        Args:
            parser (ArgumentParser): The parser instance.
            namespace (Any): The namespace to update.
            values (str | Sequence[Any] | None): List of key=value strings.
            option_string (str | None): The option string seen on the command line.
        """
        dictionary = {}
        if values and isinstance(values, list):
            for pair in values:
                if isinstance(pair, str) and "=" in pair:
                    key, val = pair.split("=", 1)
                    dictionary[key] = val
        setattr(namespace, self.dest, dictionary)


class Parser(ArgumentParser):
    """
    Command-line argument parser for image calculation parameters.

    Handles arguments related to image dimensions, resolutions, 
    and rounding settings. Groups required arguments separately for better 
    user interface.
    """

    def __init__(self) -> None:
        """
        Initialize the Parser with all image calculation arguments.
        """
        ArgumentParser.__init__(self)
        # Group required arguments for better help output
        required_group = self.add_argument_group("required arguments")
        # Add all arguments to the parser (same semantics as before)
        self.add_argument(
            "-b",
            "--batch",
            default=["scan"],
            nargs="+",
            help=(
                "Batch mode: scan (interactive), calculate (single calculation), "
                "or process (folder processing). Default: scan"
            ),
        )
        self.add_argument(
            "-w",
            "--workflow",
            type=str,
            help=(
                "Path to the workflow configuration file (INI format) "
                "for batch processing"
            ),
        )
        self.add_argument(
            "-t",
            "--templates",
            type=str,
            nargs="+",
            action=KeyValueAction,
            help=(
                "List of template key-value pairs for file naming or metadata, "
                "e.g. -t year=2024 author=Smith"
            ),
        )
        self.add_argument(
            "-e",
            "--engine",
            type=str,
            default=DEFAULT_ENGINE,
            help=f"Scan engine to use for processing (default: {DEFAULT_ENGINE})",
        )
        self.add_argument(
            "-mnd",
            "--min-dpi",
            type=int,
            help="Minimum allowed DPI value for scanning (optional)",
        )
        self.add_argument(
            "-mxd",
            "--max-dpi",
            type=int,
            help="Maximum allowed DPI value for scanning (optional)",
        )
        self.add_argument(
            "-d",
            "--dpis",
            type=int,
            nargs="+",
            help=(
                "List of supported DPI resolutions by the scanner, "
                "separated by space, e.g., 100 300 1200"
            ),
        )
        self.add_argument(
            "-r",
            "--rounding",
            choices=[e.value for e in RoundingStrategy],
            default=RoundingStrategy.NEAREST.value,
            help=(
                "Rounding strategy for calculated DPI: "
                f"{RoundingStrategy.MAXIMUM.value} (maximum), "
                f"{RoundingStrategy.MINIMUM.value} (minimum), "
                f"{RoundingStrategy.NEAREST.value} (nearest). "
                f"Default: {RoundingStrategy.NEAREST.value}"
            ),
        )
        self.add_argument(
            "--log-path",
            type=str,
            default=None,
            help=(
                "Custom directory for log files "
                "(default: ~/.florentine-abbot/logs/)"
            ),
        )
