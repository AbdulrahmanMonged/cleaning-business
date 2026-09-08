from __future__ import annotations

from fastapi import APIRouter, HTTPException, Path, status
import structlog

from app.api.debs import role_dependency, db_dependency
from app.crud import (
    collect_money,
    fetch_all_available_clenaers,
    get_cleaner_appointments,
    update_appointment_status,
)
from app.models import (
    AppointmentStatus,
    CollectMoneyModel,
    RelatedAppointmentPublic,
    Roles,
    UpdateAppointmentStatus,
    UserPublic,
)

logger = structlog.get_logger()
router = APIRouter(
    prefix="/cleaner",
    tags=["cleaner"],
)


@router.get("/tasks", response_model=list[RelatedAppointmentPublic])
async def get_assigned_cleaning_tasks(
    user: role_dependency[Roles.CLEANER], db: db_dependency
):

    return await get_cleaner_appointments(user.id, db, AppointmentStatus.ASSIGNED)


@router.get("/related-appointments", response_model=list[RelatedAppointmentPublic])
async def get_all_related_appointments(
    user: role_dependency[Roles.CLEANER], db: db_dependency
):
    return await get_cleaner_appointments(user.id, db=db)


@router.post("/collect-money", response_model=RelatedAppointmentPublic)
async def cleaner_post_collect_money(
    user: role_dependency[Roles.CLEANER],
    db: db_dependency,
    payload: CollectMoneyModel,
):
    result = await collect_money(cleaner_id=user.id, payload=payload, db=db)
    return result


@router.post(
    "/{appointment_id}/start-appointment", response_model=RelatedAppointmentPublic
)
async def cleaner_cancel_appointment(
    user: role_dependency[Roles.CLEANER],
    db: db_dependency,
    appointment_id: int = Path(ge=0),
):
    payload = UpdateAppointmentStatus(new_status=AppointmentStatus.IN_PROGRESS)
    result = await update_appointment_status(
        payload, appointment_id, db, cleaner_id=user.id
    )
    return result
