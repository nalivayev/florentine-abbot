"""Global face routes."""

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from face_recognizer.store import RecognizerStore
from ui.web.deps import get_current_user, require_admin
from ui.web.routes.faces_common import (
    archive_path_or_404,
    cluster_payload,
    face_payload,
    person_record_payload,
)

router = APIRouter()


class AssignClusterPersonRequest(BaseModel):
    person_id: int = Field(gt=0)


class CreatePersonFromClusterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    notes: str | None = None


def _not_found_from_value_error(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=404, detail=str(exc))


@router.get("/people/review/clusters")
async def list_review_clusters(
    _user: dict[str, Any] = Depends(require_admin),
) -> list[dict[str, Any]]:
    archive_path = archive_path_or_404()
    with RecognizerStore(archive_path) as store:
        clusters = store.list_unconfirmed_clusters()
        return [
            cluster_payload(cluster, store.get_faces_by_cluster(cluster.cluster_id))
            for cluster in clusters
        ]


@router.get("/people/review/persons")
async def list_review_persons(
    _user: dict[str, Any] = Depends(require_admin),
) -> list[dict[str, Any]]:
    archive_path = archive_path_or_404()
    with RecognizerStore(archive_path) as store:
        persons = store.get_all_persons()
    return [person_record_payload(person) for person in persons]


@router.post("/people/review/clusters/{cluster_id}/assign")
async def assign_review_cluster_person(
    cluster_id: int,
    request: AssignClusterPersonRequest,
    _user: dict[str, Any] = Depends(require_admin),
) -> dict[str, int]:
    archive_path = archive_path_or_404()
    with RecognizerStore(archive_path) as store:
        try:
            updated_faces = store.assign_cluster_to_person(cluster_id, request.person_id)
        except ValueError as exc:
            raise _not_found_from_value_error(exc) from exc
    return {"updated_faces": updated_faces}


@router.post("/people/review/clusters/{cluster_id}/create-person")
async def create_review_cluster_person(
    cluster_id: int,
    request: CreatePersonFromClusterRequest,
    _user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    archive_path = archive_path_or_404()
    with RecognizerStore(archive_path) as store:
        try:
            person = store.create_person_from_cluster(
                cluster_id,
                name=request.name.strip(),
                notes=request.notes,
            )
        except ValueError as exc:
            raise _not_found_from_value_error(exc) from exc
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Person with this name already exists") from exc
    return {"person": person_record_payload(person)}


@router.post("/people/review/faces/{face_id}/exclude")
async def exclude_review_face(
    face_id: int,
    _user: dict[str, Any] = Depends(require_admin),
) -> dict[str, int]:
    archive_path = archive_path_or_404()
    with RecognizerStore(archive_path) as store:
        try:
            store.exclude_face_from_cluster(face_id)
        except ValueError as exc:
            raise _not_found_from_value_error(exc) from exc
    return {"excluded_face_id": face_id}


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