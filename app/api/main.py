from fastapi import APIRouter

from app.models import HealthResponse


router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/health")
async def health_fun():
    return HealthResponse()
