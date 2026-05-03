"""Shared helpers for flat file routes."""

from pathlib import Path
from typing import Any

from fastapi import HTTPException

from common.constants import ARCHIVE_SYSTEM_DIR
from preview_maker.constants import PREVIEWS_DIR
from tile_cutter.constants import TILES_DIR
from ui.web.store import WebStore


def file_or_404(store: WebStore, file_id: int) -> dict[str, Any]:
    detail = store.get_file_detail(file_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="File not found")
    return detail


def metadata_payload(row: dict[str, Any]) -> dict[str, Any] | None:
    metadata = {
        "photo_year": row.get("photo_year"),
        "photo_month": row.get("photo_month"),
        "photo_day": row.get("photo_day"),
        "photo_time": row.get("photo_time"),
        "date_accuracy": row.get("date_accuracy"),
        "description": row.get("description"),
        "source": row.get("source"),
        "credit": row.get("credit"),
    }
    lat = row.get("gps_lat")
    lon = row.get("gps_lon")
    if lat is not None and lon is not None:
        metadata["gps"] = {
            "lat": float(lat),
            "lon": float(lon),
            "altitude": None if row.get("gps_altitude") is None else float(row["gps_altitude"]),
        }
    return metadata if any(value is not None for value in metadata.values()) else None


def preview_url(archive_path: Path | None, parts: tuple[str, ...], stem: str, dir_parts: str) -> str | None:
    if not archive_path:
        return None
    prv_dir = archive_path / ARCHIVE_SYSTEM_DIR / PREVIEWS_DIR / Path(*parts[:-1])
    if not prv_dir.exists():
        return None
    base = ".".join(stem.split(".")[:11])
    for candidate in list(prv_dir.glob("*.jpg")) + list(prv_dir.glob("*.jpeg")):
        if candidate.stem.startswith(base):
            return f"/system/previews/{dir_parts}/{candidate.name}"
    return None


def tile_base_url(archive_path: Path | None, parts: tuple[str, ...], stem: str, dir_parts: str) -> str | None:
    if not archive_path:
        return None
    tile_dir = archive_path / ARCHIVE_SYSTEM_DIR / TILES_DIR / Path(*parts[:-1]) / stem
    if (tile_dir / "meta.json").exists():
        return f"/system/tiles/{dir_parts}/{stem}"
    return None


def decorate_file_row(row: dict[str, Any], archive_path: Path | None) -> dict[str, Any]:
    normalized_path = str(row["path"]).replace("\\", "/")
    rel_path = Path(normalized_path)
    parts = rel_path.parts
    stem = rel_path.stem
    dir_parts = "/".join(parts[:-1])
    return {
        "id": int(row["id"]),
        "collection_id": int(row["collection_id"]) if row.get("collection_id") is not None else None,
        "collection_name": str(row["collection_name"]) if row.get("collection_name") is not None else None,
        "path": normalized_path,
        "status": str(row["status"]),
        "imported_at": str(row["imported_at"]),
        "preview_url": preview_url(archive_path, parts, stem, dir_parts),
        "tile_base_url": tile_base_url(archive_path, parts, stem, dir_parts),
    }
