"""
Auth routes — login, logout, current user.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.auth import generate_token, hash_token, token_expires_at, verify_password
from common.db import get_conn
from ui.web.deps import get_current_user

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/login")
async def login(req: LoginRequest) -> dict:
    conn = get_conn()
    row = conn.execute(
        "SELECT id, password_hash, is_active FROM users WHERE username = ?",
        (req.username,),
    ).fetchone()

    if not row or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not row["is_active"]:
        raise HTTPException(status_code=403, detail="User disabled")

    raw, hashed = generate_token()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO sessions (user_id, token_hash, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (row["id"], hashed, now, token_expires_at()),
    )
    conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (now, row["id"]))
    conn.commit()

    return {"token": raw}


@router.post("/auth/logout")
async def logout(user: dict = Depends(get_current_user)) -> dict:
    conn = get_conn()
    conn.execute("DELETE FROM sessions WHERE user_id = ? AND token_hash = ?",
                 (user["id"], user["token_hash"]))
    conn.commit()
    return {"ok": True}


@router.get("/auth/me")
async def me(user: dict = Depends(get_current_user)) -> dict:
    return {"id": user["id"], "username": user["username"], "role": user["role"]}
