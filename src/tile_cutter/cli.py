"""
Command Line Interface for Tile Cutter.

Provides three subcommands:

* ``tile-cutter batch``  — one-shot tile generation for existing sources.
* ``tile-cutter process`` — generate one tile pyramid without database orchestration.
* ``tile-cutter watch``  — daemon mode that monitors for new source files.

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
from tile_cutter.classes import CutterSettings
from tile_cutter.constants import DAEMON_NAME, DEFAULT_SIZE, DEFAULT_TILE_SIZE
from tile_cutter.cutter import Cutter
from tile_cutter.processor import CutterProcessor
from tile_cutter.watcher import CutterWatcher


def _add_batch_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for batch mode without file-backed config loading."""
    parser.add_argument(
        "--path",
        required=True,
        type=str,
        help="Path to the archive root (where year folders start)",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=None,
        help="Maximum short side in pixels for generated tile pyramids",
    )
    parser.add_argument(
        "--tile-size",
        type=int,
        default=None,
        help="Tile side length in pixels for batch mode",
    )
    parser.add_argument(
        "--source-priority",
        action="append",
        default=None,
        help="Repeatable source pattern priority override for batch mode",
    )


def _build_batch_settings(args: argparse.Namespace) -> CutterSettings:
    """Create batch settings from CLI arguments without reading config files."""
    local_data: dict[str, object] = {}
    image: dict[str, object] = {}

    if args.size is not None:
        image["size"] = args.size
    if args.tile_size is not None:
        image["tile_size"] = args.tile_size
    if image:
        local_data["image"] = image

    if args.source_priority:
        local_data["priority"] = args.source_priority

    return CutterSettings.from_data(local_data=local_data)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tile Cutter - Generate image tile pyramids from source files",
        epilog="Use 'tile-cutter <command> --help' for subcommand details.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{DAEMON_NAME} (florentine-abbot {get_version()})",
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
        help="One-shot tile generation for existing source files",
        description="Scan --path for source files and generate tile pyramids.",
    )
    _add_batch_arguments(batch_parser)
    batch_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing tile sets instead of keeping them",
    )

    process_parser = subparsers.add_parser(
        "process",
        help="Generate one tile pyramid using the low-level processor",
        description="Create one tile pyramid without configuration or database orchestration.",
    )
    process_parser.add_argument(
        "--file",
        required=True,
        type=str,
        help="Path to the source image file",
    )
    process_parser.add_argument(
        "--output",
        required=True,
        type=str,
        help="Path to the output tile directory",
    )
    process_parser.add_argument(
        "--size",
        type=int,
        default=None,
        help="Maximum short side in pixels for the intermediate image",
    )
    process_parser.add_argument(
        "--tile-size",
        type=int,
        default=None,
        help="Tile side length in pixels",
    )
    process_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing tile set instead of keeping it",
    )

    watch_parser = subparsers.add_parser(
        "watch",
        help="Daemon mode — poll database for new files and generate tiles",
        description="Poll the database for new files and generate tile pyramids continuously.",
    )
    watch_parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to tile-cutter config JSON (default: standard location)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``tile-cutter`` CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    logger = Logger(
        "tile_cutter",
        args.log_path,
        level=logging.DEBUG if args.verbose else logging.INFO,
        console=True,
    )
    version = get_version()

    try:
        if args.command == "process":
            file_path = Path(args.file)
            output_dir = Path(args.output)
            if not file_path.exists():
                logger.error("File does not exist: %s", file_path)
                return 1
            if output_dir.exists() and output_dir.is_file():
                logger.error("Output path points to a file: %s", output_dir)
                return 1
            if args.size is not None and args.size <= 0:
                logger.error("Size must be a positive integer: %s", args.size)
                return 1
            if args.tile_size is not None and args.tile_size <= 0:
                logger.error("Tile size must be a positive integer: %s", args.tile_size)
                return 1

            log_banner(logger, DAEMON_NAME, version, {
                "Mode": "process",
                "File": str(file_path),
                "Output": str(output_dir),
                "Overwrite": "yes" if args.overwrite else "no",
                "Size": str(args.size) if args.size is not None else "default",
                "Tile size": str(args.tile_size) if args.tile_size is not None else "default",
            })

            processor = CutterProcessor(logger)
            count, output_dir = processor.process(
                file_path,
                output_dir=output_dir,
                preview_size=args.size if args.size is not None else DEFAULT_SIZE,
                tile_size=args.tile_size if args.tile_size is not None else DEFAULT_TILE_SIZE,
                overwrite=bool(args.overwrite),
            )
            if count > 0:
                logger.info("Generated %d tile(s) in %s", count, output_dir)
            else:
                logger.info("Tile set already exists: %s", output_dir)

        elif args.command == "watch":
            fields: dict[str, str] = {"Mode": "watch", "Config": args.config or "default"}
            log_banner(logger, DAEMON_NAME, version, fields)
            CutterWatcher(logger, config_path=args.config).start()
        else:
            path = Path(args.path)
            if not path.exists():
                logger.error("Path does not exist: %s", path)
                return 1
            if args.size is not None and args.size <= 0:
                logger.error("Size must be a positive integer: %s", args.size)
                return 1
            if args.tile_size is not None and args.tile_size <= 0:
                logger.error("Tile size must be a positive integer: %s", args.tile_size)
                return 1
            fields = {
                "Mode": "batch",
                "Path": str(path),
                "Overwrite": "yes" if args.overwrite else "no",
                "Size": str(args.size) if args.size is not None else "default",
                "Tile size": str(args.tile_size) if args.tile_size is not None else "default",
            }
            log_banner(logger, DAEMON_NAME, version, fields)
            cutter = Cutter(logger, settings=_build_batch_settings(args))
            count = cutter.execute(path=path, overwrite=bool(args.overwrite))
            logger.info("Generated %d tile set(s)", count)

    except Exception as exc:  # pragma: no cover
        print(f"[tile_cutter] Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
