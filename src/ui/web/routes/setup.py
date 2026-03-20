"""
Setup routes — first-run initialization wizard.
"""

import asyncio
import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from common.auth import hash_password
from common.config_utils import get_config_dir, read_daemon_config, write_daemon_config
from common.db import get_conn, init_db, is_initialized
from common.logger import Logger
from file_organizer.organizer import FileOrganizer
from file_organizer.previewer import Previewer
from ui.web.deps import require_localhost

router = APIRouter()

_import_thread: threading.Thread | None = None
_import_progress: dict[str, Any] = {}

_STATE_FILE = get_config_dir() / "setup_import.json"


def _read_state() -> dict | None:
    try:
        return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_state(state: dict) -> None:
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


class SetupRequest(BaseModel):
    archive: str
    username: str
    password: str
    inbox: str = ""
    import_path: str = ""
    import_recursive: bool = False


class PreviewRequest(BaseModel):
    input_path: str
    output_path: str
    recursive: bool = False


class ValidateRequest(BaseModel):
    step: int
    archive: str = ""
    username: str = ""
    password: str = ""
    password2: str = ""
    import_path: str = ""
    inbox: str = ""


@router.post("/setup/validate", dependencies=[Depends(require_localhost)])
async def setup_validate(req: ValidateRequest) -> dict:
    """Validate wizard fields for a given step. Returns {fields: {field: error_code}}."""
    errors: dict[str, str] = {}

    def norm(p: str) -> str:
        return p.strip().lower().rstrip("/\\")

    if req.step == 1:
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

    elif req.step == 3:
        if not req.import_path.strip():
            errors["import_path"] = "required"
        else:
            if not Path(req.import_path.strip()).exists():
                errors["import_path"] = "path_not_found"
            elif norm(req.import_path) == norm(req.archive):
                errors["import_path"] = "same_as_archive"

    elif req.step == 5:
        if req.inbox.strip() and norm(req.inbox) == norm(req.archive):
            errors["inbox"] = "same_as_archive"

    return {"fields": errors}


@router.get("/setup/status")
async def setup_status() -> dict:
    initialized = is_initialized()
    state = _read_state()

    if state is None:
        return {"initialized": initialized, "import_status": "none", "import_result": None}

    status = state.get("status")

    if status == "done":
        return {"initialized": initialized, "import_status": "done", "import_result": state}

    if status == "running":
        if _import_thread and _import_thread.is_alive():
            return {"initialized": initialized, "import_status": "running", "import_result": None}
        # Thread is gone (server restarted during import)
        _write_state({**state, "status": "interrupted"})
        return {"initialized": initialized, "import_status": "interrupted", "import_result": None}

    return {"initialized": initialized, "import_status": "none", "import_result": None}


@router.post("/setup/finish", dependencies=[Depends(require_localhost)])
async def setup_finish() -> dict:
    """Delete the import state file — called when user navigates to login after setup."""
    try:
        _STATE_FILE.unlink(missing_ok=True)
    except Exception:
        pass
    return {"ok": True}


@router.post("/setup/preview", dependencies=[Depends(require_localhost)])
async def setup_preview(req: PreviewRequest) -> dict:
    """Dry-run: return a sample of source → destination mappings."""
    input_path = Path(req.input_path.strip())
    output_path = Path(req.output_path.strip())

    if not input_path.exists():
        raise HTTPException(status_code=422, detail="Папка не существует")

    logger = Logger("file_organizer", console=False)
    organizer = FileOrganizer(logger)
    result = organizer(
        input_path=input_path,
        output_path=output_path,
        recursive=req.recursive,
        dry_run=True,
    )
    previewer = Previewer(result)
    return {
        "summary": previewer.summary(),
        "sample": previewer.sample(50),
        "errors": previewer.errors(),
    }


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
    if req.inbox:
        fo.setdefault("watch", {})["path"] = req.inbox
    write_daemon_config("file-organizer", fo)

    pm = read_daemon_config("preview-maker")
    pm.setdefault("watch", {})["path"] = archive
    write_daemon_config("preview-maker", pm)

    if req.import_path:
        _start_import(req.import_path, archive, req.import_recursive)

    return {"ok": True, "importing": bool(req.import_path)}


@router.get("/setup/import/progress", dependencies=[Depends(require_localhost)])
async def import_progress() -> StreamingResponse:
    """SSE stream for import progress."""
    async def generate():
        while True:
            p = _import_progress.copy()
            yield f"data: {json.dumps(p)}\n\n"
            if p.get("done"):
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(generate(), media_type="text/event-stream")


def _start_import(import_path: str, archive: str, recursive: bool) -> None:
    """Start import in a background thread, updating _import_progress and state file."""
    global _import_thread, _import_progress
    _import_progress = {"done": False, "total": 0, "succeeded": 0, "failed": 0, "errors": []}
    _write_state({"status": "running"})

    def _run():
        global _import_progress
        logger = Logger("file_organizer", console=False)
        organizer = FileOrganizer(logger)
        result = organizer(
            input_path=Path(import_path),
            output_path=Path(archive),
            recursive=recursive,
        )
        _import_progress = {
            "done": True,
            "total": result["total"],
            "succeeded": result["succeeded"],
            "failed": result["failed"],
            "errors": result["errors"],
        }
        _write_state({
            "status": "done",
            "total": result["total"],
            "succeeded": result["succeeded"],
            "failed": result["failed"],
        })

    _import_thread = threading.Thread(target=_run, daemon=True)
    _import_thread.start()
