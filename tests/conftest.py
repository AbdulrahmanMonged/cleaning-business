import os

from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio
from sqlalchemy import make_url, text
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from alembic.config import Config
from alembic import command




def run_migrations(db_url: str):
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(config, "head")


@pytest.fixture(scope="session")
def service_urls():
    with (
        PostgresContainer(image="postgres:18.4-alpine", driver="asyncpg") as postgres,
        RedisContainer(image="redis:8.8-alpine") as redis,
    ):
        postgres_url = make_url(postgres.get_connection_url())
        redis_host = redis.get_container_host_ip()
        redis_port = redis.get_exposed_port(6379)
        os.environ["DB_HOST"] = str(postgres_url.host)
        os.environ["DB_USER"] = str(postgres_url.username)
        os.environ["DB_PASSWORD"] = str(postgres_url.password)
        os.environ["DB_PORT"] = str(postgres_url.port)
        os.environ["DB_NAME"] = str(postgres_url.database)

        os.environ["REDIS_HOST"] = str(redis_host)
        os.environ["REDIS_PORT"] = str(redis_port)

        redis_url = f"redis://{redis_host}:{redis_port}/0"

        database_url = postgres_url.render_as_string(hide_password=False)
        run_migrations(database_url)

        yield {"database_url": database_url, "redis": redis_url}


@pytest.fixture(scope="session")
def app(service_urls):
    from app.main import app

    yield app


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def client(app):
    async with LifespanManager(app) as manager:
        transport = ASGITransport(manager.app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as async_client:
            yield async_client

@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def _clean_db(client):
    yield
    from app.core.db import get_engine
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(
            text('TRUNCATE TABLE "user", "appointments" RESTART IDENTITY CASCADE')
        )