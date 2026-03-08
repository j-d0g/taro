"""Vector similarity search using SurrealDB HNSW index."""

from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from loguru import logger

from db import get_db


@tool
async def semantic_search(query: str, doc_type: str = "", limit: int = 5) -> str:
    """Search documents using vector similarity (semantic meaning).

    Best for: natural language questions, conceptual queries, "find similar" requests.
    Examples: "something for sensitive skin", "moisturizer for dryness", "hydrating serum".

    Args:
        query: Natural language search query.
        doc_type: Optional filter by document type ('product', 'faq', 'article').
        limit: Max results (default 5).
    """
    logger.info(f"semantic_search: query='{query}', doc_type='{doc_type}'")
    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        query_embedding = await embeddings.aembed_query(query)

        async with get_db() as db:
            type_filter = "AND doc_type = $doc_type" if doc_type else ""
            params: dict = {"embedding": query_embedding}
            if doc_type:
                params["doc_type"] = doc_type

            surql = f"""
                SELECT id, title, content, doc_type, source_id,
                       vector::similarity::cosine(embedding, $embedding) AS score
                FROM documents
                WHERE embedding != NONE {type_filter}
                ORDER BY score DESC
                LIMIT {limit}
            """
            result = await db.query(surql, params)
            docs = [d for d in (result or []) if isinstance(d, dict)]

            if not docs:
                return f"No semantic results for: '{query}'"

            lines = [f"**Semantic search results for '{query}'** ({len(docs)} found):"]
            for doc in docs:
                score = doc.get("score", 0)
                lines.append(f"\n- **{doc.get('title', 'Untitled')}** (similarity: {score:.3f}, type: {doc.get('doc_type', '?')})")
                source_id = doc.get("source_id")
                if source_id:
                    lines.append(f"  Record: {source_id}")
                content = doc.get("content", "")
                lines.append(f"  {content[:200]}{'...' if len(content) > 200 else ''}")
            return "\n".join(lines)
    except Exception as e:
        logger.error(f"semantic_search error: {e}")
        return f"Error in semantic search: {e}"
