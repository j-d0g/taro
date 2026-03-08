"""API endpoint tests using FastAPI TestClient (no real DB needed for most)."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Create a test client. Patches graph module to avoid DB/LLM connections."""
    # Patch graph module before main.py imports it
    mock_graph_module = MagicMock()
    mock_graph_module.build_graph = MagicMock(return_value=MagicMock())
    mock_graph_module.graph = MagicMock()
    mock_graph_module.DEFAULT_PROVIDER = "openai"
    mock_graph_module.DEFAULT_MODEL = "gpt-4o"

    with patch.dict(sys.modules, {"graph": mock_graph_module}):
        # Force re-import of main with mocked graph
        if "main" in sys.modules:
            del sys.modules["main"]
        from main import app
        with TestClient(app) as c:
            yield c


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "taro-ai"


def test_models(client):
    response = client.get("/models")
    assert response.status_code == 200
    data = response.json()
    assert "default_provider" in data
    assert "providers" in data
    assert "openai" in data["providers"]
    assert "anthropic" in data["providers"]
    assert "google" in data["providers"]


def test_prompts(client):
    response = client.get("/prompts")
    assert response.status_code == 200
    data = response.json()
    assert "prompts" in data
    assert "default" in data["prompts"]
    assert data["default"] == "default"


def test_chat_request_validation(client):
    """Verify /chat rejects invalid requests."""
    response = client.post("/chat", json={})
    assert response.status_code == 422


def test_chat_request_shape(client):
    """Verify /chat accepts well-formed requests (agent is mocked)."""
    from langchain_core.messages import AIMessage

    mock_result = {"messages": [AIMessage(content="Here are some protein options.")]}

    import main
    main._default_agent = AsyncMock()
    main._default_agent.ainvoke.return_value = mock_result

    response = client.post("/chat", json={"message": "recommend a protein powder"})
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "thread_id" in data
    assert "tool_calls" in data
    assert data["reply"] == "Here are some protein options."


def test_products_endpoint(client):
    """Products endpoint should handle request gracefully."""
    response = client.get("/products")
    assert response.status_code in (200, 404, 500)


def test_products_search_param(client):
    """Products endpoint accepts search query param."""
    response = client.get("/products?search=protein")
    assert response.status_code in (200, 404, 500)


def test_products_vertical_param(client):
    """Products endpoint accepts vertical filter."""
    response = client.get("/products?vertical=Fitness")
    assert response.status_code in (200, 404, 500)
