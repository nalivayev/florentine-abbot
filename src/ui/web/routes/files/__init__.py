"""Flat file routes."""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from common.config_utils import get_archive_path
from common.task_store import TaskStore
from ui.web.deps import get_current_user, get_web_store, require_admin
from ui.web.routes.files.common import decorate_file_row, file_or_404, preview_url
from ui.web.routes.files.faces import router as faces_router
from ui.web.routes.files.history import router as history_router
from ui.web.routes.files.metadata import router as metadata_router
from ui.web.routes.files.navigation import router as navigation_router
from ui.web.store import WebStore

router = APIRouter()


class DeleteItemsRequest(BaseModel):
    files: list[int] = Field(default_factory=list)
    file_paths: list[str] = Field(default_factory=list)
    folders: list[str] = Field(default_factory=list)


def _archive_path_or_400() -> str:
    archive_path = get_archive_path()
    if not archive_path:
        raise HTTPException(status_code=400, detail="Archive not configured")
    return archive_path


def _delete_file_now(store: WebStore, archive_path: str, file_id: int) -> dict[str, Any]:
    detail = file_or_404(store, file_id)
    path = str(detail["path"])
    physical_path = Path(archive_path) / path
    if physical_path.is_file():
        physical_path.unlink()
    store.mark_file_deleted(file_id)
    return {"kind": "file", "key": f"file:{file_id}", "file_id": file_id, "path": path}


def _delete_file_path_now(archive_path: str, path: str) -> dict[str, Any]:
    clean = path.strip("/")
    if not clean:
        raise HTTPException(status_code=400, detail="path is required")
    physical_path = Path(archive_path) / Path(clean)
    if not physical_path.is_file():
        raise HTTPException(status_code=404, detail="Not Found")
    physical_path.unlink()
    return {"kind": "file", "key": f"file-path:{clean}", "path": clean}


def _delete_folder_now(store: WebStore, archive_path: str, path: str) -> dict[str, Any]:
    clean = path.strip("/")
    if not clean:
        raise HTTPException(status_code=400, detail="path is required")
    if not store.folder_is_empty(archive_path, clean):
        raise HTTPException(status_code=409, detail="Folder is not empty")
    physical = Path(archive_path) / Path(clean)
    if physical.is_dir():
        physical.rmdir()
    return {"kind": "folder", "key": f"folder:{clean}", "path": clean}


def _run_delete_task(
    store: WebStore,
    archive_path: str,
    *,
    file_ids: list[int],
    file_paths: list[str],
    folder_paths: list[str],
) -> dict[str, Any]:
    normalized_file_paths = [path.strip("/") for path in file_paths if path and path.strip("/")]
    normalized_folders = [path.strip("/") for path in folder_paths if path and path.strip("/")]
    if not file_ids and not normalized_file_paths and not normalized_folders:
        raise HTTPException(status_code=400, detail="Nothing to delete")

    deleted: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    with TaskStore(archive_path) as tasks:
        task_id = tasks.create_task(
            domain="files",
            action="delete",
            payload={
                "file_count": len(file_ids) + len(normalized_file_paths),
                "folder_count": len(normalized_folders),
                "count": len(file_ids) + len(normalized_file_paths) + len(normalized_folders),
            },
        )
        steps: list[dict[str, Any]] = []

        for file_id in file_ids:
            steps.append({
                "kind": "file",
                "file_id": file_id,
                "key": f"file:{file_id}",
                "step_id": tasks.create_step(task_id=task_id, kind="delete_file", payload={"file_id": file_id}),
            })

        for path in normalized_file_paths:
            steps.append({
                "kind": "file_path",
                "path": path,
                "key": f"file-path:{path}",
                "step_id": tasks.create_step(task_id=task_id, kind="delete_file_path", payload={"path": path}),
            })

        for path in normalized_folders:
            steps.append({
                "kind": "folder",
                "path": path,
                "key": f"folder:{path}",
                "step_id": tasks.create_step(task_id=task_id, kind="delete_folder", payload={"path": path}),
            })

        tasks.start_task(task_id)

        for step in steps:
            tasks.start_step(step["step_id"])
            try:
                if step["kind"] == "file":
                    deleted.append(_delete_file_now(store, archive_path, int(step["file_id"])))
                elif step["kind"] == "file_path":
                    deleted.append(_delete_file_path_now(archive_path, str(step["path"])))
                else:
                    deleted.append(_delete_folder_now(store, archive_path, str(step["path"])))
            except HTTPException as exc:
                detail = str(exc.detail)
                tasks.fail_step(step["step_id"], detail)
                failed.append({
                    "kind": step["kind"],
                    "key": step["key"],
                    "detail": detail,
                    "status_code": exc.status_code,
                })
            except Exception as exc:  # pragma: no cover - defensive runtime guard
                detail = str(exc) or exc.__class__.__name__
                tasks.fail_step(step["step_id"], detail)
                failed.append({
                    "kind": step["kind"],
                    "key": step["key"],
                    "detail": detail,
                    "status_code": 500,
                })
            else:
                tasks.finish_step(step["step_id"])

        if failed:
            tasks.fail_task(task_id)
        else:
            tasks.finish_task(task_id)

    return {"task_id": task_id, "deleted": deleted, "failed": failed}


