"""Collections API routes."""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ui.web.deps import get_current_user, get_web_store, require_admin
from ui.web.routes.collections.files import router as files_router
from ui.web.store import WebStore

router = APIRouter()


class CollectionCreate(BaseModel):
    type: str
    name: str


@router.get("/collections")
async def list_collections(
    _user: dict[str, Any] = Depends(get_current_user),
    store: WebStore = Depends(get_web_store),
) -> list[dict[str, Any]]:
    return store.list_collections()


@router.post("/collections")
async def create_collection(
    body: CollectionCreate,
    _user: dict[str, Any] = Depends(require_admin),
    store: WebStore = Depends(get_web_store),
) -> dict[str, Any]:
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")
    if not body.type.strip():
        raise HTTPException(status_code=400, detail="Type is required")
    return store.create_collection(
        collection_type=body.type.strip(),
        name=body.name.strip(),
        created_at=datetime.now(timezone.utc).isoformat(),
    )


router.include_router(files_router)