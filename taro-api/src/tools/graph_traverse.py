"""Graph traversal tool using SurrealDB RELATE edges."""

from langchain_core.tools import tool
from loguru import logger

from db import get_db


@tool
async def graph_traverse(
    start_id: str,
    edge_type: str = "belongs_to",
    direction: str = "out",
    depth: int = 1,
) -> str:
    """Traverse graph relationships from a starting record.

    Follows edges (belongs_to, child_of, related_to) to discover connected records.
    Best for: "what category is this product in?", "related products", "subcategories of X".

    Use the source_id returned by search tools (e.g. 'product:impact_whey') as start_id.

    Args:
        start_id: Starting record ID (e.g. 'product:whey_isolate', 'category:protein').
        edge_type: Relationship type: 'belongs_to', 'child_of', 'related_to'.
        direction: 'out' (->edge->) or 'in' (<-edge<-).
        depth: Hops to traverse (1-3, default 1).
    """
    logger.info(f"graph_traverse: {start_id} -{edge_type}-> depth={depth}")
    try:
        async with get_db() as db:
            depth = min(depth, 3)  # Cap at 3 hops

            if direction == "out":
                arrow = "".join([f"->{edge_type}->" for _ in range(depth)])
            else:
                arrow = "".join([f"<-{edge_type}<-" for _ in range(depth)])

            surql = f"SELECT * FROM {start_id}{arrow}*"
            result = await db.query(surql)
            records = result[0].get("result", []) if result else []

            if not records:
                return f"No {edge_type} connections from {start_id} (direction: {direction}, depth: {depth})"

            lines = [f"**Graph traversal from {start_id}** ({edge_type}, {direction}, depth {depth}):"]
            for rec in records:
                rec_id = rec.get("id", "?")
                name = rec.get("name", rec.get("title", ""))
                desc = rec.get("description", "")
                lines.append(f"\n- **{rec_id}**: {name}")
                if desc:
                    lines.append(f"  {desc[:150]}")
                # Show relation metadata if present
                reason = rec.get("reason")
                if reason:
                    lines.append(f"  Reason: {reason}")
            return "\n".join(lines)
    except Exception as e:
        logger.error(f"graph_traverse error: {e}")
        return f"Error in graph traversal: {e}"
