"""Collection-rooted file history routes."""

from typing import Any

from fastapi import APIRouter, Depends

from ui.web.deps import get_current_user, get_web_store
from ui.web.routes.collections.files.common import collection_file_detail_or_404
from ui.web.store import WebStore

router = APIRouter()


@router.get("/collections/{collection_id}/files/{file_id}/history")
async def get_file_history(
    collection_id: int,
    file_id: int,
    _user: dict[str, Any] = Depends(get_current_user),
    store: WebStore = Depends(get_web_store),
) -> list[dict[str, Any]]:
    collection_file_detail_or_404(store, collection_id, file_id)
    return store.list_file_history(file_id)