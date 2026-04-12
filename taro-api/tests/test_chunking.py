"""Tests for ingestion chunking helpers."""

from ingestion.chunking import chunk_markdown_policy, chunk_text


def test_chunk_markdown_policy_short_single_chunk():
    text = "# Returns\n\nYou may return within 30 days."
    assert chunk_markdown_policy(text) == [text]


def test_chunk_markdown_policy_splits_on_headings():
    text = """# Returns

Intro paragraph.

## Eligibility

Only unopened items.

## Refunds

Money back in 14 days."""
    # Whole doc must be longer than max_chars, or we keep a single chunk (correct for short policies).
    chunks = chunk_markdown_policy(text, max_chars=80)
    assert len(chunks) >= 3
    joined = "\n".join(chunks)
    assert "Eligibility" in joined and "Refunds" in joined


def test_chunk_markdown_policy_oversized_section_uses_chunk_text():
    long_body = "x" * 900
    text = f"# Title\n\n## Huge\n\n{long_body}"
    chunks = chunk_markdown_policy(text, max_chars=800, overlap=50)
    assert len(chunks) >= 2
    assert any("Huge" in c for c in chunks)


def test_chunk_markdown_no_internal_headings_matches_chunk_text():
    flat = "word " * 500
    assert chunk_markdown_policy(flat) == chunk_text(flat)
