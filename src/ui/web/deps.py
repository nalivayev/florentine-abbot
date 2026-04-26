"""
FastAPI dependencies for authentication and access control.
"""

from collections.abc import Generator
from pathlib import Path
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from common.auth import hash_token, token_is_expired
from common.config_utils import get_archive_path
from ui.web.setup_store import SetupStore
from ui.web.store import WebStore

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


def get_runtime_archive_path() -> Path:
    """Return the configured archive path for the runtime web app."""
    archive_path = get_archive_path()
    if archive_path is None or not SetupStore(archive_path).exists():
        raise HTTPException(status_code=503, detail="Database not initialized")
    return archive_path


def get_web_store() -> Generator[WebStore, None, None]:
    """Return a request-scoped WebStore with store-owned DB lifecycle."""
    with WebStore(get_runtime_archive_path()) as store:
        yield store


def get_current_user(
    token: str = Depends(_get_token),
    store: WebStore = Depends(get_web_store),
) -> dict[str, Any]:
    """Return the user row for the session token. Raises 401 if invalid."""
    token_hash = hash_token(token)
    row = store.get_user_by_token_hash(token_hash)

    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if token_is_expired(str(row["expires_at"])):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    if not row["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User disabled")

    return row


def check_admin(user: dict[str, Any]) -> dict[str, Any]:
    """Raise 403 if user is not admin. Can be used outside of FastAPI Depends."""
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user


def require_admin(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    """Require admin role."""
    return check_admin(user)
