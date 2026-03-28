"""
Setup routes — first-run initialization wizard.
"""

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.auth import hash_password
from common.config_utils import get_config_dir, read_daemon_config, write_daemon_config
from common.constants import DEFAULT_ARCHIVE_PATH_TEMPLATE, DEFAULT_ARCHIVE_FILENAME_TEMPLATE
from common.db import get_conn, init_db, is_initialized
from ui.web.deps import require_localhost

router = APIRouter()


def _save_format(archive_path_template: str, archive_filename_template: str) -> None:
    """Persist archive format templates to common config.json."""
    config_path = get_config_dir() / "config.json"
    try:
        data = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    except Exception:
        data = {}
    data.setdefault("formats", {})["archive_path_template"] = archive_path_template
    data["formats"]["archive_filename_template"] = archive_filename_template
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@router.get("/setup/check-exiftool", dependencies=[Depends(require_localhost)])
async def check_exiftool() -> dict:
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
async def setup_format() -> dict:
    """Return current (or default) archive format templates."""
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


class SetupRequest(BaseModel):
    archive: str
    username: str
    password: str
    archive_path_template: str = DEFAULT_ARCHIVE_PATH_TEMPLATE
    archive_filename_template: str = DEFAULT_ARCHIVE_FILENAME_TEMPLATE


class ValidateRequest(BaseModel):
    step: int
    archive: str = ""
    username: str = ""
    password: str = ""
    password2: str = ""


@router.post("/setup/validate", dependencies=[Depends(require_localhost)])
async def setup_validate(req: ValidateRequest) -> dict:
    """Validate wizard fields for a given step. Returns {fields: {field: error_code}}."""
    errors: dict[str, str] = {}

    if req.step == 3:
        if not req.archive.strip():
            errors["archive"] = "required"
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
async def setup_status() -> dict:
    return {"initialized": is_initialized()}


@router.post("/setup", dependencies=[Depends(require_localhost)])
async def setup(req: SetupRequest) -> dict:
    if is_initialized():
        raise HTTPException(status_code=409, detail="Already initialized")

    archive = req.archive.strip()
    username = req.username.strip()
    password = req.password

    if not archive or not username or not password:
        raise HTTPException(status_code=422, detail="All fields are required")

    Path(archive).mkdir(parents=True, exist_ok=True)
    init_db(archive)

    conn = get_conn()
    now = datetime.now(timezone.utc).isoformat()
    admin_role = conn.execute("SELECT id FROM roles WHERE name = 'admin'").fetchone()
    conn.execute(
        "INSERT INTO users (username, password_hash, role_id, created_at) VALUES (?, ?, ?, ?)",
        (username, hash_password(password), admin_role["id"], now),
    )
    conn.commit()

    fo = read_daemon_config("file-organizer")
    fo.setdefault("watch", {})["output"] = archive
    write_daemon_config("file-organizer", fo)

    pm = read_daemon_config("preview-maker")
    pm.setdefault("watch", {})["path"] = archive
    write_daemon_config("preview-maker", pm)

    _save_format(req.archive_path_template, req.archive_filename_template)

    return {"ok": True}
