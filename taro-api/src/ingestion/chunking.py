"""Split markdown/text into overlapping chunks."""

from __future__ import annotations

import re

# ATX headings at line start (# … ###) — split policy docs by section before size limits.
_HEADING_SPLIT = re.compile(r"(?m)(?=\n#{1,3}\s)")


def chunk_text(text: str, max_chars: int = 800, overlap: int = 100) -> list[str]:
    """Split text into chunks with overlap. Tries paragraph boundaries first."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        piece = text[start:end]
        if end < len(text):
            # Prefer breaking at last newline in window
            nl = piece.rfind("\n\n")
            if nl > max_chars // 4:
                piece = piece[:nl].strip()
                end = start + nl
            else:
                sp = piece.rfind(" ")
                if sp > max_chars // 4:
                    piece = piece[:sp].strip()
                    end = start + sp
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks


def chunk_markdown_policy(text: str, max_chars: int = 800, overlap: int = 100) -> list[str]:
    """Chunk policy/help markdown: split on ``##`` / ``###`` (and top-level ``#`` blocks) first, then size-limit.

    Keeps sections intact when they fit in ``max_chars``, so retrieval tends to return a whole
    subsection instead of cutting mid-paragraph. Falls back to :func:`chunk_text` when there are
    no internal headings or a section is still too long.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    # No secondary headings → same sliding window as generic text
    if not _HEADING_SPLIT.search(text):
        return chunk_text(text, max_chars=max_chars, overlap=overlap)

    sections = [s.strip() for s in _HEADING_SPLIT.split(text) if s.strip()]
    if len(sections) <= 1:
        return chunk_text(text, max_chars=max_chars, overlap=overlap)

    out: list[str] = []
    for sec in sections:
        if len(sec) <= max_chars:
            out.append(sec)
        else:
            out.extend(chunk_text(sec, max_chars=max_chars, overlap=overlap))
    return out if out else chunk_text(text, max_chars=max_chars, overlap=overlap)
