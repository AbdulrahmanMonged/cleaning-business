from fastapi import APIRouter, Path, Query, status
import structlog
from app.api.debs import role_dependency, db_dependency
from app.crud import (
    fetch_all_appointments_by_status,
    fetch_appointment_by_id,
    insert_appointment,
)
from app.models import (
    AppointmentCreateModel,
    AppointmentPublic,
    AppointmentStatus,
    Roles,
)

log = structlog.get_logger()
router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentPublic, status_code=status.HTTP_201_CREATED)
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
