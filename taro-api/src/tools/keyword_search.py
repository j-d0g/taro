"""BM25 full-text keyword search over SurrealDB documents."""

from langchain_core.tools import tool
from loguru import logger

from db import get_db


@tool
async def keyword_search(query: str, doc_type: str = "", limit: int = 5) -> str:
    """Search documents using BM25 keyword matching.

    Best for: exact product names, specific terms, known phrases, SKUs.
    Examples: "CeraVe Cleanser", "retinol serum", "Clinique Moisture Surge".

    Args:
        query: The search terms.
        doc_type: Optional filter by document type ('product', 'faq', 'article').
        limit: Max results (default 5).
    """
    logger.info(f"keyword_search: query='{query}', doc_type='{doc_type}'")
    try:
        async with get_db() as db:
            type_filter = "AND doc_type = $doc_type" if doc_type else ""
            params: dict = {"query": query}
            if doc_type:
                params["doc_type"] = doc_type

            surql = f"""
                SELECT id, title, content, doc_type, source_id,
                       search::score(1) AS score
                FROM documents
                WHERE content @1@ $query {type_filter}
                ORDER BY score DESC
                LIMIT {limit}
            """
            result = await db.query(surql, params)
            docs = result or []

            if not docs:
                return f"No keyword results for: '{query}'"

            lines = [f"**Keyword search results for '{query}'** ({len(docs)} found):"]
            for doc in docs:
                score = doc.get("score", 0)
                lines.append(f"\n- **{doc.get('title', 'Untitled')}** (score: {score:.2f}, type: {doc.get('doc_type', '?')})")
                source_id = doc.get("source_id")
                if source_id:
                    lines.append(f"  Record: {source_id}")
                content = doc.get("content", "")
                lines.append(f"  {content[:200]}{'...' if len(content) > 200 else ''}")
            return "\n".join(lines)
    except Exception as e:
        logger.error(f"keyword_search error: {e}")
        return f"Error in keyword search: {e}"
