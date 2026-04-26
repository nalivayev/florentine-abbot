"""Global face routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from common.config_utils import get_archive_path
from face_recognizer.store import Face, RecognizerStore
from ui.web.deps import get_current_user

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


@router.get("/faces/{face_id}")
async def get_face(
	face_id: int,
	_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
	archive_path = archive_path_or_404()
	with RecognizerStore(archive_path) as store:
		face = store.get_face(face_id)
	if face is None:
		raise HTTPException(status_code=404, detail="Face not found")
	return face_payload(face)