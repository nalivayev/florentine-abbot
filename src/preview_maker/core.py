"""Core implementation for Preview Maker.

Provides functions to generate PRV (preview) JPEGs from RAW/MSR sources,
plus a `main()` suitable for CLI use.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from PIL import Image

from common.logger import Logger
from file_organizer.parser import FilenameParser


def convert_to_prv(
    input_path: Path,
    output_path: Path,
    max_size: int = 2000,
    quality: int = 80,
) -> None:
    """Convert a single source image to a PRV JPEG."""

    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    Image.MAX_IMAGE_PIXELS = None

    with Image.open(input_path) as img:
        img.load()

        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, format="JPEG", quality=quality, optimize=True)


def generate_previews_for_sources(
    path: Path,
    overwrite: bool = False,
    max_size: int = 2000,
    quality: int = 80,
) -> int:
    """Walk under ``path`` and generate PRV JPEGs for SOURCES/ files."""

    parser = FilenameParser()
    written = 0

    for dirpath in path.rglob("SOURCES"):
        if not dirpath.is_dir():
            continue

        date_dir = dirpath.parent

        for src_path in dirpath.iterdir():
            if not src_path.is_file():
                continue

            parsed = parser.parse(src_path.name)
            if not parsed:
                continue

            suffix = parsed.suffix.upper()
            if suffix not in {"RAW", "MSR"}:
                continue

            if suffix == "RAW":
                msr_name = src_path.name.replace(".RAW.", ".MSR.")
                msr_candidate = src_path.with_name(msr_name)
                if msr_candidate.exists():
                    continue

            base = (
                f"{parsed.year:04d}.{parsed.month:02d}.{parsed.day:02d}."
                f"{parsed.hour:02d}.{parsed.minute:02d}.{parsed.second:02d}."
                f"{parsed.modifier}.{parsed.group}.{parsed.subgroup}."
                f"{int(parsed.sequence):04d}.{parsed.side}.PRV.jpg"
            )

            prv_path = date_dir / base

            if prv_path.exists() and not overwrite:
                continue

            convert_to_prv(src_path, prv_path, max_size=max_size, quality=quality)
            written += 1

    return written


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate PRV (preview) JPEGs from source images using Pillow. "
            "Can work in single-file mode or batch mode over SOURCES/ trees."
        )
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        help="Path to the source image (e.g. RAW TIFF or MSR TIFF)",
    )
    parser.add_argument(
        "output_path",
        nargs="?",
        help=(
            "Path to the output JPEG (e.g. "
            "1945.06.15.12.00.00.E.FAM.POR.0001.A.PRV.jpg)"
        ),
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
            "Path to scan in batch mode. If provided, PRV files "
            "are generated for SOURCES/ under this path."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing PRV files instead of keeping them.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        if args.path:
            logger = Logger(
                "preview_maker",
                args.log_path,
                level=logging.DEBUG if args.verbose else logging.INFO,
                console=True,
            )

            path = Path(args.path)
            logger.info(f"Starting batch PRV generation under {path}")

            count = generate_previews_for_sources(
                path=path,
                overwrite=bool(args.overwrite),
                max_size=args.max_size,
                quality=args.quality,
            )
            logger.info(f"Generated {count} PRV file(s) under {path}")
        else:
            if not args.input_path or not args.output_path:
                raise ValueError(
                    "Either specify --path for batch mode or provide "
                    "INPUT_PATH and OUTPUT_PATH for single-file mode."
                )

            logger = Logger(
                "preview_maker",
                args.log_path,
                level=logging.DEBUG if args.verbose else logging.INFO,
                console=True,
            )

            input_path = Path(args.input_path)
            output_path = Path(args.output_path)

            logger.info(f"Converting single file to PRV: {input_path} -> {output_path}")
            convert_to_prv(
                input_path=input_path,
                output_path=output_path,
                max_size=args.max_size,
                quality=args.quality,
            )
    except Exception as exc:  # pragma: no cover - generic CLI error reporting
        print(f"[preview_maker] Error: {exc}", file=sys.stderr)
        return 1

    return 0


__all__ = [
    "convert_to_prv",
    "generate_previews_for_sources",
    "main",
]
