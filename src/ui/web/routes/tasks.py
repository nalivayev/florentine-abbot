"""Routes for user-facing task listing."""

from pathlib import Path
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from common.database import ArchiveDatabase
from ui.web.deps import get_runtime_archive_path, require_admin

router = APIRouter(prefix="/tasks")

_SELECT = "SELECT id, domain, action, status, payload, steps, done, failed, created_at, started_at, finished_at FROM tasks"


def _parse_row(row: Any) -> dict[str, Any]:
    result = dict(row)
    try:
        result["payload"] = json.loads(result.get("payload") or "null")
    except Exception:
        pass
    return result


@router.get("")
def list_tasks(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    archive_path: Path = Depends(get_runtime_archive_path),
    _user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    db = ArchiveDatabase(archive_path)
    try:
        conn = db.get_conn()
        total: int = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        offset = (page - 1) * per_page
        rows = conn.execute(
            f"{_SELECT} ORDER BY id DESC LIMIT ? OFFSET ?", (per_page, offset)
        ).fetchall()
    finally:
        db.close_conn()
    pages = max(1, (total + per_page - 1) // per_page)
    return {"items": [_parse_row(r) for r in rows], "total": total, "page": page, "pages": pages}


@router.get("/{task_id}")
def get_task(
    task_id: int,
    archive_path: Path = Depends(get_runtime_archive_path),
    _user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    db = ArchiveDatabase(archive_path)
    try:
        row = db.get_conn().execute(f"{_SELECT} WHERE id = ?", (task_id,)).fetchone()
    finally:
        db.close_conn()
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return _parse_row(row)
