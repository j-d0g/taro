"""Shared helpers for Taro.ai API routes."""

import re

from loguru import logger

import db


PRODUCT_REF_RE = re.compile(r"→ /products/([a-f0-9_]+)")


def str_id(record_id) -> str:
    """Convert a SurrealDB RecordID to a plain string key."""
    s = str(record_id)
    # Strip table prefix (e.g. "product:abc123" -> "abc123")
    return s.split(":", 1)[1] if ":" in s else s


def collect_product_ids_from_messages(messages) -> list[str]:
    """Extract deduplicated product IDs from tool calls and tool outputs.

    Scans two sources:
    1. Tool call args: cat calls with path='/products/{id}'
    2. Tool output text: '→ /products/{id}' pattern (find, grep, graph_traverse)
    """
    seen: set[str] = set()
    ids: list[str] = []

    for msg in messages:
        # From cat tool call args
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc.get("name") == "cat":
                    path = tc.get("args", {}).get("path", "")
                    if path.startswith("/products/"):
                        pid = path.replace("/products/", "").strip("/")
                        if pid and pid not in seen:
                            seen.add(pid)
                            ids.append(pid)

        # From tool output text (find, grep, graph_traverse all use → /products/{id})
        if msg.__class__.__name__ == "ToolMessage" and isinstance(msg.content, str):
            for match in PRODUCT_REF_RE.finditer(msg.content):
                pid = match.group(1)
                if pid not in seen:
                    seen.add(pid)
                    ids.append(pid)

    return ids


def collect_product_ids_from_text(text: str, seen: set[str]) -> list[str]:
    """Extract product IDs from a single tool output string. For streaming use."""
    ids = []
    for match in PRODUCT_REF_RE.finditer(text):
        pid = match.group(1)
        if pid not in seen:
            seen.add(pid)
            ids.append(pid)
    return ids


async def fetch_products(product_ids: list[str]) -> list[dict]:
    """Fetch structured product data from DB for a list of IDs."""
    if not product_ids:
        return []
    products = []
    try:
        async with db.get_db() as conn:
            for pid in product_ids[:10]:  # Cap at 10
                result = await conn.query(
                    f"SELECT id, name, price, avg_rating, image_url, vertical, subcategory "
                    f"FROM product:`{pid}`"
                )
                if result and isinstance(result[0], dict) and "name" in result[0]:
                    p = result[0]
                    products.append({
                        "id": str_id(p.get("id", "")),
                        "name": p["name"],
                        "price": p.get("price"),
                        "avg_rating": p.get("avg_rating"),
                        "image_url": p.get("image_url", ""),
                        "vertical": p.get("vertical", ""),
                        "subcategory": p.get("subcategory", ""),
                    })
    except Exception as prod_err:
        logger.warning(f"Failed to fetch product details: {prod_err}")
    return products


def sse(event_type: str, data: dict) -> str:
    """Format a single SSE event."""
    import json
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
