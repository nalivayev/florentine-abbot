"""
Command Line Interface for Preview Maker.

Provides three subcommands:

* ``preview-maker batch``    — one-shot preview generation for existing sources.
* ``preview-maker watch``    — daemon mode that monitors for new source files.
* ``preview-maker convert``  — convert a single file (no pipeline, no metadata).

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
from preview_maker.maker import PreviewMaker
from preview_maker.converter import Converter
from preview_maker.constants import FORMAT_MAP, DEFAULT_SIZE, DEFAULT_FORMAT
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
        "--no-metadata",
        action="store_true",
        help="Skip writing EXIF/XMP metadata to preview files",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview Maker - Generate preview JPEGs from source files",
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

    batch_parser = subparsers.add_parser(
        "batch",
        help="One-shot preview generation for existing source files",
        description="Scan --path for source files and generate preview JPEGs.",
    )
    _add_common_arguments(batch_parser)
    batch_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing preview files instead of keeping them",
    )

    watch_parser = subparsers.add_parser(
        "watch",
        help="Daemon mode — poll database for new files and generate previews",
        description="Poll the database for new files and generate previews continuously.",
    )
    watch_parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to preview-maker config JSON (default: standard location)",
    )

    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert a single file (no pipeline, no metadata)",
        description="Pure image conversion — resize and format change. "
                    "All parameters come from the command line.",
    )
    convert_parser.add_argument(
        "--file",
        required=True,
        type=str,
        help="Path to the source image file",
    )
    convert_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: next to source, extension from --format)",
    )
    convert_parser.add_argument(
        "--size",
        type=int,
        default=DEFAULT_SIZE,
        help=f"Maximum long edge in pixels (default: {DEFAULT_SIZE})",
    )
    convert_parser.add_argument(
        "--format",
        choices=sorted(FORMAT_MAP),
        default=DEFAULT_FORMAT,
        help=f"Output image format (default: {DEFAULT_FORMAT})",
    )
    convert_parser.add_argument(
        "--quality",
        type=int,
        default=None,
        help="Image quality for jpeg/webp (default: 80)",
    )

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
    version = get_version()

    try:
        if args.command == "convert":
            file_path = Path(args.file)
            if not file_path.exists():
                logger.error("File does not exist: %s", file_path)
                return 1

            save_options = {"quality": args.quality} if args.quality is not None else None
            converter = Converter(
                logger,
                size=args.size,
                image_format=args.format,
                save_options=save_options,
            )
            output_path = Path(args.output) if args.output else file_path.with_suffix(FORMAT_MAP[args.format][1])

            log_banner(logger, "preview-maker", version,{
                "Mode": "convert",
                "File": str(file_path),
                "Output": str(output_path),
                "Format": args.format,
                "Size": str(args.size),
            })

            converter(file_path, output_path)
            logger.info("Saved: %s", output_path)

        elif args.command == "watch":
            log_banner(logger, "preview-maker", version, {
                "Mode": "watch",
                "Config": args.config or "default",
            })
            PreviewWatcher(logger, config_path=args.config).start()

        else:  # batch
            path = Path(args.path)
            if not path.exists():
                logger.error("Path does not exist: %s", path)
                return 1
            log_banner(logger, "preview-maker", version, {
                "Mode": "batch",
                "Path": str(path),
                "Overwrite": "yes" if args.overwrite else "no",
                "No metadata": "yes" if args.no_metadata else "no",
                "Config": args.config or "default",
            })
            maker = PreviewMaker(logger, args.config, no_metadata=args.no_metadata)
            count = maker(path=path, overwrite=bool(args.overwrite))
            logger.info("Generated %d preview file(s)", count)

    except Exception as exc:  # pragma: no cover - generic CLI error reporting
        print(f"[preview_maker] Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    raise SystemExit(main())
