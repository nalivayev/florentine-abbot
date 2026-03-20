"""
Florentine Abbot — web dashboard.

Start the development server directly::

    python -m ui.web.app

Or via the installed entry point::

    florentine-web [--host HOST] [--port PORT]
"""

import argparse
import json
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from common.config_utils import get_config_dir
from common.db import init_db
from ui.web.routes import router as api_router

_HERE = Path(__file__).parent
_DIST = _HERE / "frontend" / "dist"


def _try_init_db() -> None:
    """Init DB from file-organizer config if archive path is already set."""
    try:
        config_path = get_config_dir() / "file-organizer" / "config.json"
        if config_path.exists():
            data = json.loads(config_path.read_text(encoding="utf-8"))
            archive = data.get("watch", {}).get("output", "").strip()
            if archive and Path(archive).exists():
                init_db(archive)
    except Exception:
        pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    _try_init_db()
    app = FastAPI(title="Florentine Abbot", docs_url=None, redoc_url=None)
    app.include_router(api_router)

    @app.get("/favicon.ico")
    async def favicon() -> Response:
        return Response(status_code=204)

    if _DIST.exists():
        app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

        @app.get("/{full_path:path}")
        async def spa(full_path: str) -> FileResponse:
            return FileResponse(_DIST / "index.html")

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
