from __future__ import annotations
from httpx import AsyncClient
import structlog

from app.models import Roles

logger = structlog.get_logger()

async def test_manager_basic_access(client: AsyncClient, auth_headers_map: dict):
    response = await client.post(
        "/v1/manager/7/change-role",
        headers=auth_headers_map["manager"],
        json={"target_role": "cleaner"},
    )
    json_resp = response.json()
    logger.info(json_resp=json_resp)
    assert response.status_code == 200
    assert json_resp["role"] == Roles.CLEANER.value


async def test_cleaner_access_manager(client: AsyncClient, auth_headers_map: dict):
    response = await client.post(
        "/v1/manager/7/change-role",
        headers=auth_headers_map["cleaner1"],
        json={"target_role": "cleaner"},
    )
    json_resp = response.json()
    logger.info(json_resp=json_resp)
    assert response.status_code == 403
    assert json_resp["message"] == "You're not allowed to access this endpoint"
