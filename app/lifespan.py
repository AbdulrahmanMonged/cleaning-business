from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.cache import get_redis_pool
from app.core.db import get_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await get_redis_pool().disconnect()
    await get_engine().dispose()