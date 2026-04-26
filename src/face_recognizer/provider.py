"""Archive task provider declaration for Face Recognizer."""

from common.provider import ArchiveProvider, provider
from face_recognizer.constants import DAEMON_NAME


@provider(DAEMON_NAME)
class RecognizerProvider(ArchiveProvider):
    """Registers face-recognizer as an archive task provider."""
