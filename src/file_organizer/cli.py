"""
Command Line Interface for File Organizer.

Provides two subcommands:

* ``file-organizer batch`` — one-shot processing of existing files.
* ``file-organizer watch`` — daemon mode that monitors a directory.

Global flags (``--verbose``, ``--config``, ``--log-path``, ``--version``)
are shared across both subcommands.
"""

import argparse
import logging
import sys
from pathlib import Path

from common.logger import Logger
from common.version import get_version
from file_organizer.organizer import FileOrganizer
from file_organizer.config import Config
from file_organizer.watcher import FileWatcher


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments shared between batch and watch subcommands."""
    parser.add_argument(
        "--input",
        required=True,
        type=str,
        dest="input_path",
        help="Path to the input folder to process or monitor",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=str,
        dest="output_path",
        help="Path to the archive (output) folder.",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy files instead of moving them (useful for testing)",
    )
    parser.add_argument(
        "--config",
        help="Path to JSON configuration file (see config.template.json)",
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Skip writing EXIF/XMP metadata to files",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="File Organizer - Metadata Extraction and Organization Tool",
        epilog="Use 'file-organizer <command> --help' for subcommand details.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"file-organizer (florentine-abbot {get_version()})",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--log-path",
        help="Custom directory for log files (default: ~/.florentine-abbot/logs/)",
    )

    subparsers = parser.add_subparsers(dest="command")

    # ── batch ──────────────────────────────────────────────────────────
    batch_parser = subparsers.add_parser(
        "batch",
        help="One-shot processing of existing files",
        description="Process all matching files under --input and exit.",
    )
    _add_common_arguments(batch_parser)
    batch_parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Process files recursively in subdirectories",
    )

    # ── watch ──────────────────────────────────────────────────────────
    watch_parser = subparsers.add_parser(
        "watch",
        help="Daemon mode — monitor a directory for new files",
        description="Watch --input for new files and process them continuously.",
    )
    _add_common_arguments(watch_parser)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``file-organizer`` CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    logger = Logger(
        "file_organizer",
        args.log_path,
        level=logging.DEBUG if args.verbose else logging.INFO,
        console=True,
    )

    input_path = Path(args.input_path)
    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        return 1

    output_path = Path(args.output_path)

    try:
        if args.command == "watch":
            config = Config(logger, args.config)
            watcher = FileWatcher(
                logger,
                path=str(input_path),
                config=config,
                output_path=output_path,
                copy_mode=args.copy,
                no_metadata=args.no_metadata,
            )
            watcher.start()
        else:
            # batch
            organizer = FileOrganizer(logger)
            organizer(
                input_path=input_path,
                output_path=output_path,
                config_path=args.config,
                recursive=args.recursive,
                copy_mode=args.copy,
                no_metadata=args.no_metadata,
            )
    except Exception as exc:  # pragma: no cover - generic CLI error reporting
        print(f"[file_organizer] Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    raise SystemExit(main())
