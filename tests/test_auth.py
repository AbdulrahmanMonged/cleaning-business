from httpx import AsyncClient
import structlog

logger = structlog.get_logger()
TEST_USER = {
    "name": "test_user123",
    "password": "test_user",
    "confirm_password": "test_user",
}


async def test_register(client: AsyncClient, auth_headers_map):
    response = await client.post("/v1/auth/register", json=TEST_USER)
    data = response.json()
    logger.warn(register_response=data)
    assert response.status_code == 201


async def test_login_fails_with_wrong_password(client: AsyncClient):
    response = await client.post(
        "/v1/auth/login",
        data={"username": TEST_USER["name"], "password": "wrong-password"},
    )
    data = response.json()
    assert response.status_code == 401
    assert data["message"] == "Could not validate credentials"


async def test_login_succeeds(client: AsyncClient):
    response = await client.post(
        "/v1/auth/login",
        data={"username": TEST_USER["name"], "password": TEST_USER["password"]},
    )
    data = response.json()
    assert response.status_code == 200
    assert "access_token" in data
    assert "token_type" in data


async def test_me_requires_auth(client: AsyncClient):
    response = await client.get(
        "/v1/auth/me",
        headers={
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODg1MjI1ODIsInN1YiI6ImFkbWluIn0.Onx9ZGgEW_MqrBzdJgUdCwPtSg586fXPDlXJzNwLB68"
        },
    )
    data = response.json()
    assert response.status_code == 401
    assert data["message"] == "Could not validate credentials"


async def test_me_returns_current_user(client: AsyncClient, auth_headers_map: dict):
    admin_user = {"name": "admin", "role": "admin"}
    response = await client.get(
        "/v1/auth/me", headers=auth_headers_map[admin_user["name"]]
    )
    data = response.json()
    assert response.status_code == 200
    assert data["name"] == admin_user["name"]
    assert data["role"] == admin_user["role"]
