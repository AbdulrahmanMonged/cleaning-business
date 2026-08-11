from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
import structlog
from app.core.cache import get_redis_pool
from app.core.db import get_engine

from app.models import Roles, User
from app.core.config import Settings, get_settings

log = structlog.get_logger()
async def insert_admin_user(db: AsyncSession, settings: Settings):
    try:
        admin_model = User(
            id=1,
            name=settings.ADMIN_USER,
            password=settings.ADMIN_PASSWORD,
            role=Roles.ADMIN,
        )
        cleaner_model = User(
            id=3, name="cleaner", password="cleaner", role=Roles.CLEANER
        )
        manager_model = User(
            id=2, name="manager", password="manager", role=Roles.MANAGER
        )
        customer_model = User(
            id=4, name="customer", password="customer", role=Roles.CUSTOMER
        )
        normal_user_model = User(id=5, name="user", password="user", role=Roles.USER)
        db.add_all(
            [
                admin_model,
                manager_model,
                cleaner_model,
                customer_model,
                normal_user_model,
            ]
        )

        await db.commit()
    except IntegrityError:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.ENV == "development":
        session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
        async with session_factory() as session:
            await insert_admin_user(session, settings)

    yield
    await get_redis_pool().disconnect()
    await get_engine().dispose()
