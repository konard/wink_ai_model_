import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model_version" in data


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "endpoints" in data


def test_rate_script_valid(client):
    payload = {
        "text": "INT. HOUSE - DAY\n\nJohn enters the room and sits down.",
        "script_id": "test_script_1"
    }

    response = client.post("/rate_script", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["script_id"] == "test_script_1"
    assert data["predicted_rating"] in ["6+", "12+", "16+", "18+"]
    assert "top_trigger_scenes" in data
    assert "agg_scores" in data


def test_rate_script_invalid_empty_text(client):
    payload = {
        "text": "",
        "script_id": "test_script_2"
    }

    response = client.post("/rate_script", json=payload)
    assert response.status_code == 422


def test_rate_script_without_script_id(client):
    payload = {
        "text": "INT. OFFICE - DAY\n\nSarah types on her computer."
    }

    response = client.post("/rate_script", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["script_id"] is None
    assert data["predicted_rating"] in ["6+", "12+", "16+", "18+"]
