"""Tests for raw_query tool's write-blocking regex."""
import pytest
from tools.raw_query import BLOCKED_KEYWORDS


@pytest.mark.parametrize("query", [
    "CREATE user SET name = 'x'",
    "DELETE product:123",
    "UPDATE product SET price = 0",
    "REMOVE TABLE users",
    "INSERT INTO products",
    "DEFINE TABLE test",
    "ALTER TABLE test",
    "DROP TABLE test",
    "RELATE user:1->bought->product:2",
])
def test_blocked_keywords_reject(query):
    assert BLOCKED_KEYWORDS.search(query) is not None


@pytest.mark.parametrize("query", [
    "SELECT * FROM product",
    "SELECT count() FROM documents GROUP ALL",
    "INFO FOR DB",
    "INFO FOR TABLE product",
])
def test_blocked_keywords_allow(query):
    assert BLOCKED_KEYWORDS.search(query) is None
