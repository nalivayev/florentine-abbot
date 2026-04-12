"""
FastAPI dependencies for authentication and access control.
"""

from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from common.auth import hash_token, token_is_expired
from common.db import get_conn

_bearer = HTTPBearer(auto_error=False)


def require_localhost(request: Request) -> None:
    """Allow only requests from localhost."""
    host = request.client.host if request.client else ""
    if host not in ("127.0.0.1", "::1", "localhost"):
        raise HTTPException(status_code=403, detail="Local access only")


def _get_token(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> str:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return credentials.credentials


def get_current_user(token: str = Depends(_get_token)) -> dict[str, Any]:
    """Return the user row for the session token. Raises 401 if invalid."""
    conn = get_conn()
    token_hash = hash_token(token)
    row = conn.execute("""
        SELECT u.id, u.username, u.is_active, u.role_id,
               r.name AS role, s.expires_at, s.token_hash
        FROM sessions s
        JOIN users u ON u.id = s.user_id
        JOIN roles r ON r.id = u.role_id
        WHERE s.token_hash = ?
    """, (token_hash,)).fetchone()

    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if token_is_expired(row["expires_at"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    if not row["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User disabled")

    return dict(row)


def check_admin(user: dict[str, Any]) -> dict[str, Any]:
    """Raise 403 if user is not admin. Can be used outside of FastAPI Depends."""
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user


def require_admin(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    """Require admin role."""
    return check_admin(user)
