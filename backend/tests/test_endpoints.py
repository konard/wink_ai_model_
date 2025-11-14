import pytest
from io import BytesIO
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_upload_script_success(client: AsyncClient):
    files = {
        "file": ("test.txt", BytesIO(b"INT. OFFICE - DAY\n\nSarah types on computer."), "text/plain")
    }
    data = {"title": "Uploaded Script"}

    response = await client.post("/api/v1/scripts/upload", files=files, data=data)

    assert response.status_code == 201
    json_data = response.json()
    assert json_data["title"] == "Uploaded Script"
    assert json_data["id"] is not None


@pytest.mark.asyncio
async def test_upload_script_without_title(client: AsyncClient):
    files = {
        "file": ("script.txt", BytesIO(b"INT. ROOM - DAY\n\nJohn sits down."), "text/plain")
    }

    response = await client.post("/api/v1/scripts/upload", files=files)

    assert response.status_code == 201
    json_data = response.json()
    assert "script.txt" in json_data["title"]


@pytest.mark.asyncio
async def test_upload_script_invalid_extension(client: AsyncClient):
    files = {
        "file": ("test.exe", BytesIO(b"Some content"), "application/octet-stream")
    }

    response = await client.post("/api/v1/scripts/upload", files=files)

    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_script_too_large(client: AsyncClient):
    large_content = b"x" * (11 * 1024 * 1024)
    files = {
        "file": ("large.txt", BytesIO(large_content), "text/plain")
    }

    response = await client.post("/api/v1/scripts/upload", files=files)

    assert response.status_code == 413


@pytest.mark.asyncio
async def test_upload_script_invalid_encoding(client: AsyncClient):
    files = {
        "file": ("test.txt", BytesIO(b"\x80\x81\x82"), "text/plain")
    }

    response = await client.post("/api/v1/scripts/upload", files=files)

    assert response.status_code == 400
    assert "UTF-8" in response.json()["detail"]


@pytest.mark.asyncio
async def test_rate_script_sync(client: AsyncClient, sample_script):
    mock_result = {
        "predicted_rating": "12+",
        "agg_scores": {},
        "model_version": "v1.0",
        "total_scenes": 1,
        "top_trigger_scenes": [],
        "reasons": [],
    }

    with patch("app.services.script_service.ml_client") as mock_client:
        mock_client.rate_script = AsyncMock(return_value=mock_result)

        response = await client.post(
            f"/api/v1/scripts/{sample_script.id}/rate",
            params={"background": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["job_id"] == "sync"


@pytest.mark.asyncio
async def test_rate_script_background(client: AsyncClient, sample_script):
    with patch("app.api.endpoints.scripts.enqueue_rating_job") as mock_enqueue:
        mock_enqueue.return_value = "job-123"

        response = await client.post(
            f"/api/v1/scripts/{sample_script.id}/rate",
            params={"background": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert data["job_id"] == "job-123"


@pytest.mark.asyncio
async def test_rate_script_not_found(client: AsyncClient):
    response = await client.post("/api/v1/scripts/99999/rate")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_job_status(client: AsyncClient):
    with patch("app.api.endpoints.scripts.get_job_status") as mock_status:
        mock_status.return_value = {
            "job_id": "job-123",
            "status": "completed",
            "result": {"predicted_rating": "12+"},
            "error": None,
        }

        response = await client.get("/api/v1/scripts/jobs/job-123/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
