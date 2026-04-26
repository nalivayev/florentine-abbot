"""
Command Line Interface for Preview Maker.

Provides three subcommands:

* ``preview-maker batch``    — one-shot preview generation for existing sources.
* ``preview-maker process``  — generate one preview file without metadata.
* ``preview-maker watch``    — daemon mode that monitors for new source files.

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
from preview_maker.classes import MakerSettings
from preview_maker.constants import DAEMON_NAME, DEFAULT_SIZE
from preview_maker.maker import Maker
from preview_maker.processor import MakerProcessor
from preview_maker.watcher import MakerWatcher


def _add_batch_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for batch mode without file-backed config loading."""
    parser.add_argument(
        "--path",
        required=True,
        type=str,
        help="Path to the archive root (where year folders start)",
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Skip writing EXIF/XMP metadata to preview files",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=None,
        help="Maximum long edge in pixels for generated previews",
    )
    parser.add_argument(
        "--format",
        choices=["jpeg", "png", "webp", "tiff"],
        default=None,
        help="Output image format for generated previews",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=None,
        help="Quality for jpeg/webp output in batch mode",
    )
    parser.add_argument(
        "--template",
        type=str,
        default=None,
        help="Preview filename template stem for batch mode",
    )
    parser.add_argument(
        "--source-priority",
        action="append",
        default=None,
        help="Repeatable source pattern priority override for batch mode",
    )


def _build_batch_settings(args: argparse.Namespace) -> MakerSettings:
    """Create batch settings from CLI arguments without reading config files."""
    local_data: dict[str, object] = {}
    image: dict[str, object] = {}

    if args.size is not None:
        image["size"] = args.size
    if args.format is not None:
        image["format"] = args.format
    if args.quality is not None:
        format_name = args.format or "jpeg"
        image[format_name] = {"quality": args.quality}
    if image:
        local_data["image"] = image

    if args.template is not None:
        local_data["template"] = args.template
    if args.source_priority:
        local_data["priority"] = args.source_priority

    return MakerSettings.from_data(local_data=local_data, no_metadata=bool(args.no_metadata))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview Maker - Generate preview JPEGs from source files",
        epilog="Use 'preview-maker <command> --help' for subcommand details.",
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
        help="One-shot preview generation for existing source files",
        description="Scan --path for source files and generate preview JPEGs.",
    )
    _add_batch_arguments(batch_parser)
    batch_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing preview files instead of keeping them",
    )

    process_parser = subparsers.add_parser(
        "process",
        help="Generate one preview file using the low-level processor",
        description="Create one preview file without metadata or database orchestration.",
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
        help="Path to the output preview file",
    )
    process_parser.add_argument(
        "--size",
        type=int,
        default=None,
        help="Maximum long edge in pixels (default: built-in processor default)",
    )
    process_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing preview file instead of keeping it",
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
        if args.command == "process":
            file_path = Path(args.file)
            output_path = Path(args.output)
            if not file_path.exists():
                logger.error("File does not exist: %s", file_path)
                return 1
            if output_path.exists() and output_path.is_dir():
                logger.error("Output path points to a directory: %s", output_path)
                return 1
            if args.size is not None and args.size <= 0:
                logger.error("Size must be a positive integer: %s", args.size)
                return 1

            log_banner(logger, DAEMON_NAME, version, {
                "Mode": "process",
                "File": str(file_path),
                "Output": str(output_path),
                "Overwrite": "yes" if args.overwrite else "no",
                "Size": str(args.size) if args.size else "default",
            })

            processor = MakerProcessor(logger)
            written, output_path = processor.process(
                file_path,
                output_path=output_path,
                size=args.size if args.size is not None else DEFAULT_SIZE,
                overwrite=bool(args.overwrite),
            )
            if written:
                logger.info("Generated preview: %s", output_path)
            else:
                logger.info("Preview already exists: %s", output_path)

        elif args.command == "watch":
            log_banner(logger, DAEMON_NAME, version, {
                "Mode": "watch",
                "Config": args.config or "default",
            })
            MakerWatcher(logger, config_path=args.config).start()

        else:  # batch
            path = Path(args.path)
            if not path.exists():
                logger.error("Path does not exist: %s", path)
                return 1
            if args.size is not None and args.size <= 0:
                logger.error("Size must be a positive integer: %s", args.size)
                return 1
            if args.quality is not None and args.quality <= 0:
                logger.error("Quality must be a positive integer: %s", args.quality)
                return 1
            log_banner(logger, DAEMON_NAME, version, {
                "Mode": "batch",
                "Path": str(path),
                "Overwrite": "yes" if args.overwrite else "no",
                "No metadata": "yes" if args.no_metadata else "no",
                "Size": str(args.size) if args.size is not None else "default",
                "Format": args.format or "default",
            })
            maker = Maker(logger, settings=_build_batch_settings(args))
            count = maker.execute(path=path, overwrite=bool(args.overwrite))
            logger.info("Generated %d preview file(s)", count)

    except Exception as exc:  # pragma: no cover - generic CLI error reporting
        print(f"[preview_maker] Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    raise SystemExit(main())
