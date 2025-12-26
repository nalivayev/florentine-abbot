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


class Arguments:
    """
    Defines and manages command-line arguments for the application.

    Contains argument definitions and validation methods for parameters
    including photo dimensions, image dimensions, resolution settings, and file processing options.
    """

    def __init__(self) -> None:
        """Initialize the Arguments class."""
        pass

    workflow = {
        "keys": ["-w", "--workflow"],
        "values": {
            "type": str, 
            "help": "Path to the workflow configuration file (INI format) for batch processing"
        }
    }

    templates = {
        "keys": ["-t", "--templates"],
        "values": {
            "type": str, 
            "nargs": "+", 
            "action": KeyValueAction, 
            "help": "List of template key-value pairs for file naming or metadata, e.g. -t year=2024 author=Smith"
        }
    }

    engine = {
        "keys": ["-e", "--engine"],
        "values": {
            "type": str, 
            "default": DEFAULT_ENGINE, 
            "help": f"Scan engine to use for processing (default: {DEFAULT_ENGINE})"
        }
    }
    
    batch = {
        "keys": ["-b", "--batch"],
        "values": {
            "default": ["scan"],
            "nargs": '+',
            "help": "Batch mode: scan (interactive), calculate (single calculation), or process (folder processing). Default: scan"
        }
    }

    min_dpi = {
        "keys": ["-mnd", "--min-dpi"],
        "values": {
            "type": int, 
            "help": "Minimum allowed DPI value for scanning (optional)"
        }
    }

    max_dpi = {
        "keys": ["-mxd", "--max-dpi"],
        "values": {
            "type": int, 
            "help": "Maximum allowed DPI value for scanning (optional)"
        }
    }

    dpis = {
        "keys": ["-d", "--dpis"],
        "values": {
            "type": int,
            "nargs": "+",
            "help": "List of supported DPI resolutions by the scanner, separated by space, e.g., 100 300 1200"
        }
    }

    rounding = {
        "keys": ["-r", "--rounding"],
        "values": {
            "choices": [e.value for e in RoundingStrategy],
            "default": RoundingStrategy.NEAREST.value,
            "help": (
                f"Rounding strategy for calculated DPI: "
                f"{RoundingStrategy.MAXIMUM.value} (maximum), "
                f"{RoundingStrategy.MINIMUM.value} (minimum), "
                f"{RoundingStrategy.NEAREST.value} (nearest). "
                f"Default: {RoundingStrategy.NEAREST.value}"
            )
        }
    }
    
    log_path = {
        "keys": ["--log-path"],
        "values": {
            "type": str,
            "default": None,
            "help": "Custom directory for log files (default: ~/.florentine-abbot/logs/)"
        }
    }


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
        # Add all arguments to the parser
        self.add_argument(*Arguments.batch["keys"], **Arguments.batch["values"])
        self.add_argument(*Arguments.workflow["keys"], **Arguments.workflow["values"])
        self.add_argument(*Arguments.templates["keys"], **Arguments.templates["values"])
        self.add_argument(*Arguments.engine["keys"], **Arguments.engine["values"])
        self.add_argument(*Arguments.min_dpi["keys"], **Arguments.min_dpi["values"])
        self.add_argument(*Arguments.max_dpi["keys"], **Arguments.max_dpi["values"])
        self.add_argument(*Arguments.dpis["keys"], **Arguments.dpis["values"])
        self.add_argument(*Arguments.rounding["keys"], **Arguments.rounding["values"])
        self.add_argument(*Arguments.log_path["keys"], **Arguments.log_path["values"])
