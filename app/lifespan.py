from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.api.debs import get_db
from app.core.cache import get_redis_pool
from app.core.db import get_engine

from app.models import Roles, User
from app.core.config import get_settings


async def insert_admin_user(db: AsyncSession):
    settings = get_settings()
    try:
        admin_model = User(
            name=settings.ADMIN_USER, password=settings.ADMIN_PASSWORD, role=Roles.ADMIN
        )
        db.add(admin_model)
        await db.commit()
    except IntegrityError:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):

    session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    async with session_factory() as session:
        await insert_admin_user(session)

    yield
    await get_redis_pool().disconnect()
    await get_engine().dispose()
