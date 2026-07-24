import pytest_asyncio
from httpx import AsyncClient



TEST_USER = {"name": "test-123", "password": "test-123", "confirm_password": "test-123"}


@pytest_asyncio.fixture(loop_scope="session")
async def registered_user(client: AsyncClient) -> dict:
    response = await client.post("/v1/auth/register", json=TEST_USER)
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture(loop_scope="session")
async def auth_headers(client: AsyncClient, registered_user: dict) -> dict:
    response = await client.post(
        "/v1/auth/login",
        data={"username": TEST_USER["name"], "password": TEST_USER["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    return {"Authorization": f"{data['token_type']} {data['access_token']}"}


async def test_register(client: AsyncClient):
    from app.models import UserCreate
    valid_user = UserCreate(**TEST_USER)
    response = await client.post("/v1/auth/register", json=valid_user.model_dump())
    data = response.json()
    assert response.status_code == 201
    assert data["name"] == valid_user.name
    assert data["role"] == "user"


async def test_login_fails_with_wrong_password(client: AsyncClient, registered_user):
    response = await client.post(
        "/v1/auth/login",
        data={"username": TEST_USER["name"], "password": "wrong-password"},
    )
    data = response.json()
    assert response.status_code == 401
    assert data["message"] == "Could not validate credentials"


async def test_login_succeeds(client: AsyncClient, registered_user):
    response = await client.post(
        "/v1/auth/login",
        data={"username": TEST_USER["name"], "password": TEST_USER["password"]},
    )
    data = response.json()
    assert response.status_code == 200
    assert "access_token" in data
    assert "token_type" in data


async def test_me_requires_auth(client: AsyncClient):
    response = await client.get("/v1/auth/me")
    data = response.json()
    assert response.status_code == 401
    assert data["message"] == "Not authenticated"


async def test_me_returns_current_user(client: AsyncClient, auth_headers):
    response = await client.get("/v1/auth/me", headers=auth_headers)
    data = response.json()
    assert response.status_code == 200
    assert data["name"] == TEST_USER["name"]
    assert data["role"] == "user"