"""
Command Line Interface for Face Detector.

Provides a single ``batch`` subcommand that scans a directory tree,
previews faces, extracts embeddings, and clusters results into identity domains.

Usage::

    face-detector batch --path /archive/photos
    face-detector batch --path /archive/photos --no-cluster --overwrite
    face-detector batch --path /archive/photos --db /data/faces.db
"""

import argparse
import logging
import sys
from pathlib import Path

from common.logger import Logger
from common.utils import log_banner
from common.version import get_version
from face_detector.constants import DEFAULT_DETECTOR
from face_detector.engine import FaceDetectorEngine
from face_detector.previewer import FacePreviewer


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Face Detector — preview faces, extract embeddings, cluster identities",
        epilog="Use 'face-detector <command> --help' for subcommand details.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"face-detector (florentine-abbot {get_version()})",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )
    parser.add_argument(
        "--log-path",
        metavar="DIR",
        help="Custom directory for log files (default: ~/.florentine-abbot/logs/)",
    )

    subparsers = parser.add_subparsers(dest="command")

    batch = subparsers.add_parser(
        "batch",
        help="Scan a directory tree for faces and cluster results",
        description=(
            "Recursively scan --path for image files, preview faces using DeepFace, "
            "store embeddings in a SQLite database, and cluster results into identity domains."
        ),
    )
    batch.add_argument(
        "--path", "-p",
        required=True,
        metavar="PATH",
        help="Root directory to scan for image files",
    )
    batch.add_argument(
        "--db",
        metavar="DB",
        default=None,
        help="Path to the SQLite database (default: from config or next to config file)",
    )
    batch.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-process files that already have face records in the database",
    )
    batch.add_argument(
        "--no-cluster",
        action="store_true",
        help="Skip DBSCAN clustering after previewion",
    )
    batch.add_argument(
        "--detector",
        metavar="NAME",
        default=DEFAULT_DETECTOR,
        help=f"Detector plugin to use, e.g. 'insightface' or 'deepface' (default: {DEFAULT_DETECTOR!r})",
    )
    batch.add_argument(
        "--config",
        metavar="CONFIG",
        default=None,
        help="Path to a custom config.json (default: from standard config directory)",
    )

    preview = subparsers.add_parser(
        "preview",
        help="Detect faces in a single image and save a preview with bounding boxes",
        description=(
            "Run face previewion on a single image and save a JPEG preview with "
            "numbered bounding boxes.  No database required."
        ),
    )
    preview.add_argument(
        "--file", "-i",
        required=True,
        metavar="FILE",
        help="Source image file",
    )
    preview.add_argument(
        "--output", "-o",
        metavar="OUTPUT",
        default=None,
        help="Output JPEG path (default: <file_stem>_preview.jpg next to source)",
    )
    preview.add_argument(
        "--max-size",
        type=int,
        default=3000,
        metavar="PX",
        help="Maximum long edge of the preview in pixels (default: 3000)",
    )
    preview.add_argument(
        "--detector",
        metavar="NAME",
        default=None,
        help=f"Detector plugin to use (default: from config or {DEFAULT_DETECTOR!r})",
    )
    preview.add_argument(
        "--config",
        metavar="CONFIG",
        default=None,
        help="Path to a custom config.json",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``face-detector`` CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    logger = Logger(
        "face_detector",
        args.log_path,
        level=logging.DEBUG if args.verbose else logging.INFO,
        console=True,
    )

    version = get_version()

    try:
        if args.command == "preview":
            file_path = Path(args.file)
            if not file_path.exists():
                logger.error("Image does not exist: %s", file_path)
                return 1

            log_banner(logger, "face-detector", version, {
                "Mode": "preview",
                "File": str(file_path),
                "Detector": args.detector or "from config",
                "MaxSize": f"{args.max_size}px",
            })

            viz = FacePreviewer(logger, args.config, detector=args.detector, max_size=args.max_size)
            out = viz(file_path, Path(args.output) if args.output else None)
            print(str(out))

        else:  # batch
            path = Path(args.path)
            if not path.exists():
                logger.error("Path does not exist: %s", path)
                return 1

            log_banner(logger, "face-detector", version, {
                "Mode": "batch",
                "Path": str(path),
                "Database": str(Path(args.db) if args.db else "default (from config)"),
                "Overwrite": "yes" if args.overwrite else "no",
                "Cluster": "no" if args.no_cluster else "yes",
                "Detector": args.detector,
                "Config": args.config or "default",
            })

            engine = FaceDetectorEngine(logger, args.config, detector=args.detector)
            total = engine(
                path=path,
                db_path=Path(args.db) if args.db else None,
                overwrite=args.overwrite,
                cluster=not args.no_cluster,
            )
            logger.info("Detected %d face(s) in total", total)

    except Exception as exc:
        print(f"[face_detector] Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    raise SystemExit(main())
