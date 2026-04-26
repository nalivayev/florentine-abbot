"""Archive task provider declaration for Tile Cutter."""

from common.provider import ArchiveProvider, provider
from tile_cutter.constants import DAEMON_NAME


@provider(DAEMON_NAME)
class CutterProvider(ArchiveProvider):
    """Registers tile-cutter as an archive task provider."""
