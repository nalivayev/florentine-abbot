"""
Command Line Interface for Preview Maker.

Provides two subcommands:

* ``preview-maker batch`` — one-shot PRV generation for existing masters.
* ``preview-maker watch`` — daemon mode that monitors for new masters.

Global flags (``--verbose``, ``--log-path``, ``--version``)
are shared across both subcommands.
"""

import argparse
import logging
import sys
from pathlib import Path

from common.logger import Logger
from common.version import get_version
from preview_maker.maker import PreviewMaker
from preview_maker.watcher import PreviewWatcher


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
        help="Path to preview-maker config JSON (default: ~/.config/florentine-abbot/preview-maker/config.json)",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=2000,
        help="Maximum long edge in pixels for the preview (default: 2000)",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=80,
        help="JPEG quality (1-100, default: 80)",
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Skip writing EXIF/XMP metadata to PRV files",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview Maker - Generate PRV JPEGs from master sources",
        epilog="Use 'preview-maker <command> --help' for subcommand details.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"preview-maker (florentine-abbot {get_version()})",
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
        help="One-shot PRV generation for existing master files",
        description="Scan --path for RAW/MSR masters and generate PRV JPEGs.",
    )
    _add_common_arguments(batch_parser)
    batch_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing PRV files instead of keeping them",
    )

    # ── watch ──────────────────────────────────────────────────────────
    watch_parser = subparsers.add_parser(
        "watch",
        help="Daemon mode — watch for new master files",
        description="Watch --path for new RAW/MSR masters and generate PRVs continuously.",
    )
    _add_common_arguments(watch_parser)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``preview-maker`` CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    logger = Logger(
        "preview_maker",
        args.log_path,
        level=logging.DEBUG if args.verbose else logging.INFO,
        console=True,
    )

    path = Path(args.path)
    if not path.exists():
        logger.error(f"Path does not exist: {path}")
        return 1

    try:
        if args.command == "watch":
            watcher = PreviewWatcher(
                logger,
                path=str(path),
                config_path=args.config,
                max_size=args.max_size,
                quality=args.quality,
                no_metadata=args.no_metadata,
            )
            watcher.start()
        else:
            # batch
            maker = PreviewMaker(logger, args.config, no_metadata=args.no_metadata)
            count = maker(
                path=path,
                overwrite=bool(args.overwrite),
                max_size=args.max_size,
                quality=args.quality,
            )
            logger.info(f"Generated {count} PRV file(s)")
    except Exception as exc:  # pragma: no cover - generic CLI error reporting
        print(f"[preview_maker] Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    raise SystemExit(main())
