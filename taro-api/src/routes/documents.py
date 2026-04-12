"""Read-only document retrieval for citations (Layer 5/6)."""

from fastapi import APIRouter, HTTPException

import db
from helpers import str_id

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{chunk_ref}")
async def get_document(chunk_ref: str):
    """
    Fetch a documents row by id suffix (e.g. pol_abc123...) or full `documents:pol_...`.
    Used to show citation details in the UI.
    """
    rid = chunk_ref.strip()
    if not rid.startswith("documents:"):
        rid = f"documents:{rid}"

    async with db.get_db() as conn:
        # Record id may contain only [a-zA-Z0-9_]; pol_* is safe
        result = await conn.query(f"SELECT * FROM `{rid}`")
        if not result or not isinstance(result[0], dict):
            raise HTTPException(status_code=404, detail="Document not found")
        row = result[0]
        row["id"] = str_id(row.get("id", ""))
        meta = row.get("metadata") or {}
        return {
            "id": row["id"],
            "doc_type": row.get("doc_type"),
            "title": row.get("title"),
            "content": row.get("content"),
            "source_key": meta.get("source_key"),
            "chunk_index": meta.get("chunk_index"),
            "content_hash": meta.get("content_hash"),
            "indexed_at": meta.get("indexed_at"),
            "metadata": meta,
        }
