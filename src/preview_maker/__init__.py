"""Preview Maker package.

The actual implementation lives in :mod:`preview_maker.core`.
This ``__init__`` re-exports the public API for convenience.
"""

from __future__ import annotations

from .core import convert_to_prv, generate_previews_for_sources, main

__all__ = ["convert_to_prv", "generate_previews_for_sources", "main"]

