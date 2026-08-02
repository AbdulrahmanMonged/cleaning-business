from fastapi import APIRouter, Path, Query
from app.api.debs import role_dependency, db_dependency
from app.crud import (
    assign_cleaner_to_appointment,
    fetch_all_appointments_by_status,
    fetch_appointment_by_id,
    insert_appointment,
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

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("")
async def create_appointment(
    appointment: AppointmentCreateModel,
    user: role_dependency[Roles.CUSTOMER],
    db: db_dependency,
):
    created_appointment = await insert_appointment(
        appointment=appointment, user=user, db=db
    )
    return AppointmentPublic.model_validate(created_appointment)


@router.get("", response_model=list[AppointmentPublic])
async def get_all_appointments_by_status(
    user: role_dependency[Roles.CUSTOMER],
    db: db_dependency,
    status: AppointmentStatus = Query(None),
):
    results = await fetch_all_appointments_by_status(db, status)
    return results


@router.get("/{appointment_id}")
async def get_appointment_by_id(
    user: role_dependency[Roles.CUSTOMER],
    db: db_dependency,
    appointment_id: int = Path(..., ge=0),
):
    selected_appointment = await fetch_appointment_by_id(appointment_id, db)
    return AppointmentPublic.model_validate(selected_appointment)


@router.put("/{appointment_id}/update-status")
async def modify_appointment_status(
    user: role_dependency[Roles.MANAGER],
    db: db_dependency,
    payload: UpdateAppointmentStatus,
    appointment_id: int = Path(..., ge=0),
):
    modified_appointmenet = await update_appointment_status(payload, appointment_id, db)
    return AppointmentPublic.model_validate(modified_appointmenet)


@router.post("/{appointment_id}/assign-cleaner")
async def assign_cleaner(
    appointment_id: int,
    db: db_dependency,
    role: role_dependency[Roles.MANAGER],
    payload: AssignCleanerModel,
):
    updated_appointment = await assign_cleaner_to_appointment(
        appointment_id, payload, db
    )
    return AppointmentPublic.model_validate(updated_appointment)
