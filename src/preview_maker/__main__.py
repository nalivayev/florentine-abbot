"""Module entry point for ``python -m preview_maker``.

This simply delegates to :func:`preview_maker.core.main`.
"""

from __future__ import annotations

from preview_maker.core import main


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
