"""
Config routes — project paths.
"""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.config_utils import get_archive_path, get_config_dir, read_daemon_config, read_metadata_config, remove_daemon_archive_settings, write_daemon_config, write_metadata_config
from common.constants import DEFAULT_ARCHIVE_PATH_TEMPLATE, DEFAULT_ARCHIVE_FILENAME_TEMPLATE
from ui.web.daemon_manager import manager
from ui.web.deps import get_current_user, require_admin
from ui.web.setup_store import SetupStore

router = APIRouter()


class FormatSettings(BaseModel):
    archive_path_template: str
    archive_filename_template: str


class InboxSettings(BaseModel):
    inbox: str


class ArchiveSettings(BaseModel):
    archive_path: str


class MetadataSettings(BaseModel):
    languages: dict[str, dict[str, Any]]


@router.get("/config/format")
async def config_format_get(_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, str]:
    config_path = get_config_dir() / "config.json"
    try:
        data: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
        formats: dict[str, Any] = data.get("formats", {})
    except Exception:
        formats = {}
    return {
        "archive_path_template": formats.get("archive_path_template", DEFAULT_ARCHIVE_PATH_TEMPLATE),
        "archive_filename_template": formats.get("archive_filename_template", DEFAULT_ARCHIVE_FILENAME_TEMPLATE),
    }


@router.post("/config/format")
async def config_format_save(settings: FormatSettings, _user: dict[str, Any] = Depends(require_admin)) -> dict[str, bool]:
    config_path = get_config_dir() / "config.json"
    try:
        data: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    except Exception:
        data = {}
    data.setdefault("formats", {})["archive_path_template"] = settings.archive_path_template
    data["formats"]["archive_filename_template"] = settings.archive_filename_template
    config_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"ok": True}


@router.get("/config/metadata")
async def config_metadata_get(_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    data = read_metadata_config()
    return {
        "languages": data.get("languages", {}),
    }


@router.post("/config/metadata")
async def config_metadata_save(
    settings: MetadataSettings,
    _user: dict[str, Any] = Depends(require_admin),
) -> dict[str, bool]:
    data = read_metadata_config()
    data["languages"] = settings.languages
    write_metadata_config(data)
    return {"ok": True}


@router.get("/config")
async def config_get(_user: dict[str, Any] = Depends(require_admin)) -> dict[str, str]:
    fo = read_daemon_config("file-organizer")
    watch: dict[str, Any] = fo.get("watch", {})
    archive_path = get_archive_path()
    return {
        "archive_path": str(archive_path) if archive_path is not None else "",
        "inbox": watch.get("path", ""),
    }


@router.post("/config/inbox")
async def config_save_inbox(settings: InboxSettings, _user: dict[str, Any] = Depends(require_admin)) -> dict[str, bool]:
    inbox = settings.inbox.strip()
    if not inbox:
        raise HTTPException(status_code=422, detail="required")

    fo = read_daemon_config("file-organizer")
    watch = fo.setdefault("watch", {})
    watch["path"] = inbox
    watch.pop("output", None)
    write_daemon_config("file-organizer", fo)

    try:
        manager.stop("file-organizer")
        manager.start("file-organizer")
    except Exception:
        pass

    return {"ok": True}


@router.post("/config/archive-path")
async def config_save_archive(
    settings: ArchiveSettings,
    _user: dict[str, Any] = Depends(require_admin),
) -> dict[str, bool]:
    archive_path = settings.archive_path.strip()
    if not archive_path:
        raise HTTPException(status_code=422, detail="required")

    config_path = get_config_dir() / "config.json"
    try:
        data: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    except Exception:
        data = {}
    data["archive_path"] = archive_path
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    remove_daemon_archive_settings()
    SetupStore(archive_path).ensure_ready()

    for name in ("preview-maker", "tile-cutter", "archive-keeper"):
        try:
            manager.stop(name)
            manager.start(name)
        except Exception:
            pass

    return {"ok": True}
