"""
Synthetic image generator.

Generates TIFF or JPEG images with randomly overlapping geometric shapes,
useful for testing image-processing pipelines.

Usage (from project root):
    python scripts/generate_scan_data.py -o /tmp/images -n 5
    python scripts/generate_scan_data.py -o /tmp/images --image-style gray --gray-level 160
    python scripts/generate_scan_data.py -o /tmp/images --width 1500 --height 2000 --seed 42
"""

import argparse
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


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


def _make_synthetic_image(width: int, height: int, seed: int, shapes: int = 120) -> Image.Image:
    rng = random.Random(seed)

    bg = _BACKGROUNDS[seed % len(_BACKGROUNDS)]
    base = Image.new("RGB", (width, height), bg)

    for _ in range(shapes):
        color = rng.choice(_COLORS)
        cx = rng.randint(0, width)
        cy = rng.randint(0, height)
        rx = rng.randint(width // 12, width // 4)
        ry = rng.randint(height // 12, height // 4)

        shape = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(shape)
        sides = rng.randint(3, 12)
        angles = sorted(rng.uniform(0, 2 * math.pi) for _ in range(sides))
        pts = [
            (cx + rx * math.cos(a), cy + ry * math.sin(a))
            for a in angles
        ]
        draw.polygon(pts, fill=color)

        base = Image.blend(base, ImageChops.multiply(base, shape), alpha=0.6)

    result = base.convert("RGB")
    draw_final = ImageDraw.Draw(result)
    border = 20
    bc = (20, 20, 20)
    draw_final.rectangle([0, 0, width - 1, border - 1], fill=bc)
    draw_final.rectangle([0, height - border, width - 1, height - 1], fill=bc)
    draw_final.rectangle([0, 0, border - 1, height - 1], fill=bc)
    draw_final.rectangle([width - border, 0, width - 1, height - 1], fill=bc)

    return result


def _make_flat_gray_image(width: int, height: int, seed: int, gray_level: int | None) -> Image.Image:
    if gray_level is None:
        level = 96 + (seed * 17 % 96)
    else:
        level = max(0, min(255, gray_level))

    return Image.new("RGB", (width, height), (level, level, level))


def _make_image(width: int, height: int, seed: int, style: str, gray_level: int | None, shapes: int = 120) -> Image.Image:
    if style == "gray":
        return _make_flat_gray_image(width, height, seed, gray_level)
    return _make_synthetic_image(width, height, seed, shapes=shapes)


def generate_files(
    output: Path,
    count: int,
    width: int,
    height: int,
    extension: str,
    style: str,
    gray_level: int | None,
    seed: int,
    shapes: int = 120,
) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    fmt = "TIFF" if extension in ("tif", "tiff") else "JPEG"
    generated: list[Path] = []

    for i in range(count):
        name = f"image_{i + 1:04d}.{extension}"
        file_path = output / name
        img = _make_image(width, height, seed=seed + i, style=style, gray_level=gray_level, shapes=shapes)
        img.save(file_path, format=fmt)
        generated.append(file_path)
        print(f"  {file_path.name}")

    return generated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic images with overlapping geometric shapes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("-o", "--output", required=True, type=Path,
                        help="Destination directory for generated files")
    parser.add_argument("-n", "--count", type=int, default=1,
                        help="Number of files to generate (default: 1)")
    parser.add_argument("--width", type=int, default=3000,
                        help="Image width in pixels (default: 3000)")
    parser.add_argument("--height", type=int, default=4000,
                        help="Image height in pixels (default: 4000)")
    parser.add_argument("--extension", default="tif", choices=["tif", "jpg"],
                        help="File extension (default: tif)")
    parser.add_argument("--style", default="synthetic", choices=["synthetic", "gray"],
                        help="Image style (default: synthetic)")
    parser.add_argument("--gray-level", type=int, default=None,
                        help="Gray level 0-255 for gray style (default: vary by seed)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Starting random seed, incremented per file (default: random)")
    parser.add_argument("--shapes", type=int, default=120,
                        help="Number of shapes per image (default: 200)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seed = args.seed if args.seed is not None else random.randint(0, 2**32 - 1)
    print(f"Generating {args.count} file(s) in {args.output}/ (seed={seed})")
    generated = generate_files(
        output=args.output,
        count=args.count,
        width=args.width,
        height=args.height,
        extension=args.extension,
        style=args.style,
        gray_level=args.gray_level,
        seed=seed,
        shapes=args.shapes,
    )
    print(f"Done. {len(generated)} file(s) created.")


if __name__ == "__main__":
    main()
