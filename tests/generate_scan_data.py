"""
Test data generator — synthetic scan-batcher output files.

Generates TIFF or JPEG images with filenames and XMP metadata that match
what scan-batcher produces, so they can be fed to content-importer tests.

Simulates the full two-phase metadata workflow:
  Phase 1 — scanner EXIF (VueScan): Make, Model, Software, CreateDate (no TZ)
  Phase 2 — scan-batcher XMP:     DocumentID, InstanceID, DateTimeDigitized
                                   with TZ, XMP History (created + edited)

Usage (from project root):
    python -m tests.generate_scan_data --output /tmp/scans --count 5
    python -m tests.generate_scan_data -o /tmp/scans -n 3 --date 2025-06-01
    python -m tests.generate_scan_data -o /tmp/scans --modifier E --group FAM
"""

import argparse
import random
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

# Ensure src/ is on the path when running as a script
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))

from common.constants import (
    TAG_IFD0_MAKE, TAG_IFD0_MODEL, TAG_IFD0_SOFTWARE, TAG_EXIFIFD_CREATE_DATE,
)
from common.logger import Logger
from tests.common.fake_exifer import FakeExifer
from tests.scan_batcher.fake_metadata_workflow import FakeMetadataWorkflow


_SCANNER_MAKE = "Epson"
_SCANNER_MODEL = "Perfection V850 Photo"
_SCANNER_SOFTWARE = "VueScan 9 x64 (9.8.50)"

# Source filename template (without format specifiers — matches what VueScan produces)
# {year}.{month}.{day}.{hour}.{minute}.{second}.{modifier}.{group}.{subgroup}.{sequence}.{side}.{suffix}.{extension}
_SOURCE_TEMPLATE = (
    "{year:04d}.{month:02d}.{day:02d}."
    "{hour:02d}.{minute:02d}.{second:02d}."
    "{modifier}.{group}.{subgroup}.{sequence:04d}.{side}.{suffix}.{extension}"
)

_MIME_TYPES = {"tif": "image/tiff", "jpg": "image/jpeg"}

_COLORS = [
    (225, 168, 168),  # red
    (168, 182, 225),  # blue
    (168, 215, 178),  # green
    (225, 218, 168),  # gold
    (195, 172, 225),  # purple
    (168, 212, 212),  # teal
    (228, 198, 168),  # orange
    (225, 172, 198),  # pink
    (168, 192, 225),  # sky blue
    (212, 225, 172),  # lime
    (178, 180, 218),  # indigo
    (222, 195, 168),  # brown
]

_BACKGROUNDS = [
    (248, 242, 232),
    (232, 240, 248),
    (238, 248, 234),
    (248, 234, 240),
    (234, 234, 248),
]


