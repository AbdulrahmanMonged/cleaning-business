from functools import lru_cache

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


@lru_cache
def get_engine():
    settings = get_settings()
    return create_async_engine(
        settings.DB_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=1800,
        echo=False,
    )


@lru_cache
def get_sessionmaker():
    return async_sessionmaker(
        get_engine(),
        expire_on_commit=False,
    )


class Base(DeclarativeBase):
    pass
