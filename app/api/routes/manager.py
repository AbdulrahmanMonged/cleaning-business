from fastapi import APIRouter, Path, HTTPException, status
import structlog

from app.models import (
    AppointmentPublic,
    AssignCleanerModel,
    ChangeUserRole,
    CollectMoneyModel,
    CollectedMoneyCleanerAppointmentResponse,
    CollectedMoneyResponse,
    Roles,
    UpdateAppointmentStatus,
    UserPublic,
)
from app.api.debs import role_dependency, db_dependency
from app.crud import (
    assign_cleaner_to_appointment,
    change_role,
    collect_money,
    fetch_all_available_cleaners,
    fetch_cleaner_collected_money,
    fetch_cleaner_collected_money_appointment_view,
    trigger_is_recurred,
    update_appointment_status,
)

log = structlog.get_logger()
router = APIRouter(prefix="/manager", tags=["manager"])


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
async def get_cleaner_appointment_collected_money(
    user: role_dependency[Roles.MANAGER],
    db: db_dependency,
    cleaner_id: int = Path(ge=0),
):
    return await fetch_cleaner_collected_money_appointment_view(cleaner_id, db)


@router.post("/collect-money", response_model=AppointmentPublic)
async def manager_collect_money(
    user: role_dependency[Roles.MANAGER], payload: CollectMoneyModel, db: db_dependency
):
    result = await collect_money(payload=payload, db=db)
    return result


@router.post("/{appointment_id}/assign-cleaner", response_model=AppointmentPublic)
async def assign_cleaner(
    appointment_id: int,
    db: db_dependency,
    role: role_dependency[Roles.MANAGER],
    payload: AssignCleanerModel,
):
    return await assign_cleaner_to_appointment(appointment_id, payload, db)

@router.put("/{appointment_id}/update-status", response_model=AppointmentPublic)
async def modify_appointment_status(
    user: role_dependency[Roles.MANAGER],
    db: db_dependency,
    payload: UpdateAppointmentStatus,
    appointment_id: int = Path(..., ge=0),
):

    return await update_appointment_status(payload, appointment_id, db)


@router.post("/{appointment_id}/recurred", response_model=AppointmentPublic)
async def trigger_recurred_appointment(
    appointment_id: int, db: db_dependency, user: role_dependency[Roles.MANAGER]
):
    return await trigger_is_recurred(appointment_id, db=db)


@router.get("/available-cleaners", response_model=list[UserPublic])
async def get_available_cleaners(
    db: db_dependency, role: role_dependency[Roles.MANAGER]
):
    available_cleaners = await fetch_all_available_cleaners(db)
    return available_cleaners
