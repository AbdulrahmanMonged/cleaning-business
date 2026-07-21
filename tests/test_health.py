from httpx import AsyncClient


async def test_health(client: AsyncClient):
    response = await client.get("/v1/health")
    assert response.status_code == 200
