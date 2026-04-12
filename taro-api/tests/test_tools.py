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


def test_surreal_select_rows_single_dict():
    """SDK may return one dict for a single-row SELECT; must not drop it."""
    from tools.fs_tools import _surreal_select_rows

    row = {"id": "documents:pol_x", "title": "Returns", "content": "...", "doc_type": "policy"}
    assert _surreal_select_rows(row) == [row]
    assert _surreal_select_rows([row]) == [row]
    assert _surreal_select_rows([]) == []


def test_surreal_select_rows_coerces_mapping():
    """Table scans may return Mapping/Record objects, not plain dicts."""
    from types import MappingProxyType

    from tools.fs_tools import _surreal_select_rows

    row = {"id": "documents:pol_x", "title": "Returns", "content": "...", "doc_type": "policy"}
    proxy = MappingProxyType(row)
    assert _surreal_select_rows([proxy]) == [row]
    assert _surreal_select_rows(proxy) == [row]


def test_surreal_select_rows_accepts_tuple_of_rows():
    """Surreal ``query()`` may return a tuple of row dicts instead of a list."""
    from tools.fs_tools import _surreal_select_rows

    a = {"id": "documents:pol_a", "doc_type": "policy"}
    b = {"id": "documents:pol_b", "doc_type": "policy"}
    assert _surreal_select_rows((a, b)) == [a, b]


def test_surreal_select_rows_unwraps_nested_list():
    """Rare SDK shape: ``[[row, row]]`` — normalize to flat list."""
    from tools.fs_tools import _surreal_select_rows

    a = {"id": "documents:pol_a", "doc_type": "policy"}
    b = {"id": "documents:pol_b", "doc_type": "policy"}
    assert _surreal_select_rows([[a, b]]) == [a, b]


def test_grep_content_preview_around_match():
    """Policy grep should show a window around the query, not only the first 150 chars."""
    from tools.fs_tools import _grep_content_preview

    long = "A" * 400 + " CMS demo line: proof." + "Z" * 200
    out = _grep_content_preview(long, "CMS demo line", max_len=120)
    assert "CMS demo line" in out
    assert "proof" in out


def test_rrf_fusion():
    """Test the RRF fusion function directly."""
    from tools.fs_tools import _rrf_fuse

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
