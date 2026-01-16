"""Command Line Interface for Preview Maker.

Parses command-line arguments and delegates work to :mod:`preview_maker.maker`.
The ``preview-maker`` console script is wired to :func:`main`.
"""

import argparse
import logging
import sys
from pathlib import Path

from common.logger import Logger
from preview_maker.maker import PreviewMaker


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate PRV (preview) JPEGs from source images using Pillow "
            "in batch mode over processed/ SOURCES trees."
        )
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
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--log-path",
        help="Custom directory for log files (default: ~/.florentine-abbot/logs/)",
    )
    parser.add_argument(
        "--path",
        help=(
            "Path to scan in batch mode. PRV files "
            "are generated for SOURCES/ under this path."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing PRV files instead of keeping them.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the `preview-maker` CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        logger = Logger(
            "preview_maker",
            args.log_path,
            level=logging.DEBUG if args.verbose else logging.INFO,
            console=True,
        )
        maker = PreviewMaker(logger)

        if not args.path:
            raise ValueError("Specify --path for batch mode.")

        path = Path(args.path)
        logger.info(f"Starting batch PRV generation under {path}")

        count = maker(
            path=path,
            overwrite=bool(args.overwrite),
            max_size=args.max_size,
            quality=args.quality,
        )
        logger.info(f"Generated {count} PRV file(s) under {path}")
    except Exception as exc:  # pragma: no cover - generic CLI error reporting
        print(f"[preview_maker] Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    raise SystemExit(main())
