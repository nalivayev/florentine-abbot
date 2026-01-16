"""Module entry point for ``python -m preview_maker``.

This simply delegates to :func:`preview_maker.cli.main`.
"""

from preview_maker.cli import main


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
