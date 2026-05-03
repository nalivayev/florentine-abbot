"""File faces route."""

from typing import Any

from fastapi import APIRouter, Depends

from face_recognizer.store import RecognizerStore
from ui.web.deps import get_current_user, get_web_store
from ui.web.routes.faces_common import archive_path_or_404, face_payload
from ui.web.routes.files.common import file_or_404
from ui.web.store import WebStore

router = APIRouter()


@router.get("/files/{file_id}/faces")
async def list_faces(
    file_id: int,
    _user: dict[str, Any] = Depends(get_current_user),
    store: WebStore = Depends(get_web_store),
) -> list[dict[str, Any]]:
    file_or_404(store, file_id)
    archive_path = archive_path_or_404()
    with RecognizerStore(archive_path) as recognizer_store:
        faces = recognizer_store.get_faces_by_file_id(file_id)
    return [face_payload(face) for face in faces]
