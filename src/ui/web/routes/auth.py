"""
Auth routes — login, logout, current user.
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.auth import generate_token, token_expires_at, verify_password
from ui.web.deps import get_current_user, get_web_store
from ui.web.store import WebStore

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/login")
async def login(req: LoginRequest, store: WebStore = Depends(get_web_store)) -> dict[str, str]:
    row = store.get_user_for_login(req.username)

    if not row or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not row["is_active"]:
        raise HTTPException(status_code=403, detail="User disabled")

    raw, hashed = generate_token()
    now = datetime.now(timezone.utc).isoformat()
    store.create_session(
        user_id=int(row["id"]),
        token_hash=hashed,
        created_at=now,
        expires_at=token_expires_at(),
    )
    store.update_last_login(int(row["id"]), now)

    return {"token": raw}


@router.post("/auth/logout")
async def logout(
    user: dict[str, Any] = Depends(get_current_user),
    store: WebStore = Depends(get_web_store),
) -> dict[str, bool]:
    store.delete_session(int(user["id"]), str(user["token_hash"]))
    return {"ok": True}


@router.get("/auth/me")
async def me(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return {"id": user["id"], "username": user["username"], "role": user["role"]}
