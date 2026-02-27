"""Face Detector package.

Public API for face detection, embedding extraction and identity clustering.

Detector plugins are loaded automatically from the ``face_detector.detectors``
entry-points group.  Use :func:`face_detector.detectors.get_detector` to
look up a registered detector by name.
"""

from face_detector.config import Config
from face_detector.detector import DetectedFace, FaceDetector
from face_detector.detectors import get_detector, load_detectors, register_detector
from face_detector.store import FaceStore
from face_detector.clusterer import FaceClusterer
from face_detector.engine import FaceDetectorEngine
from face_detector.visualizer import FaceVisualizer

__all__ = [
    "Config",
    "FaceDetector",
    "DetectedFace",
    "register_detector",
    "get_detector",
    "load_detectors",
    "FaceStore",
    "FaceClusterer",
    "FaceDetectorEngine",
    "FaceVisualizer",
]
