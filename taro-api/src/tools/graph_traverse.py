"""Graph traversal tool using SurrealDB RELATE edges — focused patterns."""

from langchain_core.tools import tool
from loguru import logger

from db import get_db

PATTERNS = {
    "also_bought": {
        "query": "SELECT ->also_bought->product.{id, name, price, avg_rating, subcategory} AS results FROM {start}",
        "label": "Customers who bought this also bought",
    },
    "ingredients": {
        "query": "SELECT ->contains_ingredient->ingredient.{id, name, role, description} AS results FROM {start}",
        "label": "Key ingredients",
    },
    "similar": {
        "query": "SELECT ->related_to->product.{id, name, price, subcategory} AS results FROM {start}",
        "label": "Related products",
    },
    "customer_history": {
        "query": "SELECT ->placed->order->contains->product.{id, name, price, subcategory} AS results FROM {start}",
        "label": "Purchase history",
    },
    "goal_products": {
        "query": "SELECT <-supports_goal<-product.{id, name, price, avg_rating, subcategory} AS results FROM {start}",
        "label": "Products supporting this goal",
    },
}


@tool
async def graph_traverse(start_id: str, pattern: str) -> str:
    """[ACT] Traverse the product/customer graph to find relationships.

    Use high-level patterns instead of raw edges. Each pattern runs the
    optimal multi-hop graph query and returns human-readable results.

    PATTERNS (use these exact names):
    - "also_bought": Products frequently bought together with start product
    - "ingredients": Active ingredients in a product
    - "similar": Products related to start product (same category, complementary)
    - "customer_history": A customer's full purchase history (products they bought)
    - "goal_products": Products that support a specific goal

    Examples:
        graph_traverse("product:hydrating_cream", "also_bought")
        graph_traverse("customer:charlotte_gong", "customer_history")
        graph_traverse("goal:clear_skin", "goal_products")

    Args:
        start_id: Starting record ID (e.g. 'product:impact_whey', 'customer:abc', 'goal:clear_skin').
        pattern: One of: also_bought, ingredients, similar, customer_history, goal_products.
    """
    logger.info(f"graph_traverse: {start_id} pattern={pattern}")

    if pattern not in PATTERNS:
        available = ", ".join(PATTERNS.keys())
        return f"Unknown pattern: {pattern}. Available: {available}"

    p = PATTERNS[pattern]
    try:
        async with get_db() as db:
            query = p["query"].replace("{start}", start_id)
            result = await db.query(query)

            # Extract results from the graph query response
            items = []
            if result and isinstance(result[0], dict):
                items = result[0].get("results", [])
            elif result and isinstance(result, list):
                # Flat list fallback
                items = [r for r in result if isinstance(r, dict) and "results" in r]
                if items:
                    items = items[0].get("results", [])

            if not items:
                return f"{p['label']} for {start_id}: No results found."

            lines = [f"{p['label']} for {start_id} ({len(items)} results):"]
            for item in items:
                name = item.get("name", "?")
                price = item.get("price")
                extra = ""
                if price:
                    extra += f" — \u00a3{price:.2f}"
                if item.get("avg_rating"):
                    extra += f" \u2605{item['avg_rating']:.1f}"
                if item.get("role"):
                    extra += f" ({item['role']})"
                if item.get("subcategory"):
                    extra += f" [{item['subcategory']}]"
                lines.append(f"  \u2022 {name}{extra}")
                # Product reference for structured extraction
                item_id = str(item.get("id", ""))
                if "product:" in item_id:
                    sid = item_id.split("product:", 1)[1]
                    lines.append(f"    → /products/{sid}")
                if item.get("description"):
                    lines.append(f"    {item['description'][:120]}")

            return "\n".join(lines)
    except Exception as e:
        logger.error(f"graph_traverse error: {e}")
        return f"Error in graph traversal: {e}"
