"""Archive task provider declaration for Preview Maker."""

from common.provider import ArchiveProvider, provider
from preview_maker.constants import DAEMON_NAME


@provider(DAEMON_NAME)
class MakerProvider(ArchiveProvider):
    """Registers preview-maker as an archive task provider."""
