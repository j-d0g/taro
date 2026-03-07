"""Hybrid search combining vector + BM25 via Reciprocal Rank Fusion."""

from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from loguru import logger

from db import get_db


def _rrf_fuse(vector_results: list, bm25_results: list, k: int = 60) -> list[dict]:
    """Fuse two ranked result lists using Reciprocal Rank Fusion.

    For each document, score = sum(1 / (k + rank)) across all lists it appears in.
    Returns merged results sorted by fused score, deduplicated by id.
    """
    scores: dict[str, float] = {}
    docs_by_id: dict[str, dict] = {}

    for rank, doc in enumerate(vector_results):
        doc_id = str(doc.get("id", ""))
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
        if doc_id not in docs_by_id:
            docs_by_id[doc_id] = doc
        else:
            docs_by_id[doc_id]["vec_score"] = doc.get("vec_score", 0)

    for rank, doc in enumerate(bm25_results):
        doc_id = str(doc.get("id", ""))
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
        if doc_id not in docs_by_id:
            docs_by_id[doc_id] = doc
        else:
            docs_by_id[doc_id]["bm25_score"] = doc.get("bm25_score", doc.get("score", 0))

    # Sort by fused score descending
    ranked_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    results = []
    for doc_id in ranked_ids:
        doc = docs_by_id[doc_id]
        doc["rrf_score"] = scores[doc_id]
        results.append(doc)
    return results


@tool
async def hybrid_search(query: str, doc_type: str = "", limit: int = 5) -> str:
    """Search using HYBRID strategy: combines semantic (vector) and keyword (BM25) results via Reciprocal Rank Fusion.

    This is the most powerful search tool. Use it as the default for product recommendations
    and general queries where you want both exact matches AND semantically similar results.

    Args:
        query: Natural language search query.
        doc_type: Optional filter by document type ('product', 'faq', 'article').
        limit: Max results (default 5).
    """
    logger.info(f"hybrid_search: query='{query}', doc_type='{doc_type}'")
    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        query_embedding = await embeddings.aembed_query(query)

        async with get_db() as db:
            type_filter = "AND doc_type = $doc_type" if doc_type else ""
            params = {"embedding": query_embedding, "query": query}
            if doc_type:
                params["doc_type"] = doc_type

            fetch_limit = limit * 2

            # Run vector and BM25 searches separately, then fuse with RRF
            vec_surql = f"""
                SELECT id, title, content, doc_type, source_id,
                       vector::similarity::cosine(embedding, $embedding) AS vec_score
                FROM documents
                WHERE embedding <|{fetch_limit}|> $embedding {type_filter}
                ORDER BY vec_score DESC
            """
            bm25_surql = f"""
                SELECT id, title, content, doc_type, source_id,
                       search::score(1) AS bm25_score
                FROM documents
                WHERE content @1@ $query {type_filter}
                ORDER BY bm25_score DESC
                LIMIT {fetch_limit}
            """

            vec_result = await db.query(vec_surql, params)
            bm25_result = await db.query(bm25_surql, params)

            vec_docs = vec_result[0].get("result", []) if vec_result else []
            bm25_docs = bm25_result[0].get("result", []) if bm25_result else []

            # Fuse with Reciprocal Rank Fusion
            fused = _rrf_fuse(vec_docs, bm25_docs)[:limit]

            if not fused:
                return f"No hybrid results for: '{query}'"

            lines = [f"**Hybrid search results for '{query}'** ({len(fused)} found, fused from {len(vec_docs)} vector + {len(bm25_docs)} keyword):"]
            for doc in fused:
                vec = doc.get("vec_score", 0)
                bm25 = doc.get("bm25_score", 0)
                rrf = doc.get("rrf_score", 0)
                lines.append(
                    f"\n- **{doc.get('title', 'Untitled')}** "
                    f"(rrf: {rrf:.4f}, vec: {vec:.3f}, bm25: {bm25:.2f}, type: {doc.get('doc_type', '?')})"
                )
                source_id = doc.get("source_id")
                if source_id:
                    lines.append(f"  Record: {source_id}")
                content = doc.get("content", "")
                lines.append(f"  {content[:200]}{'...' if len(content) > 200 else ''}")
            return "\n".join(lines)
    except Exception as e:
        logger.error(f"hybrid_search error: {e}")
        return f"Error in hybrid search: {e}"
