"""Tests for the SSE streaming chat endpoint."""

import json
import sys
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Create a test client with mocked graph module."""
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


def test_stream_endpoint_exists(client):
    """POST /chat/stream returns 200, not 404."""
    # Mock agent with astream_events
    import agent

    async def mock_astream_events(input_msg, config, version="v2"):
        # Simulate: tool_start -> tool_end -> llm stream -> end
        yield {
            "event": "on_tool_start",
            "name": "find",
            "run_id": "run-1",
            "data": {"input": {"query": "moisturizer"}},
        }
        yield {
            "event": "on_tool_end",
            "name": "find",
            "run_id": "run-1",
            "data": {"output": "Found 3 products"},
        }
        yield {
            "event": "on_chat_model_stream",
            "name": "ChatOpenAI",
            "run_id": "run-2",
            "data": {"chunk": MagicMock(content="Here are ", tool_call_chunks=[])},
        }
        yield {
            "event": "on_chat_model_stream",
            "name": "ChatOpenAI",
            "run_id": "run-2",
            "data": {"chunk": MagicMock(content="some results.", tool_call_chunks=[])},
        }

    mock_agent = MagicMock()
    mock_agent.astream_events = mock_astream_events
    agent._default_agent = mock_agent

    response = client.post(
        "/chat/stream",
        json={"message": "recommend a moisturizer"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")


def test_stream_emits_sse_events(client):
    """SSE stream contains tool_start, tool_end, token, and done events."""
    import agent

    async def mock_astream_events(input_msg, config, version="v2"):
        yield {
            "event": "on_tool_start",
            "name": "find",
            "run_id": "run-1",
            "data": {"input": {"query": "moisturizer"}},
        }
        yield {
            "event": "on_tool_end",
            "name": "find",
            "run_id": "run-1",
            "data": {"output": "Found 3 products"},
        }
        yield {
            "event": "on_chat_model_stream",
            "name": "ChatOpenAI",
            "run_id": "run-2",
            "data": {"chunk": MagicMock(content="Great choice!", tool_call_chunks=[])},
        }

    mock_agent = MagicMock()
    mock_agent.astream_events = mock_astream_events
    agent._default_agent = mock_agent

    response = client.post(
        "/chat/stream",
        json={"message": "recommend a moisturizer"},
    )
    body = response.text

    # Parse SSE events
    events = []
    for block in body.strip().split("\n\n"):
        lines = block.strip().split("\n")
        event_type = None
        data = None
        for line in lines:
            if line.startswith("event: "):
                event_type = line[7:]
            elif line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                except json.JSONDecodeError:
                    pass
        if event_type and data:
            events.append({"event": event_type, "data": data})

    event_types = [e["event"] for e in events]
    assert "tool_start" in event_types
    assert "tool_end" in event_types
    assert "token" in event_types
    assert "done" in event_types


def test_stream_request_validation(client):
    """POST /chat/stream rejects invalid request body."""
    response = client.post("/chat/stream", json={})
    assert response.status_code == 422


def test_stream_with_user_id(client):
    """Streaming endpoint injects user context when user_id is provided."""
    import agent

    captured_input = {}

    async def mock_astream_events(input_msg, config, version="v2"):
        captured_input["messages"] = input_msg["messages"]
        yield {
            "event": "on_chat_model_stream",
            "name": "ChatOpenAI",
            "run_id": "run-1",
            "data": {"chunk": MagicMock(content="Hello!", tool_call_chunks=[])},
        }

    mock_agent = MagicMock()
    mock_agent.astream_events = mock_astream_events
    agent._default_agent = mock_agent

    # Mock DB to return a customer
    mock_db = AsyncMock()
    mock_db.query = AsyncMock(return_value=[{
        "id": "customer:charlotte_gong",
        "name": "Charlotte Gong",
        "skin_type": "combination",
        "concerns": ["dryness", "sensitivity"],
    }])

    @asynccontextmanager
    async def mock_get_db():
        yield mock_db

    import db
    with patch.object(db, "get_db", mock_get_db):
        response = client.post(
            "/chat/stream",
            json={"message": "hi", "user_id": "charlotte_gong"},
        )

    assert response.status_code == 200
    # Verify user context was injected into the message
    msg_content = captured_input["messages"][0].content
    assert "Charlotte Gong" in msg_content
    assert "combination" in msg_content


def test_stream_error_handling(client):
    """Stream emits error event on agent failure."""
    import agent

    async def mock_astream_events(input_msg, config, version="v2"):
        raise RuntimeError("LLM connection failed")
        yield  # Make it a generator

    mock_agent = MagicMock()
    mock_agent.astream_events = mock_astream_events
    agent._default_agent = mock_agent

    response = client.post(
        "/chat/stream",
        json={"message": "hello"},
    )
    assert response.status_code == 200
    body = response.text
    assert "error" in body
    assert "done" in body  # Always ends with done


def test_stream_multiple_tools(client):
    """Stream handles multiple sequential tool calls."""
    import agent

    async def mock_astream_events(input_msg, config, version="v2"):
        for i, tool_name in enumerate(["find", "cat", "grep"]):
            yield {
                "event": "on_tool_start",
                "name": tool_name,
                "run_id": f"run-{i}",
                "data": {"input": {"query": f"test-{i}"}},
            }
            yield {
                "event": "on_tool_end",
                "name": tool_name,
                "run_id": f"run-{i}",
                "data": {"output": f"Result {i}"},
            }
        yield {
            "event": "on_chat_model_stream",
            "name": "ChatOpenAI",
            "run_id": "run-final",
            "data": {"chunk": MagicMock(content="Done!", tool_call_chunks=[])},
        }

    mock_agent = MagicMock()
    mock_agent.astream_events = mock_astream_events
    agent._default_agent = mock_agent

    response = client.post(
        "/chat/stream",
        json={"message": "test multiple tools"},
    )
    body = response.text

    # Count tool_start events
    assert body.count("event: tool_start") == 3
    assert body.count("event: tool_end") == 3
    assert "event: token" in body
    assert "event: done" in body


def test_stream_product_extraction(client):
    """Stream extracts product IDs from tool output '→ /products/{id}' pattern."""
    import agent

    # Tool output uses the standard → /products/{id} format (same as find/grep/graph_traverse)
    tool_output = (
        "find 'moisturizer' (1 results, from 3 vector + 2 keyword):\n"
        "\n"
        "  Hydrating Face Cream (rrf: 0.0909, vec: 0.842, bm25: 0.85, type: product)\n"
        "    → /products/abc123def456\n"
        "    A rich moisturizer for dry skin..."
    )

    async def mock_astream_events(input_msg, config, version="v2"):
        yield {
            "event": "on_tool_start",
            "name": "find",
            "run_id": "run-1",
            "data": {"input": {"query": "moisturizer"}},
        }
        yield {
            "event": "on_tool_end",
            "name": "find",
            "run_id": "run-1",
            "data": {"output": tool_output},
        }
        yield {
            "event": "on_chat_model_stream",
            "name": "ChatOpenAI",
            "run_id": "run-2",
            "data": {"chunk": MagicMock(content="Here you go!", tool_call_chunks=[])},
        }

    mock_agent = MagicMock()
    mock_agent.astream_events = mock_astream_events
    agent._default_agent = mock_agent

    # Mock DB to return product details when fetched
    mock_db = AsyncMock()
    mock_db.query = AsyncMock(return_value=[{
        "id": "product:abc123def456",
        "name": "Test Moisturizer",
        "price": 14.99,
        "avg_rating": 4.5,
        "image_url": "",
        "vertical": "Skincare",
        "subcategory": "Moisturisers",
    }])

    @asynccontextmanager
    async def mock_get_db():
        yield mock_db

    import db
    with patch.object(db, "get_db", mock_get_db):
        response = client.post(
            "/chat/stream",
            json={"message": "recommend a moisturizer"},
        )
    body = response.text

    # Find the done event and parse its data
    for block in body.strip().split("\n\n"):
        lines = block.strip().split("\n")
        event_type = None
        data = None
        for line in lines:
            if line.startswith("event: "):
                event_type = line[7:]
            elif line.startswith("data: "):
                data = json.loads(line[6:])
        if event_type == "done":
            assert len(data["products"]) == 1
            assert data["products"][0]["name"] == "Test Moisturizer"
            assert data["products"][0]["price"] == 14.99
            break
    else:
        pytest.fail("No 'done' event found in SSE stream")
