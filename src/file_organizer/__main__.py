"""Module entry point for ``python -m file_organizer``.

This simply delegates to :func:`file_organizer.cli.main`.
"""

from file_organizer.cli import main


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
