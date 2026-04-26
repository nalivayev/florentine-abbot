"""
Setup routes — first-run initialization wizard.
"""

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.auth import hash_password
from common.config_utils import (
    get_archive_path,
    get_config_dir,
    read_daemon_config,
    remove_daemon_archive_settings,
    write_daemon_config,
)
from common.constants import DEFAULT_ARCHIVE_FILENAME_TEMPLATE, DEFAULT_ARCHIVE_PATH_TEMPLATE
from ui.web.deps import require_localhost
from ui.web.setup_store import SetupStore
from ui.web.store import WebStore

router = APIRouter()


def _save_format(archive_path_template: str, archive_filename_template: str) -> None:
    """Persist archive format templates to common config.json."""
    config_path = get_config_dir() / "config.json"
    try:
        data: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    except Exception:
        data = {}

    formats_value = data.get("formats")
    formats: dict[str, Any] = cast(dict[str, Any], formats_value) if isinstance(formats_value, dict) else {}
    formats["archive_path_template"] = archive_path_template
    formats["archive_filename_template"] = archive_filename_template
    data["formats"] = formats

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@router.get("/setup/check-exiftool", dependencies=[Depends(require_localhost)])
async def check_exiftool() -> dict[str, bool | str | None]:
    """Check whether ExifTool is actually runnable and return its version."""
    try:
        result = subprocess.run(
            ["exiftool", "-ver"], capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return {"installed": True, "version": result.stdout.strip()}
        return {"installed": False, "version": None}
    except Exception:
        return {"installed": False, "version": None}


@router.get("/setup/format", dependencies=[Depends(require_localhost)])
async def setup_format() -> dict[str, str]:
    """Return current (or default) archive format templates."""
    config_path = get_config_dir() / "config.json"
    try:
        data: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
        formats_value = data.get("formats")
        formats: dict[str, Any] = cast(dict[str, Any], formats_value) if isinstance(formats_value, dict) else {}
    except Exception:
        formats = {}
    return {
        "archive_path_template": formats.get("archive_path_template", DEFAULT_ARCHIVE_PATH_TEMPLATE),
        "archive_filename_template": formats.get("archive_filename_template", DEFAULT_ARCHIVE_FILENAME_TEMPLATE),
    }


class SetupRequest(BaseModel):
    archive_path: str
    username: str
    password: str
    archive_path_template: str = DEFAULT_ARCHIVE_PATH_TEMPLATE
    archive_filename_template: str = DEFAULT_ARCHIVE_FILENAME_TEMPLATE


class ValidateRequest(BaseModel):
    step: int
    archive_path: str = ""
    username: str = ""
    password: str = ""
    password2: str = ""


@router.post("/setup/validate", dependencies=[Depends(require_localhost)])
async def setup_validate(req: ValidateRequest) -> dict[str, dict[str, str]]:
    """Validate wizard fields for a given step. Returns {fields: {field: error_code}}."""
    errors: dict[str, str] = {}

    if req.step == 3:
        if not req.archive_path.strip():
            errors["archive_path"] = "required"
        if not req.username.strip():
            errors["username"] = "required"
        elif not re.match(r"^\w{3,}$", req.username.strip()):
            errors["username"] = "username_format"
        if not req.password:
            errors["password"] = "required"
        elif len(req.password) < 6:
            errors["password"] = "password_short"
        if not req.password2:
            errors["password2"] = "required"
        elif req.password != req.password2:
            errors["password2"] = "passwords_mismatch"

    return {"fields": errors}


@router.get("/setup/status")
async def setup_status() -> dict[str, bool]:
    archive_path = get_archive_path()
    initialized = False if archive_path is None else SetupStore(archive_path).has_any_users()
    return {"initialized": initialized}


@router.post("/setup", dependencies=[Depends(require_localhost)])
async def setup(req: SetupRequest) -> dict[str, bool]:
    configured_archive_path = get_archive_path()
    if configured_archive_path is not None and SetupStore(configured_archive_path).has_any_users():
        raise HTTPException(status_code=409, detail="Already initialized")

    archive_path = req.archive_path.strip()
    username = req.username.strip()
    password = req.password
    inbox = str(Path(archive_path) / ".inbox")

    if not archive_path or not username or not password:
        raise HTTPException(status_code=422, detail="All fields are required")

    archive_root = Path(archive_path)
    archive_root.mkdir(parents=True, exist_ok=True)
    Path(inbox).mkdir(parents=True, exist_ok=True)

    setup_store = SetupStore(archive_root)
    if setup_store.has_any_users():
        raise HTTPException(status_code=409, detail="Already initialized")

    setup_store.ensure_ready()

    with WebStore(archive_root) as store:
        now = datetime.now(timezone.utc).isoformat()
        admin_role_id = store.get_role_id("admin")
        if admin_role_id is None:
            raise HTTPException(status_code=500, detail="Admin role missing")
        store.create_user(
            username=username,
            password_hash=hash_password(password),
            role_id=admin_role_id,
            created_at=now,
        )

    fo = read_daemon_config("file-organizer")
    fo.setdefault("watch", {})
    fo["watch"]["path"] = inbox
    fo["watch"].pop("output", None)
    write_daemon_config("file-organizer", fo)

    remove_daemon_archive_settings()

    _save_format(req.archive_path_template, req.archive_filename_template)

    # Save archive path to global config
    global_config_path = get_config_dir() / "config.json"
    try:
        global_data: dict[str, Any] = json.loads(global_config_path.read_text(encoding="utf-8")) if global_config_path.exists() else {}
    except Exception:
        global_data = {}
    global_data["archive_path"] = archive_path
    global_config_path.write_text(json.dumps(global_data, indent=2, ensure_ascii=False), encoding="utf-8")

    from ui.web.daemon_manager import manager
    for name in ("preview-maker", "tile-cutter"):
        try:
            manager.start(name)
        except Exception:
            pass  # daemon start failure is non-fatal for setup

    return {"ok": True}
