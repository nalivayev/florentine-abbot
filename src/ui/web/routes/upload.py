"""
Import routes — file upload to inbox.
"""

from pathlib import Path
from typing import Any
from urllib.parse import unquote

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from common.config_utils import read_daemon_config
from ui.web.deps import require_admin

router = APIRouter()


def _get_inbox() -> Path:
    fo = read_daemon_config("file-organizer")
    inbox = fo.get("watch", {}).get("path", "").strip()
    if not inbox:
        raise HTTPException(status_code=409, detail="inbox_not_configured")
    path = Path(inbox)
    if not path.exists():
        raise HTTPException(status_code=409, detail="inbox_not_found")
    return path


@router.post("/import/upload")
async def import_upload(
    request: Request,
    x_filename: str = Header(...),
    _user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    inbox = _get_inbox()
    staging = inbox / "staging"
    staging.mkdir(exist_ok=True)

    filename = Path(unquote(x_filename)).name
    stage_path = staging / filename
    dest_path = inbox / filename

    try:
        with stage_path.open("wb") as f:
            async for chunk in request.stream():
                f.write(chunk)
        stage_path.replace(dest_path)
    except Exception as exc:
        stage_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"filename": filename, "path": str(dest_path.resolve()), "ok": True}
