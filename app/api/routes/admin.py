from fastapi import APIRouter
import structlog
from app.api.debs import role_dependency, db_dependency
from app.crud import fetch_user_by_id
from app.models import Roles, UserPublic

router = APIRouter(prefix="/admin", tags=["admin"])
log = structlog.get_logger()


@router.get("/{user_id}", response_model=UserPublic)
async def get_user_by_id(
    user_id: int,
    db: db_dependency,
    role: role_dependency[Roles.ADMIN],  # pyright: ignore[reportGeneralTypeIssues]
):
    fetched_user = await fetch_user_by_id(user_id=user_id, db=db)
    return fetched_user
