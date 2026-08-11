from fastapi import APIRouter, HTTPException, Path, status
import structlog
from app.api.debs import role_dependency, db_dependency
from app.crud import change_role, fetch_user_by_id
from app.models import ChangeUserRole, Roles, UserPublic

router = APIRouter(prefix="/admin", tags=["admin"])
log = structlog.get_logger()

@router.post("/{user_id}/change-role", response_model=UserPublic)
async def change_user_role(
    user: role_dependency[Roles.ADMIN],
    target_user: ChangeUserRole,
    db: db_dependency,
    user_id: int = Path(..., ge=0),
):
    updated_user = await change_role(
        user=user, target_user=target_user, db=db, user_id=user_id
    )
    if updated_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Could not find user"
        )
    return updated_user


@router.get("/{user_id}")
async def get_user_by_id(
    user_id: int, db: db_dependency, role: role_dependency[Roles.ADMIN] # pyright: ignore[reportGeneralTypeIssues]
):
    fetched_user = await fetch_user_by_id(user_id=user_id, db=db)
    return fetched_user.is_available
