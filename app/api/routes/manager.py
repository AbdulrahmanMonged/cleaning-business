from fastapi import APIRouter, Path, HTTPException, status
import structlog

from app.models import (
    ChangeUserRole,
    CollectedMoneyCleanerAppointmentResponse,
    CollectedMoneyResponse,
    Roles,
    UserPublic,
)
from app.api.debs import role_dependency, db_dependency
from app.crud import (
    change_role,
    fetch_cleaner_collected_money,
    fetch_cleaner_collected_money_appointment_view,
)

log = structlog.get_logger()
router = APIRouter(prefix="/manager", tags=["manager"])


@router.get("/test")
async def schedule_appointment():
    pass


@router.post("/{user_id}/change-role", response_model=UserPublic)
async def change_user_role(
    user: role_dependency[Roles.MANAGER],
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


@router.get(
    "/{cleaner_id}/get-cleaner-collected-money", response_model=CollectedMoneyResponse
)
async def get_cleaner_collected_money(
    user: role_dependency[Roles.MANAGER],
    db: db_dependency,
    cleaner_id: int = Path(ge=0),
):
    return CollectedMoneyResponse(
        sum_of_money=await fetch_cleaner_collected_money(cleaner_id, db)
    )


@router.get(
    "/{cleaner_id}/get-cleaner-appointment-collected-money",
    response_model=list[CollectedMoneyCleanerAppointmentResponse],
)
async def get_cleaner_appointmentment_collected_money(
    user: role_dependency[Roles.MANAGER], db: db_dependency, cleaner_id: int = Path(ge=0)
):
    return await fetch_cleaner_collected_money_appointment_view(cleaner_id, db)
