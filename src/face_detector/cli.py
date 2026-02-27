"""
Command Line Interface for Face Detector.

Provides a single ``batch`` subcommand that scans a directory tree,
detects faces, extracts embeddings, and clusters results into identity domains.

Usage::

    face-detector batch --path /archive/photos
    face-detector batch --path /archive/photos --no-cluster --overwrite
    face-detector batch --path /archive/photos --db /data/faces.db
"""

import argparse
import logging
from pathlib import Path

from common.logger import Logger
from common.version import get_version
from face_detector.config import Config
from face_detector.constants import DEFAULT_DETECTOR
from face_detector.engine import FaceDetectorEngine
from face_detector.store import FaceStore
from face_detector.visualizer import FaceVisualizer


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Face Detector — detect faces, extract embeddings, cluster identities",
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
            "Recursively scan --path for image files, detect faces using DeepFace, "
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
        help="Skip DBSCAN clustering after detection",
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

    viz = subparsers.add_parser(
        "visualize",
        help="Draw detected face bounding boxes on a preview image",
        description=(
            "Load a source image and its face records from the database, "
            "draw red bounding boxes and save a JPEG preview."
        ),
    )
    viz.add_argument(
        "--image", "-i",
        required=True,
        metavar="IMAGE",
        help="Source image file (the same path that was processed by 'batch')",
    )
    viz.add_argument(
        "--db",
        metavar="DB",
        default=None,
        help="Path to the SQLite database (default: from config)",
    )
    viz.add_argument(
        "--output", "-o",
        metavar="OUTPUT",
        default=None,
        help="Output JPEG path (default: <image_stem>_faces.jpg next to source)",
    )
    viz.add_argument(
        "--max-size",
        type=int,
        default=3000,
        metavar="PX",
        help="Maximum long edge of the preview in pixels (default: 3000)",
    )
    viz.add_argument(
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

    if args.command == "visualize":
        image_path = Path(args.image)
        db_path = Path(args.db) if args.db else None

        logger.info("-" * 45)
        logger.info("  face-detector %s", version)
        logger.info("  Mode:    visualize")
        logger.info("  Image:   %s", image_path)
        logger.info("  DB:      %s", db_path or "default (from config)")
        logger.info("  MaxSize: %spx", args.max_size)
        logger.info("-" * 45)

        if not image_path.exists():
            logger.error("Image does not exist: %s", image_path)
            return 1

        config = Config(logger, args.config)
        resolved_db = db_path or config.default_db_path

        try:
            with FaceStore(resolved_db) as store:
                viz = FaceVisualizer(logger, max_size=args.max_size)
                out = viz.draw(
                    image_path=image_path,
                    store=store,
                    output_path=Path(args.output) if args.output else None,
                )
            print(str(out))
            return 0
        except Exception as exc:  # noqa: BLE001
            logger.error("Fatal error: %s", exc, exc_info=args.verbose)
            return 1

    path = Path(args.path)
    db_path = Path(args.db) if args.db else None

    logger.info("-" * 45)
    logger.info("  face-detector %s", version)
    logger.info("  Path:          %s", path)
    logger.info("  Database:      %s", db_path or "default (from config)")
    logger.info("  Overwrite:     %s", "yes" if args.overwrite else "no")
    logger.info("  Cluster:       %s", "no" if args.no_cluster else "yes")
    logger.info("  Detector:      %s", args.detector)
    logger.info("  Config:        %s", args.config or "default")
    logger.info("-" * 45)

    if not path.exists():
        logger.error("Path does not exist: %s", path)
        return 1

    try:
        engine = FaceDetectorEngine(logger, args.config, detector=args.detector)
        total = engine(
            path=path,
            db_path=db_path,
            overwrite=args.overwrite,
            cluster=not args.no_cluster,
        )
        logger.info("Detected %d face(s) in total", total)
        return 0

    except Exception as exc:  # noqa: BLE001
        logger.error("Fatal error: %s", exc, exc_info=args.verbose)
        return 1


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    raise SystemExit(main())
