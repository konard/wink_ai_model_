import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    with patch("app.main.redis.Redis") as mock_redis:
        mock_instance = AsyncMock()
        mock_instance.ping = AsyncMock()
        mock_instance.close = AsyncMock()
        mock_redis.return_value = mock_instance

        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data


@pytest.mark.asyncio
async def test_create_script(client: AsyncClient):
    payload = {
        "title": "New Script",
        "content": "INT. OFFICE - DAY\n\nSarah types on her computer."
    }

    response = await client.post("/api/v1/scripts/", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["title"] == "New Script"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_list_scripts(client: AsyncClient, sample_script):
    response = await client.get("/api/v1/scripts/")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_script(client: AsyncClient, sample_script):
    response = await client.get(f"/api/v1/scripts/{sample_script.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == sample_script.id
    assert data["title"] == sample_script.title


@pytest.mark.asyncio
async def test_get_nonexistent_script(client: AsyncClient):
    response = await client.get("/api/v1/scripts/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_script_invalid_data(client: AsyncClient):
    payload = {
        "title": "",
        "content": "x"
    }

    response = await client.post("/api/v1/scripts/", json=payload)
    assert response.status_code == 422
