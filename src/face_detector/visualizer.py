"""
Visualise detected face bounding boxes on a scaled-down preview image.

Reads bounding boxes from the :class:`FaceStore` database and draws them onto
a JPEG preview of the source image.  The original file is never modified.

Typical usage::

    viz = FaceVisualizer(logger, max_size=3000)
    out = viz.draw(
        image_path=Path("D:/1925/1925.04.00.00.00.00.C.001.001.0001.A.RAW.tif"),
        store=store,
        output_path=Path("preview_faces.jpg"),
    )
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from common.logger import Logger
from face_detector.store import FaceStore


class FaceVisualizer:
    """Draw face bounding boxes on a downscaled preview image."""
    
    _BOX_COLOUR = (220, 30, 30)       # red
    _BOX_WIDTH   = 3                  # px (after scaling to preview)
    _LABEL_FILL  = (220, 30, 30, 180) # semi-transparent red
    _LABEL_TEXT  = (255, 255, 255)

    def __init__(self, logger: Logger, *, max_size: int = 3000) -> None:
        self._logger = logger
        self._max_size = max_size

    def draw(
        self,
        image_path: Path,
        store: FaceStore,
        output_path: Path | None = None,
    ) -> Path:
        """
        Load *image_path*, draw bounding boxes for all faces stored in
        *store*, save the result and return its path.

        Parameters
        ----------
        image_path:
            Source image (original, possibly very large).
        store:
            Open :class:`FaceStore` — used to look up face records.
        output_path:
            Destination JPEG.  Defaults to ``<stem>_faces.jpg`` next to
            the source file.

        Returns
        -------
        Path
            Path to the saved preview image.
        """
        faces = store.get_faces_by_file(image_path)
        if not faces:
            self._logger.warning(f"No face records found for {image_path.name} in the database")

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
            self._logger.debug(f"Downscaled {image_path.name} → {new_w}x{new_h} (scale={scale:.4f})")

        if img.mode == "RGBA":
            img = img.convert("RGB")

        draw = ImageDraw.Draw(img, "RGBA")
        box_w = max(2, int(self._BOX_WIDTH / scale * scale))  # stay reasonable

        font = self._load_font(size=max(14, int(18 * scale)))

        for face in faces:
            # Scale bbox from original → preview coords
            x = int(face.bbox_x * scale)
            y = int(face.bbox_y * scale)
            w = int(face.bbox_w * scale)
            h = int(face.bbox_h * scale)

            # Clamp to image bounds
            pw, ph = img.size
            x1, y1 = max(0, x), max(0, y)
            x2, y2 = min(pw, x + w), min(ph, y + h)

            draw.rectangle([x1, y1, x2, y2], outline=self._BOX_COLOUR, width=box_w)

            # Label: person name > cluster id > face id
            if face.person and face.person.name:
                label = face.person.name
            elif face.cluster is not None:
                label = f"cluster-{face.cluster}"
            else:
                label = f"#{face.id}"

            conf_str = f" {face.confidence:.2f}" if face.confidence is not None else ""
            text = f"{label}{conf_str}"

            # Draw small label background + text
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
            output_path = image_path.parent / (image_path.stem + "_faces.jpg")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, format="JPEG", quality=90)

        self._logger.info(f"Saved preview with {len(faces)} face(s) → {output_path}")
        return output_path

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
