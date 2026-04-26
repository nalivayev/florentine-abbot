"""Command Line Interface for Face Recognizer.

Provides four subcommands:

* ``face-recognizer batch``   — one-shot face detection for an archive tree.
* ``face-recognizer process`` — detect faces in one file without DB orchestration.
* ``face-recognizer preview`` — draw bounding boxes for one file.
* ``face-recognizer watch``   — daemon mode that polls the archive DB.

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
from face_recognizer.classes import RecognizerSettings
from face_recognizer.constants import DAEMON_NAME, DEFAULT_DETECTOR
from face_recognizer.recognizer import Recognizer
from face_recognizer.previewer import RecognizerPreviewer
from face_recognizer.processor import RecognizerProcessor
from face_recognizer.watcher import RecognizerWatcher


def _add_batch_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for batch mode without file-backed config loading."""
    parser.add_argument(
        "--path", "-p",
        required=True,
        metavar="PATH",
        help="Root directory to scan for image files",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-process files that already have face records in the database",
    )
    parser.add_argument(
        "--no-cluster",
        action="store_true",
        help="Skip DBSCAN clustering after detection",
    )
    parser.add_argument(
        "--detector",
        metavar="NAME",
        default=DEFAULT_DETECTOR,
        help=f"Detector plugin to use (default: {DEFAULT_DETECTOR!r})",
    )
    parser.add_argument(
        "--source-priority",
        action="append",
        default=None,
        help="Repeatable glob priority override for eligible master files",
    )
    parser.add_argument(
        "--source-extension",
        action="append",
        default=None,
        help="Repeatable source extension override for eligible image files",
    )
    parser.add_argument(
        "--eps",
        type=float,
        default=None,
        help="DBSCAN cosine distance threshold override for batch mode",
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=None,
        help="DBSCAN min_samples override for batch mode",
    )


def _build_batch_settings(args: argparse.Namespace) -> RecognizerSettings:
    """Create batch settings from CLI arguments without reading config files."""
    return RecognizerSettings.from_data(
        detector=args.detector,
        source_extensions=args.source_extension,
        source_priority=args.source_priority,
        clustering_eps=args.eps,
        clustering_min_samples=args.min_samples,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Face Recognizer — preview faces, extract embeddings, cluster identities",
        epilog="Use 'face-recognizer <command> --help' for subcommand details.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{DAEMON_NAME} (florentine-abbot {get_version()})",
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
    _add_batch_arguments(batch)

    process = subparsers.add_parser(
        "process",
        help="Detect faces in one image without database orchestration",
        description="Run low-level face detection for one file and print the face count.",
    )
    process.add_argument(
        "--file", "-i",
        required=True,
        metavar="FILE",
        help="Source image file",
    )
    process.add_argument(
        "--detector",
        metavar="NAME",
        default=DEFAULT_DETECTOR,
        help=f"Detector plugin to use (default: {DEFAULT_DETECTOR!r})",
    )

    preview = subparsers.add_parser(
        "preview",
        help="Detect faces in a single image and save a preview with bounding boxes",
        description=(
            "Run face detection on a single image and save a JPEG preview with "
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
        default=DEFAULT_DETECTOR,
        help=f"Detector plugin to use (default: {DEFAULT_DETECTOR!r})",
    )

    watch = subparsers.add_parser(
        "watch",
        help="Daemon mode — poll the archive DB for new files and detect faces",
        description="Poll the archive DB for new or modified files and index detected faces continuously.",
    )
    watch.add_argument(
        "--config",
        metavar="CONFIG",
        default=None,
        help="Path to a custom config.json (default: standard config location)",
    )
    watch.add_argument(
        "--no-cluster",
        action="store_true",
        help="Skip DBSCAN clustering in daemon mode",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``face-recognizer`` CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    logger = Logger(
        "face_recognizer",
        args.log_path,
        level=logging.DEBUG if args.verbose else logging.INFO,
        console=True,
    )

    version = get_version()

    try:
        if args.command == "process":
            file_path = Path(args.file)
            if not file_path.exists():
                logger.error("Image does not exist: %s", file_path)
                return 1
            if not file_path.is_file():
                logger.error("Path is not a file: %s", file_path)
                return 1

            log_banner(logger, DAEMON_NAME, version, {
                "Mode": "process",
                "File": str(file_path),
                "Detector": args.detector,
            })

            processor = RecognizerProcessor(logger, detector_name=args.detector)
            faces = processor.process(file_path)
            logger.info("Detected %d face(s) in %s", len(faces), file_path.name)
            print(len(faces))

        elif args.command == "preview":
            file_path = Path(args.file)
            if not file_path.exists():
                logger.error("Image does not exist: %s", file_path)
                return 1
            if not file_path.is_file():
                logger.error("Path is not a file: %s", file_path)
                return 1
            if args.max_size <= 0:
                logger.error("Max size must be a positive integer: %s", args.max_size)
                return 1

            log_banner(logger, DAEMON_NAME, version, {
                "Mode": "preview",
                "File": str(file_path),
                "Detector": args.detector,
                "MaxSize": f"{args.max_size}px",
            })

            processor = RecognizerProcessor(logger, detector_name=args.detector)
            viz = RecognizerPreviewer(logger, processor, max_size=args.max_size)
            out = viz.preview(file_path, Path(args.output) if args.output else None)
            print(str(out))

        elif args.command == "watch":
            log_banner(logger, DAEMON_NAME, version, {
                "Mode": "watch",
                "Config": args.config or "default",
                "Cluster": "no" if args.no_cluster else "yes",
            })

            watcher = RecognizerWatcher(
                logger,
                config_path=args.config,
                cluster=not args.no_cluster,
            )
            watcher.start()

        else:  # batch
            path = Path(args.path)
            if not path.exists():
                logger.error("Path does not exist: %s", path)
                return 1
            if not path.is_dir():
                logger.error("Path is not a directory: %s", path)
                return 1
            if args.eps is not None and args.eps < 0:
                logger.error("DBSCAN eps must be non-negative: %s", args.eps)
                return 1
            if args.min_samples is not None and args.min_samples <= 0:
                logger.error("DBSCAN min_samples must be positive: %s", args.min_samples)
                return 1

            settings = _build_batch_settings(args)

            log_banner(logger, DAEMON_NAME, version, {
                "Mode": "batch",
                "Path": str(path),
                "Overwrite": "yes" if args.overwrite else "no",
                "Cluster": "no" if args.no_cluster else "yes",
                "Detector": settings.detector,
            })

            engine = Recognizer(logger, settings=settings)
            total = engine.execute(
                path=path,
                overwrite=args.overwrite,
                cluster=not args.no_cluster,
            )
            logger.info("Detected %d face(s) in total", total)

    except Exception as exc:
        print(f"[face_recognizer] Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    raise SystemExit(main())
