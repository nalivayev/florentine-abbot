"""
User management routes.
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.auth import hash_password
from common.db import get_conn
from ui.web.deps import require_admin

router = APIRouter()


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str


@router.get("/users")
async def users_list(_user: dict[str, Any] = Depends(require_admin)) -> list[dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute("""
        SELECT u.id, u.username, r.name AS role, u.is_active, u.created_at, u.last_login_at
        FROM users u
        JOIN roles r ON r.id = u.role_id
        ORDER BY u.id
    """).fetchall()
    return [dict(r) for r in rows]


@router.post("/users")
async def create_user(
    req: CreateUserRequest,
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    conn = get_conn()

    role_row = conn.execute("SELECT id FROM roles WHERE name = ?", (req.role,)).fetchone()
    if not role_row:
        raise HTTPException(status_code=400, detail="invalid_role")

    existing = conn.execute("SELECT id FROM users WHERE username = ?", (req.username,)).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail="username_taken")

    if len(req.username) < 3:
        raise HTTPException(status_code=400, detail="username_too_short")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="password_too_short")

    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO users (username, password_hash, role_id, is_active, created_by, created_at) VALUES (?, ?, ?, 1, ?, ?)",
        (req.username, hash_password(req.password), role_row["id"], current_user["id"], now),
    )
    conn.commit()

    row = conn.execute("""
        SELECT u.id, u.username, r.name AS role, u.is_active, u.created_at, u.last_login_at
        FROM users u JOIN roles r ON r.id = u.role_id
        WHERE u.username = ?
    """, (req.username,)).fetchone()
    return dict(row)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="cannot_delete_self")

    conn = get_conn()
    row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="not_found")

    conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    return {"ok": True}
