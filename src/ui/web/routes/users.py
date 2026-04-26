"""
User management routes.
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.auth import hash_password
from ui.web.deps import get_web_store, require_admin
from ui.web.store import WebStore

router = APIRouter()


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str


@router.get("/users")
async def users_list(
    _user: dict[str, Any] = Depends(require_admin),
    store: WebStore = Depends(get_web_store),
) -> list[dict[str, Any]]:
    return store.list_users()


@router.post("/users")
async def create_user(
    req: CreateUserRequest,
    current_user: dict[str, Any] = Depends(require_admin),
    store: WebStore = Depends(get_web_store),
) -> dict[str, Any]:
    role_id = store.get_role_id(req.role)
    if role_id is None:
        raise HTTPException(status_code=400, detail="invalid_role")

    if store.username_exists(req.username):
        raise HTTPException(status_code=409, detail="username_taken")

    if len(req.username) < 3:
        raise HTTPException(status_code=400, detail="username_too_short")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="password_too_short")

    now = datetime.now(timezone.utc).isoformat()
    store.create_user(
        username=req.username,
        password_hash=hash_password(req.password),
        role_id=role_id,
        created_at=now,
        created_by=int(current_user["id"]),
    )

    row = store.get_user_summary(req.username)
    assert row is not None
    return row


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict[str, Any] = Depends(require_admin),
    store: WebStore = Depends(get_web_store),
) -> dict[str, Any]:
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="cannot_delete_self")

    row = store.get_user_by_id(user_id)
    if not row:
        raise HTTPException(status_code=404, detail="not_found")

    store.delete_user_sessions(user_id)
    store.delete_user(user_id)
    return {"ok": True}
