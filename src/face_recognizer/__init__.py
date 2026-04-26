"""Face Recognizer package.

Public API for face detection, embedding extraction and identity clustering.
"""

from face_recognizer.classes import DetectedFace, RecognizerSettings
from face_recognizer.clusterer import RecognizerClusterer
from face_recognizer.detector import FaceDetector
from face_recognizer.recognizer import Recognizer
from face_recognizer.previewer import RecognizerPreviewer
from face_recognizer.processor import RecognizerProcessor
from face_recognizer.store import RecognizerStore
from face_recognizer.watcher import RecognizerWatcher

__all__ = [
	"RecognizerSettings",
	"FaceDetector",
	"DetectedFace",
	"RecognizerStore",
	"RecognizerClusterer",
	"Recognizer",
	"RecognizerProcessor",
	"RecognizerPreviewer",
	"RecognizerWatcher",
]
