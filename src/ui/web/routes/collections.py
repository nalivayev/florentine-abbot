"""
Collections API routes.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.config_utils import get_archive_path
from common.db import get_conn
from ui.web.deps import get_current_user, require_admin

router = APIRouter()


class CollectionCreate(BaseModel):
    type: str
    name: str


def _preview_url(archive: Path | None, parts: tuple, stem: str, dir_parts: str) -> str | None:
    if not archive:
        return None
    prv_dir = archive / ".system" / "previews" / Path(*parts[:-1])
    if not prv_dir.exists():
        return None
    base = ".".join(stem.split(".")[:11])
    for c in list(prv_dir.glob("*.jpg")) + list(prv_dir.glob("*.jpeg")):
        if c.stem.startswith(base):
            return f"/system/previews/{dir_parts}/{c.name}"
    return None


def _tile_base_url(archive: Path | None, parts: tuple, stem: str, dir_parts: str) -> str | None:
    if not archive:
        return None
    tile_dir = archive / ".system" / "tiles" / Path(*parts[:-1]) / stem
    if (tile_dir / "meta.json").exists():
        return f"/system/tiles/{dir_parts}/{stem}"
    return None


@router.get("/collections")
async def list_collections(
    _user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    try:
        conn = get_conn()
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Database not initialized")
    rows = conn.execute(
        "SELECT id, type, name, created_at FROM collections ORDER BY id"
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/collections/{collection_id}/files")
async def list_collection_files(
    collection_id: int,
    _user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    try:
        conn = get_conn()
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Database not initialized")

    rows = conn.execute(
        """
        SELECT id, path, status, checksum, imported_at
        FROM files
        WHERE collection_id = ?
        ORDER BY path
        """,
        (collection_id,),
    ).fetchall()

    archive = get_archive_path()
    result = []
    for row in rows:
        rel = row["path"]  # e.g. scan/000001/2025/2025.06.01/file.tif
        rel_path = Path(rel)
        parts = rel_path.parts  # ('scan', '000001', '2025', '2025.06.01', 'file.tif')
        stem = rel_path.stem

        dir_parts = "/".join(parts[:-1])
        prv_url = _preview_url(archive, parts, stem, dir_parts)
        tile_base_url = _tile_base_url(archive, parts, stem, dir_parts)

        result.append({
            "id": row["id"],
            "path": rel,
            "status": row["status"],
            "preview_url": prv_url,
            "tile_base_url": tile_base_url,
        })

    return result


@router.get("/collections/{collection_id}/files/{file_id}")
async def get_collection_file(
    collection_id: int,
    file_id: int,
    _user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    try:
        conn = get_conn()
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Database not initialized")

    rows = conn.execute(
        "SELECT id, path FROM files WHERE collection_id = ? ORDER BY path",
        (collection_id,),
    ).fetchall()

    ids = [r["id"] for r in rows]
    if file_id not in ids:
        raise HTTPException(status_code=404, detail="File not found")

    idx = ids.index(file_id)
    row = rows[idx]

    archive = get_archive_path()
    rel_path = Path(row["path"])
    parts = rel_path.parts
    stem = rel_path.stem
    dir_parts = "/".join(parts[:-1])

    prv_url = _preview_url(archive, parts, stem, dir_parts)
    tile_base_url = _tile_base_url(archive, parts, stem, dir_parts)

    # Find prev/next among files that have tiles
    viewable = []
    for r in rows:
        rp = Path(r["path"])
        if archive:
            td = archive / ".system" / "tiles" / Path(*rp.parts[:-1]) / rp.stem
            if (td / "meta.json").exists():
                viewable.append(r["id"])

    vidx = viewable.index(file_id) if file_id in viewable else -1
    prev_id = viewable[vidx - 1] if vidx > 0 else None
    next_id = viewable[vidx + 1] if vidx >= 0 and vidx < len(viewable) - 1 else None

    return {
        "id": file_id,
        "path": row["path"],
        "preview_url": prv_url,
        "tile_base_url": tile_base_url,
        "prev_id": prev_id,
        "next_id": next_id,
    }


@router.post("/collections")
async def create_collection(
    body: CollectionCreate,
    _user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")
    if not body.type.strip():
        raise HTTPException(status_code=400, detail="Type is required")
    try:
        conn = get_conn()
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Database not initialized")
    created_at = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO collections (type, name, created_at) VALUES (?, ?, ?)",
        (body.type.strip(), body.name.strip(), created_at),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id, type, name, created_at FROM collections WHERE id = ?",
        (cur.lastrowid,),
    ).fetchone()
    return dict(row)
