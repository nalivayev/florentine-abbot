"""Collection-rooted file routes."""

from typing import Any

from fastapi import APIRouter, Depends

from common.config_utils import get_archive_path
from ui.web.deps import get_current_user, get_web_store
from ui.web.routes.collections.files.common import collection_file_detail_or_404, decorate_file_row
from ui.web.routes.collections.files.faces import router as faces_router
from ui.web.routes.collections.files.history import router as history_router
from ui.web.routes.collections.files.metadata import router as metadata_router
from ui.web.routes.collections.files.navigation import router as navigation_router
from ui.web.store import WebStore

router = APIRouter()


@router.get("/collections/{collection_id}/files")
async def list_files(
    collection_id: int,
    _user: dict[str, Any] = Depends(get_current_user),
    store: WebStore = Depends(get_web_store),
) -> list[dict[str, Any]]:
    rows = store.list_files(collection_id=collection_id)
    archive_path = get_archive_path()
    return [decorate_file_row(row, archive_path) for row in rows]


@router.get("/collections/{collection_id}/files/{file_id}")
async def get_file(
    collection_id: int,
    file_id: int,
    _user: dict[str, Any] = Depends(get_current_user),
    store: WebStore = Depends(get_web_store),
) -> dict[str, Any]:
    detail = collection_file_detail_or_404(store, collection_id, file_id)

    archive_path = get_archive_path()
    payload = decorate_file_row(detail, archive_path)
    payload["creators"] = store.list_file_creators(file_id)
    return payload


router.include_router(metadata_router)
router.include_router(history_router)
router.include_router(faces_router)
router.include_router(navigation_router)