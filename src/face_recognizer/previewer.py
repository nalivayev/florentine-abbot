"""Visualise detected face bounding boxes on a scaled-down preview image."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from common.logger import Logger
from face_recognizer.processor import RecognizerProcessor


def _pixel_bbox_from_region(
    region: tuple[float, float, float, float],
    image_size: tuple[int, int],
) -> tuple[int, int, int, int]:
    image_width, image_height = image_size
    center_x, center_y, width, height = region
    half_width = width / 2.0
    half_height = height / 2.0

    left = max(0.0, min(1.0, center_x - half_width))
    top = max(0.0, min(1.0, center_y - half_height))
    right = max(0.0, min(1.0, center_x + half_width))
    bottom = max(0.0, min(1.0, center_y + half_height))

    pixel_left = int(round(left * image_width))
    pixel_top = int(round(top * image_height))
    pixel_right = int(round(right * image_width))
    pixel_bottom = int(round(bottom * image_height))

    return (
        pixel_left,
        pixel_top,
        max(0, pixel_right - pixel_left),
        max(0, pixel_bottom - pixel_top),
    )


class RecognizerPreviewer:
    """Detect faces and draw bounding boxes on a downscaled preview image."""

    _BOX_COLOUR = (220, 30, 30)       # red
    _BOX_WIDTH   = 3                  # px (after scaling to preview)
    _LABEL_FILL  = (220, 30, 30, 180) # semi-transparent red
    _LABEL_TEXT  = (255, 255, 255)

    def __init__(
        self,
        logger: Logger,
        processor: RecognizerProcessor,
        *,
        max_size: int = 3000,
    ) -> None:
        self._logger = logger
        self._processor = processor
        self._max_size = max_size

    def preview(
        self,
        image_path: Path,
        output_path: Path | None = None,
    ) -> Path:
        """
        Detect faces in *image_path*, draw numbered bounding boxes, save and
        return the output path.

        Parameters
        ----------
        image_path:
            Source image (original, possibly very large).
        output_path:
            Destination JPEG.  Defaults to ``<stem>_detect.jpg`` next to
            the source file.

        Returns
        -------
        Path
            Path to the saved preview image.
        """
        faces = self._processor.process(image_path)
        if not faces:
            self._logger.warning(f"No faces detected in {image_path.name}")

        Image.MAX_IMAGE_PIXELS = None
        img = Image.open(image_path)
        img.load()

        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        orig_w, orig_h = img.size
        scale = 1.0

        if max(orig_w, orig_h) > self._max_size:
            scale = self._max_size / max(orig_w, orig_h)
            new_w = int(orig_w * scale)
            new_h = int(orig_h * scale)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            self._logger.debug(f"Downscaled {image_path.name} -> {new_w}x{new_h} (scale={scale:.4f})")

        if img.mode == "RGBA":
            img = img.convert("RGB")

        draw = ImageDraw.Draw(img, "RGBA")
        box_w = self._BOX_WIDTH
        font = self._load_font(size=max(14, int(18 * scale)))

        for i, face in enumerate(faces):
            x, y, w, h = _pixel_bbox_from_region(face.region, img.size)

            pw, ph = img.size
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(pw, x + w), min(ph, y + h)

            draw.rectangle([x1, y1, x2, y2], outline=self._BOX_COLOUR, width=box_w)

            conf_str = f" {face.confidence:.2f}" if face.confidence is not None else ""
            text = f"#{i + 1}{conf_str}"

            try:
                bbox_text = font.getbbox(text)
                tw = bbox_text[2] - bbox_text[0]
                th = bbox_text[3] - bbox_text[1]
            except AttributeError:
                tw, th = len(text) * 7, 14

            tx = x1
            ty = max(0, y1 - th - 4)
            draw.rectangle([tx, ty, tx + tw + 6, ty + th + 4], fill=self._LABEL_FILL)
            draw.text((tx + 3, ty + 2), text, fill=self._LABEL_TEXT, font=font)

        if output_path is None:
            output_path = image_path.parent / (image_path.stem + "_detect.jpg")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, format="JPEG", quality=90)

        self._logger.info(f"Saved preview with {len(faces)} face(s) -> {output_path}")
        return output_path

    def __call__(self, image_path: Path, output_path: Path | None = None) -> Path:
        """Backward-compatible wrapper around :meth:`preview`."""
        return self.preview(image_path, output_path)

    @staticmethod
    def _load_font(size: int = 14) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
        """Try to load a system TrueType font; fall back to PIL default."""
        candidates = [
            # Windows
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            # macOS
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        for path in candidates:
            try:
                return ImageFont.truetype(path, size)
            except (IOError, OSError):
                continue
        return ImageFont.load_default()
