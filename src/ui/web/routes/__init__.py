from fastapi import APIRouter

from ui.web.routes import auth, config, daemons, setup

API_VERSION = "v1"

router = APIRouter(prefix=f"/api/{API_VERSION}")
router.include_router(setup.router)
router.include_router(auth.router)
router.include_router(config.router)
router.include_router(daemons.router)
