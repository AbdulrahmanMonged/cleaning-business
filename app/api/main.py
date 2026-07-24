from fastapi import APIRouter

from app.api.routes import auth
from app.models import HealthResponse


router = APIRouter(prefix="/v1", tags=["v1"])
router.include_router(auth.router)


@router.get("/health")
async def health_fun():
    return HealthResponse()
