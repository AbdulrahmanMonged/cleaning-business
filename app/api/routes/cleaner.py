from __future__ import annotations

from fastapi import APIRouter
import structlog

from app.api.debs import role_dependency, db_dependency
from app.crud import fetch_all_available_clenaers, get_cleaner_appointments, update_appointment_status
from app.models import (
    RelatedAppointmentPublic,
    Roles,
    UserPublic,
)
log = structlog.get_logger()
router = APIRouter(
    prefix="/cleaner",
    tags=["cleaner"],
)


@router.get("")
async def test_cleaner(
    user: role_dependency[Roles.CLEANER,],
):
    return UserPublic.model_validate(user)


@router.get("/available-cleaners", response_model=list[UserPublic])
async def get_available_cleaners(
    db: db_dependency, role: role_dependency[Roles.MANAGER]
):
    available_cleaners = await fetch_all_available_clenaers(db)
    return available_cleaners


@router.get("/tasks", response_model=list[RelatedAppointmentPublic])
async def get_assigned_cleaning_tasks(user: role_dependency[Roles.CLEANER], db: db_dependency):
    return await get_cleaner_appointments(user.id, db)
