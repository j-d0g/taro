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
    "customer_preferences": {
        "query": (
            "SELECT "
            "->wants->product.{id, name, price} AS cart, "
            "->interested_in->product.{id, name, price} AS saved, "
            "->rejected->product.{id, name, price} AS rejected "
            "FROM {start}"
        ),
        "label": "Customer preferences (cart, saved, rejected) — use to avoid recommending rejected items",
    },
}


@tool
async def graph_traverse(start_id: str, pattern: str) -> str:
    """[ACT] Traverse the product/customer graph to find relationships.

    This is the PRIMARY tool for relationship queries — prefer it over `find` or `grep`
    when the user asks about connections between entities.

    Best for: "what do people also buy", "related products", "ingredients in X",
    "products for [goal]", "order history", "similar items", "complementary products".

    Do NOT use `find` for these queries — use graph_traverse instead.

    PATTERNS (use these exact names):
    - "also_bought": Products frequently bought together with start product
    - "ingredients": Active ingredients in a product
    - "similar": Products related to start product (same category, complementary)
    - "customer_history": A customer's full purchase history (products they bought)
    - "goal_products": Products that support a specific goal
    - "customer_preferences": Customer's cart, saved, and rejected products — avoid recommending rejected items

    Examples:
        graph_traverse("product:hydrating_cream", "also_bought")
        graph_traverse("customer:charlotte_gong", "customer_history")
        graph_traverse("customer:charlotte_gong", "customer_preferences")
        graph_traverse("goal:clear_skin", "goal_products")

    Args:
        start_id: Starting record ID (e.g. 'product:abc123', 'customer:charlotte_gong', 'goal:clear_skin').
                  Get IDs from grep/find results or cat output.
        pattern: One of: also_bought, ingredients, similar, customer_history, goal_products, customer_preferences.
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

            # Special case: customer_preferences returns {cart, saved, rejected}
            if pattern == "customer_preferences" and result and isinstance(result[0], dict):
                row = result[0]
                lines = [f"{p['label']} for {start_id}:"]
                for key, label in [("cart", "Cart"), ("saved", "Saved"), ("rejected", "Rejected")]:
                    items = row.get(key) or []
                    lines.append(f"  {label}: {len(items)} items")
                    for item in items:
                        name = item.get("name", "?")
                        price = item.get("price")
                        extra = f" — £{price:.2f}" if price else ""
                        lines.append(f"    • {name}{extra}")
                return "\n".join(lines)

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
