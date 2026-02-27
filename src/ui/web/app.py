"""
Florentine Abbot — web dashboard.

Start the development server directly::

    python -m ui.web.app

Or via the installed entry point::

    florentine-web [--host HOST] [--port PORT]
"""

import argparse
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from ui.web import routes

_HERE = Path(__file__).parent


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Florentine Abbot", docs_url=None, redoc_url=None)
    app.mount("/static", StaticFiles(directory=_HERE / "static"), name="static")
    app.include_router(routes.router)
    return app


app = create_app()


def main(argv: list[str] | None = None) -> None:
    """Entry point for the ``florentine-web`` CLI."""
    parser = argparse.ArgumentParser(description="Florentine Abbot web dashboard")
    parser.add_argument("--host", default="127.0.0.1", metavar="HOST",
                        help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, metavar="PORT",
                        help="Bind port (default: 8000)")
    args = parser.parse_args(argv)

    uvicorn.run("ui.web.app:app", host=args.host, port=args.port)


if __name__ == "__main__":  # pragma: no cover
    main()
