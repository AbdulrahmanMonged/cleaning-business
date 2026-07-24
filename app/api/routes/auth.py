from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import get_settings
from app.core.security import create_access_token
from app.crud import create_user, login_user
from app.models import TokenResponse, UserCreate, UserPublic
from app.api.debs import db_dependency, user_dependency

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: db_dependency):
    created_user = await create_user(user, db)
    return UserPublic(
        name=created_user.name, createdAt=created_user.createdAt, role=created_user.role
    )


@router.post("/login")
async def auth_user(
    db: db_dependency,
    form: OAuth2PasswordRequestForm = Depends(),
):
    settings = get_settings()
    logged_user = await login_user(form, db)
    if logged_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    jwt_token = create_access_token(
        logged_user.name, timedelta(minutes=settings.JWT_EXPIRATION_IN_MINUTES)
    )
    return TokenResponse(access_token=jwt_token)


@router.get("/me")
async def get_me(user: user_dependency):
    return UserPublic(name=user.name, role=user.role, createdAt=user.createdAt)
