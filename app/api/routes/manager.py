from fastapi import APIRouter
import structlog

log = structlog.get_logger()
router = APIRouter(prefix="/manager", tags=["manager"])


@router.get("/test")
async def schedule_appointment():
    pass
