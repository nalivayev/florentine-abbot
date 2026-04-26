"""InsightFace detector plugin.

Uses the ``buffalo_l`` model pack by default, which bundles:

* **RetinaFace** - face localization
* **ArcFace R100** - 512-dim face embeddings

Requires ``insightface`` and ``onnxruntime`` (or ``onnxruntime-gpu``).
Install via the ``face-insightface`` extra::

    pip install "florentine-abbot[face-insightface]"
"""

from pathlib import Path
from typing import cast

import numpy
from PIL import Image

from common.config_utils import ensure_config_exists, get_config_dir, get_template_path, load_optional_config
from common.logger import Logger
from face_recognizer.classes import DetectedFace
from face_recognizer.detector import FaceDetector, detector

try:
    from insightface.app import FaceAnalysis as _FaceAnalysis  # type: ignore[import-untyped]
except ImportError:
    _FaceAnalysis = None  # type: ignore[assignment]

@detector("insightface")
class InsightFaceDetector(FaceDetector):
    """Face detector backed by InsightFace (insightface + onnxruntime).

    The ONNX runtime automatically selects a CUDA device when available
    and falls back to CPU otherwise. Model weights are downloaded to
    ``~/.insightface/`` on first use.
    """

    def __init__(self, logger: Logger) -> None:
        self._logger = logger
        self._app: object | None = None  # lazy: initialised on first detect()

        config_path = (
            get_config_dir() / "face-recognizer" / "detectors" / "insightface" / "config.json"
        )
        template_path = get_template_path(
            "face_recognizer.detectors.insightface",
            "config.template.json",
        )
        ensure_config_exists(self._logger, config_path, {}, template_path)
        opts = load_optional_config(self._logger, config_path, {})

        self._model_pack: str = str(opts.get("model_pack", "buffalo_l"))
        self._det_size: int = int(opts.get("det_size", 640))

    def _ensure_app(self) -> None:
        if _FaceAnalysis is None:
            raise RuntimeError(
                "insightface is required for face detection. "
                "Install it with: pip install insightface onnxruntime"
            )
        if self._app is None:
            det_size = self._det_size
            app = _FaceAnalysis(
                name=self._model_pack,
                providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
            )
            app.prepare(ctx_id=0, det_size=(det_size, det_size))  # type: ignore[union-attr]
            self._app = app

    def detect(self, image_path: Path) -> list[DetectedFace]:
        """Detect faces and extract embeddings from *image_path*.

        The caller is expected to pass a detector-ready image path.
        Oversized archive masters are reduced earlier by
        :class:`face_recognizer.processor.RecognizerProcessor`.

        Returns a (possibly empty) list of :class:`DetectedFace`.
        Raises ``RuntimeError`` if insightface is not installed.
        """
        self._ensure_app()

        self._logger.debug(
            f"Detecting faces in {image_path} (model={self._model_pack}, det_size={self._det_size})"
        )

        Image.MAX_IMAGE_PIXELS = None  # allow large archival scans
        try:
            pil_img = Image.open(image_path)
            pil_img.load()
        except Exception as exc:
            self._logger.warning(f"Cannot open {image_path}: {exc}")
            return []

        view_w, view_h = pil_img.size

        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")

        # insightface expects a BGR numpy array (OpenCV convention)
        img_bgr = numpy.array(pil_img)[:, :, ::-1]

        try:
            raw_faces = self._app.get(img_bgr)  # type: ignore[union-attr]
        except Exception as exc:
            self._logger.warning(f"InsightFace failed on {image_path}: {exc}")
            return []

        faces: list[DetectedFace] = []

        for face in raw_faces:  # type: ignore[union-attr]
            x1, y1, x2, y2 = [float(value) for value in face.bbox]  # type: ignore[union-attr]
            bbox = (int(x1), int(y1), int(x2 - x1), int(y2 - y1))

            embedding = numpy.array(face.embedding, dtype=numpy.float32)  # type: ignore[union-attr]
            norm = numpy.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

            det_score = getattr(cast(object, face), "det_score", None)
            confidence: float | None = float(det_score) if det_score is not None else None

            faces.append(
                DetectedFace(
                    bbox=bbox,
                    confidence=confidence,
                    embedding=embedding,
                )
            )

        self._logger.info(
            f"Found {len(faces)} face(s) in {image_path.name} ({view_w}x{view_h})"
        )
        return faces
