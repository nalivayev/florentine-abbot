from fastapi import APIRouter

from ui.web.routes import auth, collections, config, daemons, faces, imports, setup, upload, users

API_VERSION = "v1"

router = APIRouter(prefix=f"/api/{API_VERSION}")
router.include_router(setup.router)
router.include_router(auth.router)
router.include_router(config.router)
router.include_router(collections.router)
router.include_router(faces.router)
router.include_router(daemons.router)
router.include_router(upload.router)
router.include_router(users.router)
router.include_router(imports.router)
