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
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from common.config_utils import get_archive_path
from common.constants import ARCHIVE_SYSTEM_DIR
from ui.web.routes import router as api_router
from ui.web.setup_store import SetupStore

_HERE = Path(__file__).parent
_DIST = _HERE / "frontend" / "dist"


def _try_init_db() -> None:
    """Ensure the archive DB exists when global config already provides a path."""
    try:
        archive = get_archive_path()
        if archive and archive.exists():
            SetupStore(archive).ensure_ready()
    except Exception:
        pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Florentine Abbot", docs_url=None, redoc_url=None)
    _try_init_db()
    app.include_router(api_router)

    @app.get("/favicon.ico")
    async def favicon() -> Response:
        return Response(status_code=204)

    @app.get("/system/{full_path:path}")
    async def system_file(full_path: str) -> FileResponse:
        archive = get_archive_path()
        if archive is None:
            raise HTTPException(status_code=404)

        system_dir = (archive / ARCHIVE_SYSTEM_DIR).resolve()
        target = (system_dir / full_path).resolve()

        try:
            target.relative_to(system_dir)
        except ValueError as exc:
            raise HTTPException(status_code=404) from exc

        if not target.is_file():
            raise HTTPException(status_code=404)

        return FileResponse(target)

    if _DIST.exists():
        app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

        @app.get("/{full_path:path}")
        async def spa(full_path: str) -> FileResponse:
            if full_path.startswith("setup"):
                return FileResponse(_DIST / "setup.html")
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
