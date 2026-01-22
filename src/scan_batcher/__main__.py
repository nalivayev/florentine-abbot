"""Module entry point for ``python -m scan_batcher``.

This simply delegates to :func:`scan_batcher.cli.main`.
"""

from scan_batcher.cli import main


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
