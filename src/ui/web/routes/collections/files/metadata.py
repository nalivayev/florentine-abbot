"""Collection-rooted file metadata routes."""

from typing import Any

from fastapi import APIRouter, Depends

from ui.web.deps import get_current_user, get_web_store
from ui.web.routes.collections.files.common import collection_file_detail_or_404, metadata_payload
from ui.web.store import WebStore

router = APIRouter()


@router.get("/collections/{collection_id}/files/{file_id}/metadata")
async def get_file_metadata(
    collection_id: int,
    file_id: int,
    _user: dict[str, Any] = Depends(get_current_user),
    store: WebStore = Depends(get_web_store),
) -> dict[str, Any] | None:
    detail = collection_file_detail_or_404(store, collection_id, file_id)
    return metadata_payload(detail)