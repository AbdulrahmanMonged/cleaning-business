from __future__ import annotations

from fastapi import APIRouter

from app.api.debs import role_dependency, db_dependency
from app.crud import fetch_all_available_clenaers
from app.models import Roles, UserPublic

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
