from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
import structlog

from app.api.debs import role_dependency, db_dependency
from app.crud import (
    cleaner_collect_money,
    fetch_all_available_clenaers,
    get_cleaner_appointments,
)
from app.models import (
    AppointmentStatus,
    CollectMoneyModel,
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
async def post_collect_money(
    user: role_dependency[Roles.CLEANER, Roles.MANAGER],
    db: db_dependency,
    payload: CollectMoneyModel,
):
    result = await cleaner_collect_money(user.id, payload, db)
    return result
