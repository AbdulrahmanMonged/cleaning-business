from fastapi import APIRouter
import structlog

from app.api.routes import admin, appointments, auth, cleaner, manager
from app.models import HealthResponse
log = structlog.get_logger()
router = APIRouter(prefix="/v1", tags=["v1"])
router.include_router(auth.router)
router.include_router(cleaner.router)
router.include_router(admin.router)
router.include_router(appointments.router)
router.include_router(manager.router)

@router.get("/health")
async def health_fun():
    return HealthResponse()
