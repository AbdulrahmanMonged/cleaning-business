from fastapi import APIRouter, Path, Query
import structlog
from app.api.debs import role_dependency, db_dependency
from app.crud import (
    assign_cleaner_to_appointment,
    fetch_all_appointments_by_status,
    fetch_appointment_by_id,
    insert_appointment,
    trigger_is_recurred,
    update_appointment_status,
)
from app.models import (
    AppointmentCreateModel,
    AppointmentPublic,
    AppointmentStatus,
    AssignCleanerModel,
    Roles,
    UpdateAppointmentStatus,
)

log = structlog.get_logger()
router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentPublic)
async def create_appointment(
    appointment: AppointmentCreateModel,
    user: role_dependency[Roles.CUSTOMER],
    db: db_dependency,
):
    return await insert_appointment(appointment=appointment, user=user, db=db)


@router.get("", response_model=list[AppointmentPublic])
async def get_all_appointments_by_status(
    user: role_dependency[Roles.CUSTOMER, Roles.MANAGER],
    db: db_dependency,
    status: AppointmentStatus = Query(None),
):
    return await fetch_all_appointments_by_status(db, status)


@router.get("/{appointment_id}", response_model=AppointmentPublic)
async def get_appointment_by_id(
    user: role_dependency[Roles.CUSTOMER, Roles.MANAGER],
    db: db_dependency,
    appointment_id: int = Path(..., ge=0),
):
    return await fetch_appointment_by_id(appointment_id, db)


@router.put("/{appointment_id}/update-status", response_model=AppointmentPublic)
async def modify_appointment_status(
    user: role_dependency[Roles.MANAGER],
    db: db_dependency,
    payload: UpdateAppointmentStatus,
    appointment_id: int = Path(..., ge=0),
):

    return await update_appointment_status(payload, appointment_id, db)


@router.post("/{appointment_id}/assign-cleaner", response_model=AppointmentPublic)
async def assign_cleaner(
    appointment_id: int,
    db: db_dependency,
    role: role_dependency[Roles.MANAGER],
    payload: AssignCleanerModel,
):
    return await assign_cleaner_to_appointment(appointment_id, payload, db)


@router.post("/{appointment_id}/recurred", response_model=AppointmentPublic)
async def trigger_recurred_appointment(
    appointment_id: int, db: db_dependency, user: role_dependency[Roles.MANAGER]
):
    return await trigger_is_recurred(appointment_id, db=db)
