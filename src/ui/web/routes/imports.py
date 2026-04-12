"""
Import routes — local folder scanning and import.
"""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.config_utils import get_archive_path
from common.constants import SUPPORTED_IMAGE_EXTENSIONS
from content_importer.scan_importer import ScanImporter
from content_importer.scan_validator import ScanValidator
from ui.web.deps import require_admin

router = APIRouter()


class PreviewRequest(BaseModel):
    path: str
    recursive: bool = False
    collection_id: int | None = None
    collection_type: str = "scan"


class ImportRequest(BaseModel):
    path: str
    recursive: bool = False
    mode: str = "copy"
    collection_id: int | None = None
    collection_type: str = "scan"


def _get_archive_path() -> Path:
    archive = get_archive_path()
    if not archive:
        raise HTTPException(status_code=400, detail="Archive path not configured")
    if not archive.exists():
        raise HTTPException(status_code=400, detail="Archive folder does not exist")
    return archive


@router.post("/import/preview")
async def import_preview(
    req: PreviewRequest,
    _user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    source = Path(req.path)
    if not source.exists():
        raise HTTPException(status_code=404, detail="Папка не найдена")
    if not source.is_dir():
        raise HTTPException(status_code=400, detail="Путь должен быть папкой")

    archive = _get_archive_path()

    validator = ScanValidator()

    pattern = "**/*" if req.recursive else "*"
    files = sorted(
        p for p in source.glob(pattern)
        if p.is_file() and p.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    )

    result = []
    for f in files:
        vr = validator.validate(f, collection_id=req.collection_id, collection_type=req.collection_type)
        dest_abs = str(archive / vr.dest) if vr.dest is not None else None
        result.append({
            "filename": f.name,
            "path": str(f),
            "status": "ok" if vr.valid else "invalid",
            "errors": vr.errors,
            "destination": dest_abs,
        })

    total = len(result)
    ok = sum(1 for r in result if r["status"] == "ok")

    return {
        "files": result,
        "summary": {"total": total, "ok": ok, "skipped": total - ok},
    }


@router.post("/import/start")
async def import_start(
    req: ImportRequest,
    _user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    source = Path(req.path)
    if not source.exists():
        raise HTTPException(status_code=404, detail="Папка не найдена")
    if not source.is_dir():
        raise HTTPException(status_code=400, detail="Путь должен быть папкой")

    archive = _get_archive_path()

    importer = ScanImporter()
    report = importer.run(
        source_path=source,
        archive_path=archive,
        collection_id=req.collection_id,
        collection_type=req.collection_type,
        recursive=req.recursive,
        copy_mode=(req.mode == "copy"),
    )

    return {
        "started_at": report.started_at.isoformat() if report.started_at else None,
        "finished_at": report.finished_at.isoformat() if report.finished_at else None,
        "total": report.total,
        "valid": report.valid,
        "succeeded": report.succeeded,
        "failed": report.failed,
        "results": [
            {
                "source": str(r.source),
                "destination": str(r.dest) if r.dest is not None else None,
                "valid": r.valid,
                "copied": r.copied,
                "errors": r.errors,
            }
            for r in report.results
        ],
    }
