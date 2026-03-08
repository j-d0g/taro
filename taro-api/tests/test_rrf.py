"""Tests for Reciprocal Rank Fusion logic."""
from tools.hybrid_search import _rrf_fuse


def test_rrf_fuse_basic():
    """Two lists with overlapping docs should merge and rank by combined score."""
    vec = [{"id": "a", "vec_score": 0.9}, {"id": "b", "vec_score": 0.7}]
    bm25 = [{"id": "b", "bm25_score": 3.0}, {"id": "c", "bm25_score": 1.5}]
    result = _rrf_fuse(vec, bm25)
    assert result[0]["id"] == "b"
    assert len(result) == 3


def test_rrf_fuse_empty_lists():
    assert _rrf_fuse([], []) == []


def test_rrf_fuse_single_list():
    vec = [{"id": "a"}, {"id": "b"}]
    result = _rrf_fuse(vec, [])
    assert len(result) == 2
    assert result[0]["id"] == "a"


def test_rrf_fuse_scores_decrease():
    """RRF scores should decrease with rank."""
    vec = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    result = _rrf_fuse(vec, [])
    scores = [r["rrf_score"] for r in result]
    assert scores == sorted(scores, reverse=True)
