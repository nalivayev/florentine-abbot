"""InsightFace detector plugin.

Uses the ``buffalo_l`` model pack by default, which bundles:

* **RetinaFace** — face detection
* **ArcFace R100** — 512-dim face embeddings

Requires ``insightface`` and ``onnxruntime`` (or ``onnxruntime-gpu``).
Install via the ``face-insightface`` extra::

    pip install "florentine-abbot[face-insightface]"
"""

from pathlib import Path

import numpy as np
from PIL import Image

from common.logger import Logger
from face_detector.config import Config
from face_detector.detector import DetectedFace, FaceDetector
from face_detector.detectors import register_detector

try:
    from insightface.app import FaceAnalysis as _FaceAnalysis  # type: ignore[import-untyped]
except ImportError:
    _FaceAnalysis = None  # type: ignore[assignment]

# Maximum long edge (pixels) fed to the detector.
# Archival scans can be 500 MP+; detection doesn't need that resolution.
_DETECTION_MAX_SIZE = 4000


@register_detector("insightface")
class InsightFaceDetector(FaceDetector):
    """Face detector backed by InsightFace (insightface + onnxruntime).

    The ONNX runtime automatically selects a CUDA device when available
    and falls back to CPU otherwise.  Model weights are downloaded to
    ``~/.insightface/`` on first use.
    """

    def __init__(self, logger: Logger, config: Config) -> None:
        self._logger = logger
        self._config = config
        self._app: object | None = None  # lazy: initialised on first detect()

    def _ensure_app(self) -> None:
        if _FaceAnalysis is None:
            raise RuntimeError(
                "insightface is required for face detection. "
                "Install it with: pip install insightface onnxruntime"
            )
        if self._app is None:
            det_size = self._config.insightface_det_size
            app = _FaceAnalysis(
                name=self._config.insightface_model_pack,
                providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
            )
            app.prepare(ctx_id=0, det_size=(det_size, det_size))
            self._app = app

    def should_process(self, file_path: Path) -> bool:
        if file_path.is_symlink():
            self._logger.debug(f"Skipping {file_path}: is symlink")
            return False

        if file_path.suffix.lower() not in self._config.source_extensions:
            self._logger.debug(
                f"Skipping {file_path}: extension {file_path.suffix!r} not in source_extensions"
            )
            return False

        upper_name = file_path.name.upper()
        allowed_suffixes = self._config.source_suffixes
        if allowed_suffixes and not any(f".{s}." in upper_name for s in allowed_suffixes):
            self._logger.debug(
                f"Skipping {file_path}: no matching source suffix in {allowed_suffixes}"
            )
            return False

        return True

    def detect(self, image_path: Path) -> list[DetectedFace]:
        """Detect faces and extract embeddings from *image_path*.

        Archival scans are transparently downscaled to
        ``_DETECTION_MAX_SIZE`` px; bounding boxes are mapped back to
        the original pixel coordinates before returning.

        Returns a (possibly empty) list of :class:`DetectedFace`.
        Raises ``RuntimeError`` if insightface is not installed.
        """
        self._ensure_app()

        self._logger.debug(
            f"Detecting faces in {image_path} (model={self._config.insightface_model_pack}, det_size={self._config.insightface_det_size})"
        )

        Image.MAX_IMAGE_PIXELS = None  # allow large archival scans
        try:
            pil_img = Image.open(image_path)
            pil_img.load()
        except Exception as exc:
            self._logger.warning(f"Cannot open {image_path}: {exc}")
            return []

        orig_w, orig_h = pil_img.size
        scale = 1.0

        if max(orig_w, orig_h) > _DETECTION_MAX_SIZE:
            scale = _DETECTION_MAX_SIZE / max(orig_w, orig_h)
            new_w = int(orig_w * scale)
            new_h = int(orig_h * scale)
            self._logger.debug(
                f"Downscaling {image_path.name} from {orig_w}x{orig_h} to {new_w}x{new_h} (scale={scale:.4f})"
            )
            pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")

        # insightface expects a BGR numpy array (OpenCV convention)
        img_bgr = np.array(pil_img)[:, :, ::-1]

        try:
            raw_faces = self._app.get(img_bgr)  # type: ignore[union-attr]
        except Exception as exc:
            self._logger.warning(f"InsightFace failed on {image_path}: {exc}")
            return []

        inv = 1.0 / scale if scale != 1.0 else 1.0
        faces: list[DetectedFace] = []

        for f in raw_faces:
            # bbox from insightface: [x1, y1, x2, y2] float array
            x1, y1, x2, y2 = (float(v) * inv for v in f.bbox)
            bbox = (int(x1), int(y1), int(x2 - x1), int(y2 - y1))

            emb = np.array(f.embedding, dtype=np.float32)
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm  # L2-normalise for cosine similarity

            confidence: float | None = float(f.det_score) if hasattr(f, "det_score") else None

            faces.append(DetectedFace(
                bbox=bbox,
                confidence=confidence,
                embedding=emb,
            ))

        self._logger.info(
            f"Found {len(faces)} face(s) in {image_path.name} (orig {orig_w}x{orig_h}, scale={scale:.4f})"
        )
        return faces
