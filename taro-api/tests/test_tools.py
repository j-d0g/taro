"""Unit tests for tool functions (mocked DB, no real connections)."""

import re

from tools.raw_query import BLOCKED_KEYWORDS


def test_raw_query_blocks_writes():
    """Verify the safety regex blocks all write operations."""
    dangerous = [
        "CREATE person SET name = 'x'",
        "UPDATE person SET name = 'x'",
        "DELETE person",
        "REMOVE TABLE person",
        "DEFINE TABLE person",
        "RELATE person:a->knows->person:b",
        "INSERT INTO person {name: 'x'}",
        "ALTER TABLE person",
        "DROP TABLE person",
        # Case variations
        "create person SET name = 'x'",
        "Delete person:123",
    ]
    for query in dangerous:
        assert BLOCKED_KEYWORDS.search(query), f"Should block: {query}"


def test_raw_query_allows_reads():
    """Verify the safety regex allows read operations."""
    safe = [
        "SELECT * FROM person",
        "SELECT count() FROM person GROUP ALL",
        "INFO FOR DB",
        "INFO FOR TABLE person",
        "SELECT * FROM person WHERE name = 'creative'",  # "creative" contains CREATE
    ]
    for query in safe:
        assert not BLOCKED_KEYWORDS.search(query), f"Should allow: {query}"


def test_hybrid_search_rrf_fusion():
    """Test the RRF fusion function directly."""
    from tools.hybrid_search import _rrf_fuse

    vec_results = [
        {"id": "doc:1", "title": "A", "vec_score": 0.9},
        {"id": "doc:2", "title": "B", "vec_score": 0.7},
    ]
    bm25_results = [
        {"id": "doc:2", "title": "B", "bm25_score": 5.0},
        {"id": "doc:3", "title": "C", "bm25_score": 3.0},
    ]

    fused = _rrf_fuse(vec_results, bm25_results)

    # doc:2 appears in both lists, should rank highest
    assert len(fused) == 3
    assert fused[0]["id"] == "doc:2"
    # All results should have rrf_score
    for doc in fused:
        assert "rrf_score" in doc
        assert doc["rrf_score"] > 0


def test_all_tools_are_async():
    """Verify all tools are async (coroutine functions)."""
    import asyncio
    from tools import ALL_TOOLS

    for tool in ALL_TOOLS:
        # LangChain tools wrap the function; check the underlying coroutine
        assert tool.coroutine is not None or asyncio.iscoroutinefunction(tool.func), \
            f"Tool {tool.name} should be async"


def test_all_tools_have_descriptions():
    """Verify all tools have non-empty descriptions."""
    from tools import ALL_TOOLS

    for tool in ALL_TOOLS:
        assert tool.description, f"Tool {tool.name} missing description"
        assert len(tool.description) > 20, f"Tool {tool.name} description too short"
