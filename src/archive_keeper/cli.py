"""
Command Line Interface for Archive Keeper.

Provides three subcommands:

* ``archive-keeper watch``  — daemon mode that polls the database for integrity checks.
* ``archive-keeper process`` — low-level single-file checksum calculation.
* ``archive-keeper scan``   — one-shot integrity scan of the archive.

Global flags (``--verbose``, ``--log-path``, ``--version``)
are shared across all subcommands.
"""

import argparse
import logging
import sys
from pathlib import Path

from common.logger import Logger
from common.utils import log_banner
from common.version import get_version
from archive_keeper.keeper import Keeper
from archive_keeper.processor import KeeperProcessor
from archive_keeper.watcher import KeeperWatcher


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Archive Keeper - Archive integrity monitoring",
        epilog="Use 'archive-keeper <command> --help' for subcommand details.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"archive-keeper (florentine-abbot {get_version()})",
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

    subparsers.add_parser(
        "watch",
        help="Daemon mode — poll database for integrity checks",
        description="Continuously poll the database and monitor archive integrity.",
    )

    process_parser = subparsers.add_parser(
        "process",
        help="Calculate the checksum of one file using the low-level processor",
        description="Run one low-level checksum pass without database orchestration.",
    )
    process_parser.add_argument(
        "--file",
        required=True,
        type=str,
        help="Path to the source file",
    )

    scan_parser = subparsers.add_parser(
        "scan",
        help="One-shot integrity scan of the archive",
        description="Run a single integrity scan pass on the archive.",
    )
    scan_parser.add_argument(
        "--path",
        required=True,
        type=str,
        help="Path to the archive root",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``archive-keeper`` CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    logger = Logger(
        "archive_keeper",
        args.log_path,
        level=logging.DEBUG if args.verbose else logging.INFO,
        console=True,
    )
    version = get_version()

    try:
        if args.command == "watch":
            fields: dict[str, str] = {"Mode": "watch"}
            log_banner(logger, "archive-keeper", version, fields)
            keeper = Keeper(logger)
            KeeperWatcher(logger, keeper=keeper).start()
        elif args.command == "process":
            file_path = Path(args.file)
            if not file_path.exists():
                logger.error("File does not exist: %s", file_path)
                return 1
            if not file_path.is_file():
                logger.error("Path is not a file: %s", file_path)
                return 1

            fields = {"Mode": "process", "File": str(file_path)}
            log_banner(logger, "archive-keeper", version, fields)
            checksum = KeeperProcessor(logger).process(file_path)
            logger.info("SHA-256: %s", checksum)
        else:
            path = Path(args.path)
            if not path.exists():
                logger.error("Path does not exist: %s", path)
                return 1
            fields = {"Mode": "scan", "Path": str(path)}
            log_banner(logger, "archive-keeper", version, fields)
            Keeper(logger).execute(path=path)

    except Exception as exc:  # pragma: no cover
        print(f"[archive_keeper] Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
