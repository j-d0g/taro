"""Unit tests for product preference endpoints (POST /preferences, GET /preferences/{user_id})."""

import sys
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Create a test client. Patches graph module to avoid DB/LLM connections."""
    mock_graph_module = MagicMock()
    mock_graph_module.build_graph = MagicMock(return_value=MagicMock())
    mock_graph_module.graph = MagicMock()
    mock_graph_module.DEFAULT_PROVIDER = "openai"
    mock_graph_module.DEFAULT_MODEL = "gpt-4o"

    with patch.dict(sys.modules, {"graph": mock_graph_module}):
        for mod in list(sys.modules):
            if mod in ("main", "agent", "helpers", "models") or mod.startswith("routes."):
                del sys.modules[mod]
        from main import app
        with TestClient(app) as c:
            yield c


def _mock_db(query_responses: dict):
    """Create a mock get_db context manager with predefined query responses."""
    mock_db = AsyncMock()

    async def mock_query(surql, params=None):
        for key, response in query_responses.items():
            if key in surql:
                return response
        return []

    mock_db.query = AsyncMock(side_effect=mock_query)

    @asynccontextmanager
    async def mock_get_db():
        yield mock_db

    return mock_get_db


def test_preference_cart(client):
    """POST /preferences with action=cart returns success."""
    mock = _mock_db({
        "DELETE": [],
        "RELATE": [{"id": "wants:abc"}],
    })
    import db
    with patch.object(db, "get_db", mock):
        response = client.post("/preferences", json={
            "user_id": "charlotte_gong",
            "product_id": "test_product_001",
            "action": "cart",
        })
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "cart"
    assert data["success"] is True


def test_preference_remove_with_reason(client):
    """POST /preferences with action=remove and reason returns success."""
    mock = _mock_db({
        "DELETE": [],
        "RELATE": [{"id": "rejected:abc"}],
    })
    import db
    with patch.object(db, "get_db", mock):
        response = client.post("/preferences", json={
            "user_id": "charlotte_gong",
            "product_id": "test_product_001",
            "action": "remove",
            "reason": "Too expensive",
        })
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "remove"
    assert data["success"] is True


def test_preference_invalid_action(client):
    """POST /preferences with invalid action returns error."""
    response = client.post("/preferences", json={
        "user_id": "charlotte_gong",
        "product_id": "test_product_001",
        "action": "invalid",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "error" in data


def test_get_preferences(client):
    """GET /preferences/{user_id} returns cart/saved/rejected lists."""
    mock = _mock_db({
        "wants": [{"products": [
            {"id": "product:serum_1", "name": "Retinol Serum", "price": 14.99, "image_url": ""},
        ]}],
        "interested_in": [{"products": [
            {"id": "product:cleanser_1", "name": "CeraVe Cleanser", "price": 11.50, "image_url": ""},
        ]}],
        "rejected": [{"products": [
            {"id": "product:toner_1", "name": "Harsh Toner", "price": 8.99},
        ]}],
    })
    import db
    with patch.object(db, "get_db", mock):
        response = client.get("/preferences/charlotte_gong")
    assert response.status_code == 200
    data = response.json()
    assert "cart" in data
    assert "saved" in data
    assert "rejected" in data
    assert len(data["cart"]) == 1
    assert data["cart"][0]["name"] == "Retinol Serum"
    assert len(data["saved"]) == 1
    assert data["saved"][0]["name"] == "CeraVe Cleanser"
    assert len(data["rejected"]) == 1
    assert data["rejected"][0]["name"] == "Harsh Toner"
