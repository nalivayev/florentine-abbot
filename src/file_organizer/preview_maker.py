"""Compatibility shim for the Preview Maker.

The implementation has moved to the top-level :mod:`preview_maker` package.
This module is kept so that imports like::

    from file_organizer.preview_maker import generate_previews_for_sources

continue to work, as well as the older invocation::

    python -m file_organizer.preview_maker ...
"""

from __future__ import annotations

from preview_maker import convert_to_prv, generate_previews_for_sources, main

__all__ = [
    "convert_to_prv",
    "generate_previews_for_sources",
    "main",
]


if __name__ == "__main__":  # pragma: no cover - legacy CLI entry
    raise SystemExit(main())
