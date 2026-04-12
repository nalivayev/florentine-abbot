"""
Command Line Interface for Tile Cutter.

Provides two subcommands:

* ``tile-cutter batch``  — one-shot tile generation for existing sources.
* ``tile-cutter watch``  — daemon mode that monitors for new source files.

Global flags (``--verbose``, ``--log-path``, ``--version``)
are shared across both subcommands.
"""

import argparse
import logging
import sys
from pathlib import Path

from common.logger import Logger
from common.utils import log_banner
from common.version import get_version
from tile_cutter.cutter import TileCutter
from tile_cutter.watcher import TileWatcher


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments shared between batch and watch subcommands."""
    parser.add_argument(
        "--path",
        required=True,
        type=str,
        help="Path to the archive root (where year folders start)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to tile-cutter config JSON (default: ~/.config/florentine-abbot/tile-cutter/config.json)",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tile Cutter - Generate image tile pyramids from source files",
        epilog="Use 'tile-cutter <command> --help' for subcommand details.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"tile-cutter (florentine-abbot {get_version()})",
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
    _add_common_arguments(batch_parser)
    batch_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing tile sets instead of keeping them",
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
        if args.command == "watch":
            fields: dict[str, str] = {"Mode": "watch", "Config": args.config or "default"}
            log_banner(logger, "tile-cutter", version, fields)
            TileWatcher(logger, config_path=args.config).start()
        else:
            path = Path(args.path)
            if not path.exists():
                logger.error("Path does not exist: %s", path)
                return 1
            fields = {"Mode": "batch", "Path": str(path), "Overwrite": "yes" if args.overwrite else "no", "Config": args.config or "default"}
            log_banner(logger, "tile-cutter", version, fields)
            cutter = TileCutter(logger, args.config)
            count = cutter(path=path, overwrite=bool(args.overwrite))
            logger.info("Generated %d tile set(s)", count)

    except Exception as exc:  # pragma: no cover
        print(f"[tile_cutter] Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
