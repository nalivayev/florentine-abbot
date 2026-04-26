"""Collection-rooted file faces routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from common.config_utils import get_archive_path
from face_recognizer.store import Face, RecognizerStore
from ui.web.deps import get_current_user, get_web_store
from ui.web.routes.collections.files.common import collection_file_detail_or_404
from ui.web.store import WebStore

router = APIRouter()


def region_payload(face: Face) -> dict[str, float]:
    return {
        "center_x": face.center_x,
        "center_y": face.center_y,
        "width": face.width,
        "height": face.height,
    }


def person_payload(face: Face) -> dict[str, Any] | None:
    if face.person is None:
        return None
    return {
        "id": face.person.id,
        "name": face.person.name,
    }


def face_payload(face: Face) -> dict[str, Any]:
    return {
        "id": face.id,
        "file_id": face.file_id,
        "region": region_payload(face),
        "confidence": face.confidence,
        "cluster": face.cluster,
        "person": person_payload(face),
        "created_at": face.created_at,
    }


def archive_path_or_404() -> Any:
    archive_path = get_archive_path()
    if archive_path is None:
        raise HTTPException(status_code=404, detail="Archive not configured")
    return archive_path


@router.get("/collections/{collection_id}/files/{file_id}/faces")
async def list_faces(
    collection_id: int,
    file_id: int,
    _user: dict[str, Any] = Depends(get_current_user),
    store: WebStore = Depends(get_web_store),
) -> list[dict[str, Any]]:
    collection_file_detail_or_404(store, collection_id, file_id)

    archive_path = archive_path_or_404()
    with RecognizerStore(archive_path) as recognizer_store:
        faces = recognizer_store.get_faces_by_file_id(file_id)
    return [face_payload(face) for face in faces]