@router.get("/files/tree")
async def get_file_tree(
    _user: dict[str, Any] = Depends(require_admin),
    store: WebStore = Depends(get_web_store),
) -> list[dict[str, Any]]:
    archive_path = get_archive_path()
    if not archive_path:
        return []
    return store.file_tree(archive_path)


@router.get("/files/browse")
async def browse_files(
    path: str = Query(""),
    _user: dict[str, Any] = Depends(require_admin),
    store: WebStore = Depends(get_web_store),
) -> dict[str, Any]:
    archive_path = get_archive_path()
    if not archive_path:
        return {"path": path, "folders": [], "files": []}
    return store.browse_files(archive_path, path)


@router.get("/files")
async def list_files(
    collection_id: int | None = Query(None),
    _user: dict[str, Any] = Depends(get_current_user),
    store: WebStore = Depends(get_web_store),
) -> list[dict[str, Any]]:
    rows = store.list_files(collection_id=collection_id)
    archive_path = get_archive_path()
    return [decorate_file_row(row, archive_path) for row in rows]


@router.post("/files/delete")
async def delete_items(
    request: DeleteItemsRequest,
    _user: dict[str, Any] = Depends(require_admin),
    store: WebStore = Depends(get_web_store),
) -> dict[str, Any]:
    archive_path = _archive_path_or_400()
    return _run_delete_task(
        store,
        archive_path,
        file_ids=request.files,
        file_paths=request.file_paths,
        folder_paths=request.folders,
    )


@router.get("/files/{file_id}")
async def get_file(
    file_id: int,
    _user: dict[str, Any] = Depends(get_current_user),
    store: WebStore = Depends(get_web_store),
) -> dict[str, Any]:
    detail = file_or_404(store, file_id)
    archive_path = get_archive_path()
    payload = decorate_file_row(detail, archive_path)
    payload["creators"] = store.list_file_creators(file_id)
    return payload


@router.get("/files/{file_id}/preview")
async def get_file_preview(
    file_id: int,
    store: WebStore = Depends(get_web_store),
) -> RedirectResponse:
    detail = file_or_404(store, file_id)
    archive_path = get_archive_path()
    rel = Path(str(detail["path"]))
    parts = rel.parts
    stem = rel.stem
    dir_parts = "/".join(parts[:-1])
    url = preview_url(Path(archive_path) if archive_path else None, parts, stem, dir_parts)
    if not url:
        raise HTTPException(status_code=404, detail="Preview not found")
    return RedirectResponse(url=url)


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: int,
    _user: dict[str, Any] = Depends(require_admin),
    store: WebStore = Depends(get_web_store),
) -> dict[str, Any]:
    archive_path = _archive_path_or_400()
    result = _run_delete_task(store, archive_path, file_ids=[file_id], folder_paths=[])
    if result["failed"]:
        failed = result["failed"][0]
        raise HTTPException(status_code=int(failed["status_code"]), detail=failed["detail"])
    return {"deleted_file_id": file_id, "task_id": result["task_id"]}


@router.delete("/folders")
async def delete_folder(
    path: str = Query(""),
    _user: dict[str, Any] = Depends(require_admin),
    store: WebStore = Depends(get_web_store),
) -> dict[str, Any]:
    archive_path = _archive_path_or_400()
    result = _run_delete_task(store, archive_path, file_ids=[], folder_paths=[path])
    if result["failed"]:
        failed = result["failed"][0]
        raise HTTPException(status_code=int(failed["status_code"]), detail=failed["detail"])
    return {"deleted_path": path.strip("/"), "task_id": result["task_id"]}


@router.post("/folders")
async def create_folder(
    path: str = Body(..., embed=True),
    _user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    archive_path = get_archive_path()
    if not archive_path:
        raise HTTPException(status_code=400, detail="Archive not configured")
    clean = path.strip("/")
    if not clean:
        raise HTTPException(status_code=400, detail="path is required")
    physical = Path(archive_path) / Path(clean)
    physical.mkdir(parents=True, exist_ok=True)
    return {"created_path": clean}


router.include_router(metadata_router)
router.include_router(history_router)
router.include_router(faces_router)
router.include_router(navigation_router)
