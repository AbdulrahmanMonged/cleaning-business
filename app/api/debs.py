from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
import redis.asyncio as redis
from app.core.cache import get_redis_client
from app.core.db import get_sessionmaker


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
