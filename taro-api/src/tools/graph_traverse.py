"""Graph traversal tool using SurrealDB RELATE edges."""

from langchain_core.tools import tool
from loguru import logger

from db import get_db

# All available edge types in the data graph
EDGE_TYPES = {
    "placed": {"from": "customer", "to": "order", "desc": "customer's purchase history"},
    "contains": {"from": "order", "to": "product", "desc": "products in an order"},
    "has_review": {"from": "order", "to": "review", "desc": "reviews for an order"},
    "belongs_to": {"from": "product", "to": "category", "desc": "product categorization"},
    "child_of": {"from": "category", "to": "category", "desc": "category hierarchy"},
    "also_bought": {"from": "product", "to": "product", "desc": "co-purchase signal"},
    "supports_goal": {"from": "product", "to": "goal", "desc": "goal-product mapping"},
    "contains_ingredient": {"from": "product", "to": "ingredient", "desc": "product ingredients"},
    "related_to": {"from": "product", "to": "product", "desc": "related products with reason"},
}


@tool
async def graph_traverse(
    start_id: str,
    edge_type: str = "belongs_to",
    direction: str = "out",
    depth: int = 1,
) -> str:
    """Traverse graph relationships from a starting record.

    Follows edges to discover connected records. Use source_id from search
    results (e.g. 'product:impact_whey') as start_id.

    Available edge types:
      - placed: customer -> order (purchase history)
      - contains: order -> product (order contents)
      - has_review: order -> review (customer feedback)
      - belongs_to: product -> category (what category)
      - child_of: category -> category (subcategories)
      - also_bought: product -> product (co-purchased items)
      - supports_goal: product -> goal (goal mapping)
      - contains_ingredient: product -> ingredient (ingredients)
      - related_to: product -> product (similar/complementary)

    Args:
        start_id: Starting record ID (e.g. 'customer:abc123', 'product:impact_whey', 'category:protein').
        edge_type: Relationship type (see list above).
        direction: 'out' (->edge->) or 'in' (<-edge<-).
        depth: Hops to traverse (1-3, default 1).
    """
    logger.info(f"graph_traverse: {start_id} -{edge_type}-> depth={depth}")

    if edge_type not in EDGE_TYPES:
        available = ", ".join(sorted(EDGE_TYPES.keys()))
        return f"Unknown edge type: '{edge_type}'. Available: {available}"

    try:
        async with get_db() as db:
            depth = min(depth, 3)  # Cap at 3 hops

            # SurrealDB 3.0: use ->edge->? (wildcard) instead of ->edge->*
            if direction == "out":
                arrow = "".join([f"->{edge_type}->?" for _ in range(depth)])
            else:
                arrow = "".join([f"<-{edge_type}<-?" for _ in range(depth)])

            surql = f"SELECT * FROM {start_id}{arrow}"
            result = await db.query(surql)

            # Handle both SurrealDB 3.0 result formats
            if isinstance(result, list) and result:
                if isinstance(result[0], dict) and "result" in result[0]:
                    records = result[0].get("result", [])
                else:
                    records = result
            else:
                records = []

            if not records:
                edge_info = EDGE_TYPES[edge_type]
                return (
                    f"No {edge_type} connections from {start_id} "
                    f"(direction: {direction}, depth: {depth}).\n"
                    f"Edge '{edge_type}' connects {edge_info['from']} -> {edge_info['to']}: {edge_info['desc']}"
                )

            lines = [f"**Graph traversal from {start_id}** ({edge_type}, {direction}, depth {depth}):"]
            for rec in records:
                rec_id = rec.get("id", "?")
                name = rec.get("name", rec.get("title", ""))
                desc = rec.get("description", "")
                lines.append(f"\n- **{rec_id}**: {name}")
                if desc:
                    lines.append(f"  {desc[:150]}")
                # Show relation metadata if present
                for meta_field in ("reason", "weight", "score", "comment", "sentiment"):
                    val = rec.get(meta_field)
                    if val is not None:
                        lines.append(f"  {meta_field}: {val}")
            return "\n".join(lines)
    except Exception as e:
        logger.error(f"graph_traverse error: {e}")
        return f"Error in graph traversal: {e}"
