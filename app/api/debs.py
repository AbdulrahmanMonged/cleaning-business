from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
import redis.asyncio as redis
from app.core.cache import get_redis_client
from app.core.config import get_settings
from app.core.db import get_sessionmaker
from app.models import TokenPayload, User


async def get_db(
    sessionmaker: async_sessionmaker[AsyncSession] = Depends(get_sessionmaker),
):
    async with sessionmaker() as db:
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise


db_dependency = Annotated[AsyncSession, Depends(get_db)]


def get_redis(client: redis.Redis = Depends(get_redis_client)):
    return client


cache_dependency = Annotated[redis.Redis, Depends(get_redis)]


reusable_oauth2_scheme = OAuth2PasswordBearer("/v1/login")

token_dependency = Annotated[str, Depends(reusable_oauth2_scheme)]


def get_current_user(session: db_dependency, token: token_dependency):
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except jwt.InvalidTokenError, ValidationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    user = session.get(User, ident=token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


user_dependency = Annotated[User, Depends(get_current_user)]
