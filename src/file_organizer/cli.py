"""
Command Line Interface for File Organizer.

Provides three subcommands:

* ``file-organizer batch`` — one-shot processing of existing files.
* ``file-organizer watch`` — daemon mode that monitors a directory.
* ``file-organizer preview`` — dry-run: show what would happen without moving files.

Global flags (``--verbose``, ``--config``, ``--log-path``, ``--version``)
are shared across all subcommands.
"""

import argparse
import logging
import sys
from pathlib import Path

from common.logger import Logger
from common.utils import log_banner
from common.version import get_version
from file_organizer.organizer import FileOrganizer
from file_organizer.previewer import Previewer
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

    watch_parser = subparsers.add_parser(
        "watch",
        help="Daemon mode — monitor a directory for new files",
        description="Watch --input for new files and process them continuously.",
    )
    _add_common_arguments(watch_parser)

    preview_parser = subparsers.add_parser(
        "preview",
        help="Dry-run — show what would happen without moving files",
        description="Simulate batch processing and print a sample of source → destination mappings.",
    )
    _add_common_arguments(preview_parser)
    preview_parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Process files recursively in subdirectories",
    )
    preview_parser.add_argument(
        "-n", "--sample",
        type=int,
        default=50,
        metavar="N",
        help="Number of preview entries to show (default: 50)",
    )

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
    output_path = Path(args.output_path)

    version = get_version()
    fields: dict[str, str] = {
        "Mode": args.command,
        "Input": str(input_path),
        "Output": str(output_path),
        "Copy mode": "yes" if args.copy else "no",
    }
    if args.command in ("batch", "preview"):
        fields["Recursive"] = "yes" if args.recursive else "no"
    fields["No metadata"] = "yes" if args.no_metadata else "no"
    fields["Config"] = args.config or "default"
    log_banner(logger, "file-organizer", version, fields)

    if not input_path.exists():
        if args.command == "watch":
            input_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {input_path}")
        else:
            logger.error(f"Input path does not exist: {input_path}")
            return 1

    try:
        if args.command == "watch":
            watcher = FileWatcher(
                logger,
                path=str(input_path),
                config_path=args.config,
                output_path=output_path,
                copy_mode=args.copy,
                no_metadata=args.no_metadata,
            )
            watcher.start()
        elif args.command == "preview":
            organizer = FileOrganizer(logger)
            result = organizer(
                input_path=input_path,
                output_path=output_path,
                config_path=args.config,
                recursive=args.recursive,
                dry_run=True,
            )
            previewer = Previewer(result)
            summary = previewer.summary()
            print(f"\nTotal: {summary['total']}  OK: {summary['succeeded']}  Failed: {summary['failed']}\n")
            for entry in previewer.sample(args.sample):
                print(f"  {entry['source']}")
                print(f"    → {entry['destination']}")
            if previewer.errors():
                print("\nErrors:")
                for err in previewer.errors():
                    print(f"  {err['file']}: {err['reason']}")
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
