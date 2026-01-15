"""Command Line Interface for Preview Maker.

Thin wrapper around :func:`preview_maker.core.main` used by the
``preview-maker`` console script.
"""

from __future__ import annotations

from preview_maker.core import main as _main


def main() -> None:
    """Entry point for the `preview-maker` CLI."""

    _main()


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    main()
