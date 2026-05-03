"""Shared face API helpers for ui.web routes."""

from pathlib import Path, PurePosixPath
from typing import Any

from fastapi import HTTPException

from common.config_utils import get_archive_path
from face_recognizer.constants import FACES_DIR
from face_recognizer.store import Face, FaceClusterSummary, Person


def archive_path_or_404() -> Any:
    archive_path = get_archive_path()
    if archive_path is None:
        raise HTTPException(status_code=404, detail="Archive not configured")
    return archive_path


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


def person_record_payload(person: Person) -> dict[str, Any]:
    return {
        "id": person.id,
        "name": person.name,
        "notes": person.notes,
        "created_at": person.created_at,
    }


def face_thumb_url(face: Face) -> str | None:
    source_path = Path(face.file.file_path)
    if source_path.is_absolute():
        return None

    thumb_path = PurePosixPath(
        FACES_DIR,
        *source_path.parent.parts,
        source_path.stem,
        f"face-{face.id}.webp",
    )
    return f"/system/{thumb_path.as_posix()}"


def face_payload(face: Face) -> dict[str, Any]:
    return {
        "id": face.id,
        "file_id": face.file_id,
        "file_path": face.file.file_path,
        "region": region_payload(face),
        "confidence": face.confidence,
        "cluster": face.cluster,
        "person": person_payload(face),
        "created_at": face.created_at,
        "thumb_url": face_thumb_url(face),
    }


def cluster_payload(
    cluster: FaceClusterSummary,
    faces: list[Face],
) -> dict[str, Any]:
    return {
        "id": cluster.cluster_id,
        "face_count": cluster.face_count,
        "assigned_face_count": cluster.assigned_face_count,
        "distinct_person_count": cluster.distinct_person_count,
        "created_at": cluster.created_at,
        "faces": [face_payload(face) for face in faces],
    }