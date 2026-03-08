"""Raw read-only SurrealQL query execution for advanced queries."""

import re

from langchain_core.tools import tool
from loguru import logger

from db import get_db

BLOCKED_KEYWORDS = re.compile(
    r"\b(CREATE|UPDATE|DELETE|REMOVE|DEFINE|RELATE|INSERT|ALTER|DROP)\b",
    re.IGNORECASE,
)


@tool
async def surrealql_query(query: str, params: dict | None = None) -> str:
    """Execute a read-only SurrealQL query for advanced analysis.

    Use this when the specialized tools can't handle what you need:
    aggregations (COUNT, SUM, AVG, MIN, MAX), complex filters, JOINs,
    GROUP BY, math functions, or multi-table queries.

    ONLY SELECT and INFO statements are allowed. Write operations are blocked.

    Args:
        query: A SurrealQL SELECT or INFO statement.
        params: Optional query parameters dict.
    """
    logger.info(f"surrealql_query: {query}")

    if BLOCKED_KEYWORDS.search(query):
        return "Error: only SELECT and INFO statements are allowed. Write operations are blocked."

    try:
        async with get_db() as db:
            result = await db.query(query, params or {})
            rows = result if isinstance(result, list) else [result] if result else []

            if not rows:
                return f"Query returned no results.\nQuery: {query}"

            if isinstance(rows, list):
                lines = [f"**Query returned {len(rows)} result(s):**"]
                for row in rows:
                    if isinstance(row, dict):
                        parts = [f"  {k}: {v}" for k, v in row.items()]
                        lines.append("\n".join(parts))
                    else:
                        lines.append(str(row))
                    lines.append("---")
                return "\n".join(lines)

            return str(rows)
    except Exception as e:
        logger.error(f"surrealql_query error: {e}")
        return f"Error executing query: {e}"
