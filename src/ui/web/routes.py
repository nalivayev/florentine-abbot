"""
HTTP route handlers for the Florentine Abbot web dashboard.
"""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from ui.web.daemon_manager import manager

_HERE = Path(__file__).parent

templates = Jinja2Templates(directory=_HERE / "templates")
router = APIRouter()


@router.get("/favicon.ico")
async def favicon() -> Response:
    return Response(status_code=204)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "daemons": manager.all()},
    )


@router.get("/api/daemons", response_class=HTMLResponse)
async def daemons_fragment(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "_daemons.html",
        {"request": request, "daemons": manager.all()},
    )


@router.post("/api/daemons/{name}/start", response_class=HTMLResponse)
async def daemon_start(name: str, request: Request) -> HTMLResponse:
    manager.start(name)
    return templates.TemplateResponse(
        "_daemons.html",
        {"request": request, "daemons": manager.all()},
    )


@router.post("/api/daemons/{name}/stop", response_class=HTMLResponse)
async def daemon_stop(name: str, request: Request) -> HTMLResponse:
    manager.stop(name)
    return templates.TemplateResponse(
        "_daemons.html",
        {"request": request, "daemons": manager.all()},
    )
