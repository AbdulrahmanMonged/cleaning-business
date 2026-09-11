import asyncio
import os

from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio
from sqlalchemy import make_url, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import structlog
from testcontainers.community.postgres import PostgresContainer
from testcontainers.community.redis import RedisContainer
from alembic.config import Config
from alembic import command

from app.models import Roles, User

MANAGER_API = "/v1/manager"
APPOINTMENTS_API = "/v1/appointments"
CLEANER_API = "/v1/cleaner"
CUSTOMER_API = "/v1/customer"
logger = structlog.get_logger()


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
        os.environ["TEST_ENV"] = str(True)
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


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def db_client(service_urls):
    engine = create_async_engine(service_urls["database_url"])
    factory_session = async_sessionmaker(engine, autoflush=False)
    async with factory_session() as session:
        yield session
    await engine.dispose()


USERS = {
    "manager": {"name": "manager", "password": "manager", "role": Roles.MANAGER},
    "customer1": {"name": "customer1", "password": "customer1", "role": Roles.CUSTOMER},
    "customer2": {"name": "customer2", "password": "customer2", "role": Roles.CUSTOMER},
    "cleaner1": {"name": "cleaner1", "password": "cleaner1", "role": Roles.CLEANER},
    "cleaner2": {"name": "cleaner2", "password": "cleaner2", "role": Roles.CLEANER},
    "admin": {"name": "admin", "password": "admin", "role": Roles.ADMIN},
    "user": {"name": "user", "password": "user", "role": Roles.USER},
}


async def bulk_insert_users(db_client: AsyncSession, users):
    serialized_users = [User(**USERS[data]) for data in USERS]
    db_client.add_all(serialized_users)
    await db_client.commit()


async def bulk_register_async(db_client: AsyncSession):
    global USERS

    await bulk_insert_users(db_client, USERS)

    all_users = (
        (
            await db_client.execute(
                select(User.name, User.role, User.id).order_by(User.id)
            )
        )
        .mappings()
        .all()
    )
    for item in all_users:
        USERS[item.name]["id"] = item.id

    assert all(
        (
            all_users[i].name == USERS[all_users[i].name]["name"]
            and all_users[i].role == USERS[all_users[i].name]["role"]
        )
        for i in range(len(all_users))
    )
    logger.info(users=USERS)


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def auth_headers_map(client: AsyncClient, db_client: AsyncSession):
    await bulk_register_async(db_client)
    headers_map = {}

    async def login_and_store(client: AsyncClient, user):
        response = await client.post(
            "/v1/auth/login",
            data={"username": user["name"], "password": user["password"]},
        )
        assert response.status_code == 200
        data = response.json()
        headers_map[user["name"]] = {
            "Authorization": f"{data['token_type']} {data['access_token']}"
        }

    tasks = [login_and_store(client, USERS[user]) for user in USERS]
    await asyncio.gather(*tasks)

    return headers_map


@pytest_asyncio.fixture(autouse=True, scope="module", loop_scope="session")
async def _clean_db(db_client: AsyncSession):
    yield
    await db_client.execute(
        text('TRUNCATE TABLE "appointments" RESTART IDENTITY CASCADE')
    )
    await db_client.commit()
