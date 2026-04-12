"""SHA-256 helpers for stable chunk identity (Layer 3)."""

import hashlib


def content_hash(text: str) -> str:
    """SHA-256 hex of UTF-8 normalized chunk text."""
    normalized = " ".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def chunk_record_key(source_key: str, chunk_index: int, content_hash_hex: str) -> str:
    """Deterministic 32-hex suffix for documents:pol_<suffix> record id."""
    payload = f"{source_key}\0{chunk_index}\0{content_hash_hex}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]
