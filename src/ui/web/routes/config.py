"""
Config routes — project paths.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.config_utils import read_daemon_config, write_daemon_config
from ui.web.daemon_manager import manager
from ui.web.deps import get_current_user, require_admin

router = APIRouter()


class InboxSettings(BaseModel):
    inbox: str


class ArchiveSettings(BaseModel):
    archive: str


@router.get("/config")
async def config_get(user: dict = Depends(get_current_user)) -> dict:
    fo = read_daemon_config("file-organizer")
    watch = fo.get("watch", {})
    return {
        "archive": watch.get("output", ""),
        "inbox": watch.get("path", ""),
    }


@router.post("/config/inbox")
async def config_save_inbox(settings: InboxSettings, user: dict = Depends(require_admin)) -> dict:
    inbox = settings.inbox.strip()
    if not inbox:
        raise HTTPException(status_code=422, detail="required")

    fo = read_daemon_config("file-organizer")
    fo.setdefault("watch", {})["path"] = inbox
    write_daemon_config("file-organizer", fo)

    try:
        manager.stop("file-organizer")
        manager.start("file-organizer")
    except Exception:
        pass

    return {"ok": True}


@router.post("/config/archive")
async def config_save_archive(settings: ArchiveSettings, user: dict = Depends(require_admin)) -> dict:
    archive = settings.archive.strip()
    if not archive:
        raise HTTPException(status_code=422, detail="required")

    fo = read_daemon_config("file-organizer")
    fo.setdefault("watch", {})["output"] = archive
    write_daemon_config("file-organizer", fo)

    pm = read_daemon_config("preview-maker")
    pm.setdefault("watch", {})["path"] = archive
    write_daemon_config("preview-maker", pm)

    for name in ("file-organizer", "preview-maker"):
        try:
            manager.stop(name)
            manager.start(name)
        except Exception:
            pass

    return {"ok": True}
