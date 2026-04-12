"""
Config routes — project paths.
"""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.config_utils import read_daemon_config, write_daemon_config, get_config_dir
from common.constants import DEFAULT_ARCHIVE_PATH_TEMPLATE, DEFAULT_ARCHIVE_FILENAME_TEMPLATE
from ui.web.daemon_manager import manager
from ui.web.deps import get_current_user, require_admin

router = APIRouter()


class FormatSettings(BaseModel):
    archive_path_template: str
    archive_filename_template: str


class InboxSettings(BaseModel):
    inbox: str


class ArchiveSettings(BaseModel):
    archive: str


@router.get("/config/format")
async def config_format_get(user: dict = Depends(get_current_user)) -> dict:
    config_path = get_config_dir() / "config.json"
    try:
        data = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
        formats = data.get("formats", {})
    except Exception:
        formats = {}
    return {
        "archive_path_template": formats.get("archive_path_template", DEFAULT_ARCHIVE_PATH_TEMPLATE),
        "archive_filename_template": formats.get("archive_filename_template", DEFAULT_ARCHIVE_FILENAME_TEMPLATE),
    }


@router.post("/config/format")
async def config_format_save(settings: FormatSettings, user: dict = Depends(require_admin)) -> dict:
    config_path = get_config_dir() / "config.json"
    try:
        data = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    except Exception:
        data = {}
    data.setdefault("formats", {})["archive_path_template"] = settings.archive_path_template
    data["formats"]["archive_filename_template"] = settings.archive_filename_template
    config_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"ok": True}


@router.get("/config")
async def config_get(user: dict = Depends(require_admin)) -> dict:
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
