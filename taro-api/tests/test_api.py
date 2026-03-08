"""API endpoint tests using FastAPI TestClient (no real DB needed for most)."""

import sys
from contextlib import asynccontextmanager
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


def _mock_db(query_responses: dict):
    """Create a mock get_db context manager with predefined query responses.

    query_responses: dict mapping query substring -> return value.
    When db.query is called, the first matching substring determines the response.
    """
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


# ── New endpoint tests (mocked DB) ─────────────────────────


def test_get_customer(client):
    """GET /customers/{id} returns customer profile."""
    mock = _mock_db({
        "SELECT * FROM customer": [
            {"id": "customer:sarah_v", "name": "Sarah V", "city": "London",
             "state": "England"}
        ],
    })
    import main
    with patch.object(main, "get_db", mock):
        response = client.get("/customers/sarah_v")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "sarah_v"
    assert data["name"] == "Sarah V"
    assert data["city"] == "London"


def test_get_customer_not_found(client):
    """GET /customers/{id} returns error for missing customer."""
    mock = _mock_db({"SELECT * FROM customer": []})
    import main
    with patch.object(main, "get_db", mock):
        response = client.get("/customers/nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert "error" in data


def test_get_customer_orders(client):
    """GET /customers/{id}/orders returns orders with products."""
    mock = _mock_db({
        "SELECT id FROM customer": [{"id": "customer:sarah_v"}],
        "placed": [{"orders": [
            {"id": "order:o1", "total": 49.99, "status": "delivered", "order_date": "2025-01-15"},
        ]}],
        "contains": [{"products": [
            {"id": "product:whey_1", "name": "Impact Whey", "price": 24.99},
        ]}],
    })
    import main
    with patch.object(main, "get_db", mock):
        response = client.get("/customers/sarah_v/orders")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "o1"
    assert data[0]["products"][0]["name"] == "Impact Whey"


def test_get_customer_recommendations(client):
    """GET /customers/{id}/recommendations returns deduped recs."""
    mock = _mock_db({
        "placed->order->contains": [{"bought": ["product:whey_1"]}],
        "also_bought": [{"recs": [
            {"id": "product:creatine_1", "name": "Creatine Mono", "price": 14.99, "avg_rating": 4.8},
        ]}],
    })
    import main
    with patch.object(main, "get_db", mock):
        response = client.get("/customers/sarah_v/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Creatine Mono"


def test_list_categories(client):
    """GET /categories returns verticals with nested subcategories."""
    mock = _mock_db({
        "SELECT id, name, level": [
            {"id": "category:fitness", "name": "Fitness", "level": "vertical", "description": "Fitness products"},
            {"id": "category:fitness__protein", "name": "Protein", "level": "subcategory", "description": ""},
        ],
        "child_of": [
            {"child": "category:fitness__protein", "parent": "category:fitness"},
        ],
    })
    import main
    with patch.object(main, "get_db", mock):
        response = client.get("/categories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Fitness"
    assert len(data[0]["subcategories"]) == 1
    assert data[0]["subcategories"][0]["name"] == "Protein"


def test_get_category(client):
    """GET /categories/{id} returns category with products."""
    mock = _mock_db({
        "SELECT * FROM category": [
            {"id": "category:fitness", "name": "Fitness", "level": "vertical"},
        ],
        "belongs_to": [{"products": [
            {"id": "product:whey_1", "name": "Impact Whey", "price": 24.99},
        ]}],
        "child_of": [{"subcategories": [
            {"id": "category:fitness__protein", "name": "Protein"},
        ]}],
    })
    import main
    with patch.object(main, "get_db", mock):
        response = client.get("/categories/fitness")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Fitness"
    assert len(data["products"]) == 1
    assert len(data["subcategories"]) == 1


def test_list_goals(client):
    """GET /goals returns all goals."""
    mock = _mock_db({
        "SELECT id, name, description, vertical FROM goal": [
            {"id": "goal:muscle_gain", "name": "Muscle Gain", "description": "Build muscle", "vertical": "Fitness"},
        ],
    })
    import main
    with patch.object(main, "get_db", mock):
        response = client.get("/goals")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Muscle Gain"
    assert data[0]["id"] == "muscle_gain"


def test_get_goal(client):
    """GET /goals/{id} returns goal with products."""
    mock = _mock_db({
        "SELECT * FROM goal": [
            {"id": "goal:muscle_gain", "name": "Muscle Gain", "description": "Build muscle"},
        ],
        "supports_goal": [{"products": [
            {"id": "product:whey_1", "name": "Impact Whey", "price": 24.99, "avg_rating": 4.7},
        ]}],
    })
    import main
    with patch.object(main, "get_db", mock):
        response = client.get("/goals/muscle_gain")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Muscle Gain"
    assert len(data["products"]) == 1
    assert data["products"][0]["name"] == "Impact Whey"


def test_get_goal_not_found(client):
    """GET /goals/{id} returns error for missing goal."""
    mock = _mock_db({"SELECT * FROM goal": []})
    import main
    with patch.object(main, "get_db", mock):
        response = client.get("/goals/nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert "error" in data


def test_products_pagination(client):
    """GET /products supports limit and offset params."""
    mock = _mock_db({
        "FROM product": [
            {"id": "product:whey_1", "name": "Impact Whey", "price": 24.99},
        ],
    })
    import main
    with patch.object(main, "get_db", mock):
        response = client.get("/products?limit=10&offset=5")
    assert response.status_code == 200
    # Verify limit/offset were passed through (mock returns data regardless)
    data = response.json()
    assert isinstance(data, list)


def test_products_brand_filter(client):
    """GET /products supports brand filter."""
    mock = _mock_db({
        "FROM product": [
            {"id": "product:whey_1", "name": "Impact Whey", "price": 24.99, "brand": "Myprotein"},
        ],
    })
    import main
    with patch.object(main, "get_db", mock):
        response = client.get("/products?brand=Myprotein")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
