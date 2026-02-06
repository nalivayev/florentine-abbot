"""Command Line Interface for Archive Organizer."""

import argparse
import logging
import sys
from pathlib import Path

from common.logger import Logger
from common.version import get_version
from file_organizer.organizer import FileOrganizer
from file_organizer.config import Config
from file_organizer.monitor import FileMonitor


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="File Organizer - Metadata Extraction and Organization Tool",
        epilog="Metadata is configured in metadata.json in the config directory.",
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'file-organizer (florentine-abbot {get_version()})'
    )
    parser.add_argument("input_path", help="Path to the folder to process or monitor")
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode (monitor for new files)")
    parser.add_argument("-r", "--recursive", action="store_true", help="Process files recursively in subdirectories")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--config", help="Path to JSON configuration file (see config.template.json)")
    parser.add_argument("--log-path", help="Custom directory for log files (default: ~/.florentine-abbot/logs/)")
    parser.add_argument("--copy", action="store_true", help="Copy files instead of moving them (useful for testing)")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the `file-organizer` CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)

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

    try:
        if args.daemon:
            # Daemon mode: run filesystem monitor around per-file processor.
            config = Config(logger, args.config)
            monitor = FileMonitor(logger, str(input_path), config, copy_mode=args.copy)
            monitor.start()
        else:
            # Batch mode: one-shot processing of existing files.
            organizer = FileOrganizer(logger)
            organizer(
                input_path=input_path,
                config_path=args.config,
                recursive=args.recursive,
                copy_mode=args.copy,
            )
    except Exception as exc:  # pragma: no cover - generic CLI error reporting
        print(f"[file_organizer] Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    raise SystemExit(main())
