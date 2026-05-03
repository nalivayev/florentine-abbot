"""Global map routes."""

from typing import Any

from fastapi import APIRouter, Depends

from ui.web.deps import get_current_user, get_web_store
from ui.web.store import WebStore

router = APIRouter()


def _map_file_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "collection_id": None if row.get("collection_id") is None else int(row["collection_id"]),
        "collection_name": row.get("collection_name"),
        "path": str(row["path"]),
        "gps": {
            "lat": float(row["gps_lat"]),
            "lon": float(row["gps_lon"]),
            "altitude": None if row.get("gps_altitude") is None else float(row["gps_altitude"]),
        },
    }


@router.get("/map/files")
async def list_map_files(
    _user: dict[str, Any] = Depends(get_current_user),
    store: WebStore = Depends(get_web_store),
) -> list[dict[str, Any]]:
    return [_map_file_payload(row) for row in store.list_geotagged_files()]