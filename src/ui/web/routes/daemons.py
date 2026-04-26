"""
Daemon management routes.
"""

import asyncio
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from common.auth import hash_token, token_is_expired
from ui.web.daemon_manager import DaemonState, manager
from ui.web.deps import check_admin, get_web_store, require_admin
from ui.web.store import WebStore

router = APIRouter()


def _serialize(state: DaemonState) -> dict[str, Any]:
    return {
        "descriptor": {
            "name": state.descriptor.name,
            "label": state.descriptor.label,
            "description": state.descriptor.description,
        },
        "status": state.status.value,
        "watch_path": state.watch_path,
        "error": state.error,
    }


def _auth_by_token(token: str, store: WebStore) -> dict[str, Any]:
    """Authenticate by raw token string (for SSE query param fallback)."""
    hashed = hash_token(token)
    row = store.get_user_by_token_hash(hashed)

    if not row:
        raise HTTPException(status_code=401, detail="Invalid token")
    if token_is_expired(str(row["expires_at"])):
        raise HTTPException(status_code=401, detail="Token expired")
    if not row["is_active"]:
        raise HTTPException(status_code=403, detail="User disabled")
    return row


def _require_admin_by_token(token: str, store: WebStore) -> dict[str, Any]:
    return check_admin(_auth_by_token(token, store))


@router.get("/daemons")
async def daemons_list(_user: dict[str, Any] = Depends(require_admin)) -> list[dict[str, Any]]:
    return [_serialize(d) for d in manager.all()]


@router.post("/daemons/{name}/start")
async def daemon_start(name: str, _user: dict[str, Any] = Depends(require_admin)) -> list[dict[str, Any]]:
    manager.start(name)
    return [_serialize(d) for d in manager.all()]


@router.post("/daemons/{name}/stop")
async def daemon_stop(name: str, _user: dict[str, Any] = Depends(require_admin)) -> list[dict[str, Any]]:
    manager.stop(name)
    return [_serialize(d) for d in manager.all()]


@router.get("/daemons/{name}/logs")
async def daemon_logs(
    name: str,
    token: str = Query(..., description="Session token"),
    store: WebStore = Depends(get_web_store),
) -> StreamingResponse:
    _require_admin_by_token(token, store)

    async def generate():
        sent = 0
        try:
            while True:
                lines = manager.get_logs(name)
                for line in lines[sent:]:
                    yield f"data: {json.dumps(line)}\n\n"
                sent = len(lines)
                await asyncio.sleep(0.3)
        except asyncio.CancelledError:
            pass

    return StreamingResponse(generate(), media_type="text/event-stream")
