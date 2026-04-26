"""Collection-rooted file navigation routes."""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends

from common.config_utils import get_archive_path
from ui.web.deps import get_current_user, get_web_store
from ui.web.routes.collections.files.common import collection_file_detail_or_404, tile_base_url
from ui.web.store import WebStore

router = APIRouter()


@router.get("/collections/{collection_id}/files/{file_id}/navigation")
async def get_file_navigation(
    collection_id: int,
    file_id: int,
    _user: dict[str, Any] = Depends(get_current_user),
    store: WebStore = Depends(get_web_store),
) -> dict[str, int | None]:
    collection_file_detail_or_404(store, collection_id, file_id)

    rows = store.list_file_paths(collection_id=collection_id)
    archive_path = get_archive_path()
    viewable: list[int] = []
    for row in rows:
        rel_path = Path(str(row["path"]))
        parts = rel_path.parts
        stem = rel_path.stem
        dir_parts = "/".join(parts[:-1])
        if tile_base_url(archive_path, parts, stem, dir_parts):
            viewable.append(int(row["id"]))

    index = viewable.index(file_id) if file_id in viewable else -1
    prev_id = viewable[index - 1] if index > 0 else None
    next_id = viewable[index + 1] if index >= 0 and index < len(viewable) - 1 else None
    return {
        "file_id": file_id,
        "collection_id": collection_id,
        "prev_id": prev_id,
        "next_id": next_id,
    }