def _make_image(width: int, height: int, seed: int) -> Image.Image:
    """Generate a synthetic image with overlapping shapes and a border."""
    rng = random.Random(seed)

    bg = _BACKGROUNDS[seed % len(_BACKGROUNDS)]
    base = Image.new("RGB", (width, height), bg)

    for _ in range(75):
        color = rng.choice(_COLORS)
        cx = rng.randint(0, width)
        cy = rng.randint(0, height)
        rx = rng.randint(width // 12, width // 4)
        ry = rng.randint(height // 12, height // 4)
        bbox = [cx - rx, cy - ry, cx + rx, cy + ry]

        shape = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(shape)
        # Random convex polygon with random number of sides
        import math
        sides = rng.randint(3, 12)
        angles = sorted(rng.uniform(0, 2 * math.pi) for _ in range(sides))
        pts = [
            (cx + rx * math.cos(a), cy + ry * math.sin(a))
            for a in angles
        ]
        draw.polygon(pts, fill=color)

        base = Image.blend(base, ImageChops.multiply(base, shape), alpha=0.6)

    # Solid border — 20px, light (visible on dark background)
    result = base.convert("RGB")
    draw_final = ImageDraw.Draw(result)
    border = 20
    bc = (20, 20, 20)
    draw_final.rectangle([0, 0, width - 1, border - 1], fill=bc)
    draw_final.rectangle([0, height - border, width - 1, height - 1], fill=bc)
    draw_final.rectangle([0, 0, border - 1, height - 1], fill=bc)
    draw_final.rectangle([width - border, 0, width - 1, height - 1], fill=bc)

    return result


def generate_files(
    output: Path,
    count: int,
    scan_date: date,
    scan_time: datetime,
    group: str,
    subgroup: str,
    modifier: str,
    side: str,
    suffix: str,
    extension: str,
    sequence_start: int,
    scanner_make: str,
    scanner_model: str,
    scanner_software: str,
) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    exifer = FakeExifer()
    logger = Logger("generate_scan_data", console=False)
    workflow = FakeMetadataWorkflow(logger)

    generated: list[Path] = []

    for i in range(count):
        seq = sequence_start + i
        file_time = scan_time + timedelta(minutes=i)

        # Build source-scheme filename
        name = _SOURCE_TEMPLATE.format(
            year=file_time.year,
            month=file_time.month,
            day=file_time.day,
            hour=file_time.hour,
            minute=file_time.minute,
            second=file_time.second,
            modifier=modifier,
            group=group,
            subgroup=subgroup,
            sequence=seq,
            side=side,
            suffix=suffix,
            extension=extension,
        )
        file_path = output / name

        # Create synthetic image with geometric shapes and border
        fmt = "TIFF" if extension in ("tif", "tiff") else "JPEG"
        img = _make_image(3000, 4000, seed=seq)
        img.save(file_path, format=fmt)

        # Phase 1: scanner EXIF (VueScan writes these without TZ)
        create_date = file_time.strftime("%Y:%m:%d %H:%M:%S")

        exifer.write(file_path, {
            TAG_IFD0_MAKE: scanner_make,
            TAG_IFD0_MODEL: scanner_model,
            TAG_IFD0_SOFTWARE: scanner_software,
            TAG_EXIFIFD_CREATE_DATE: create_date,
        })

        # Phase 2: scan-batcher XMP metadata (IDs, DateTimeDigitized with TZ, History)
        file_datetime = workflow.get_digitized_datetime(file_path)
        workflow.write_xmp_metadata(file_path, file_datetime)

        generated.append(file_path)
        print(f"  {file_path.name}")

    return generated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic scan-batcher output files for content-importer tests.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("-o", "--output", required=True, type=Path,
                        help="Destination directory for generated files")
    parser.add_argument("-n", "--count", type=int, default=1,
                        help="Number of files to generate (default: 1)")
    parser.add_argument("--date", default=None,
                        help="Scan date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--time", default="10:00:00",
                        help="Scan time in HH:MM:SS format (default: 10:00:00)")
    parser.add_argument("--group", default="FAM",
                        help="Archive group (default: FAM)")
    parser.add_argument("--subgroup", default="POR",
                        help="Archive subgroup (default: POR)")
    parser.add_argument("--modifier", default="A", choices=["A", "B", "C", "E", "F"],
                        help="Filename modifier (default: A)")
    parser.add_argument("--side", default="A", choices=["A", "R"],
                        help="Scan side (default: A)")
    parser.add_argument("--suffix", default="RAW",
                        help="Filename suffix (default: RAW)")
    parser.add_argument("--extension", default="tif", choices=["tif", "jpg"],
                        help="File extension (default: tif)")
    parser.add_argument("--sequence-start", type=int, default=1,
                        help="Starting sequence number (default: 1)")
    parser.add_argument("--make", default=_SCANNER_MAKE,
                        help=f"Scanner make (default: {_SCANNER_MAKE!r})")
    parser.add_argument("--model", default=_SCANNER_MODEL,
                        help=f"Scanner model (default: {_SCANNER_MODEL!r})")
    parser.add_argument("--software", default=_SCANNER_SOFTWARE,
                        help=f"Scanner software (default: {_SCANNER_SOFTWARE!r})")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    scan_date = (
        date.fromisoformat(args.date)
        if args.date
        else date.today()
    )
    h, m, s = (int(x) for x in args.time.split(":"))
    scan_time = datetime(scan_date.year, scan_date.month, scan_date.day, h, m, s)

    print(f"Generating {args.count} file(s) in {args.output}/")
    generated = generate_files(
        output=args.output,
        count=args.count,
        scan_date=scan_date,
        scan_time=scan_time,
        group=args.group,
        subgroup=args.subgroup,
        modifier=args.modifier,
        side=args.side,
        suffix=args.suffix,
        extension=args.extension,
        sequence_start=args.sequence_start,
        scanner_make=args.make,
        scanner_model=args.model,
        scanner_software=args.software,
    )
    print(f"Done. {len(generated)} file(s) created.")


if __name__ == "__main__":
    main()
