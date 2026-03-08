"""Tavily web search with SurrealDB caching."""

import os
from datetime import datetime, timezone

from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from loguru import logger

from db import get_db


@tool
async def web_search(query: str) -> str:
    """Search the web for current information using Tavily, scoped to lookfantastic.com.

    Use as a FALLBACK when SurrealDB tools return no results, or for:
    - Current promotions/deals
    - Up-to-date product availability
    - Recent blog posts or articles

    Results are cached in SurrealDB to avoid repeated API calls.

    Args:
        query: Search query.
    """
    logger.info(f"web_search: query='{query}'")
    try:
        async with get_db() as db:
            # Check cache first
            cache_result = await db.query(
                "SELECT * FROM web_cache WHERE query = $query AND "
                "time::now() - cached_at < 24h LIMIT 1",
                {"query": query},
            )
            cached = cache_result or []
            if cached:
                logger.info("web_search: returning cached result")
                results = cached[0].get("results", [])
                return _format_results(query, results, cached=True)

            # Call Tavily
            tavily = TavilySearch(
                max_results=5,
                include_domains=["lookfantastic.com"],
            )
            response = await tavily.ainvoke({"query": query})

            # Parse results
            if isinstance(response, str):
                results = [{"content": response}]
            elif isinstance(response, list):
                results = response
            elif isinstance(response, dict):
                results = response.get("results", [response])
            else:
                results = [{"content": str(response)}]

            # Cache to SurrealDB
            await db.query(
                "CREATE web_cache SET query = $query, results = $results, cached_at = time::now()",
                {"query": query, "results": results},
            )
            logger.info(f"web_search: cached {len(results)} results")

            return _format_results(query, results, cached=False)
    except Exception as e:
        logger.error(f"web_search error: {e}")
        return f"Error in web search: {e}"


def _format_results(query: str, results: list, cached: bool) -> str:
    cache_tag = " (cached)" if cached else ""
    lines = [f"**Web search results for '{query}'**{cache_tag} ({len(results)} found):"]
    for r in results:
        if isinstance(r, dict):
            title = r.get("title", "")
            url = r.get("url", "")
            content = r.get("content", "")
            if title:
                lines.append(f"\n- **{title}**")
            if url:
                lines.append(f"  URL: {url}")
            if content:
                lines.append(f"  {content[:300]}{'...' if len(content) > 300 else ''}")
        else:
            lines.append(f"\n- {str(r)[:300]}")
    return "\n".join(lines)
