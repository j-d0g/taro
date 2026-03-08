"""Schema introspection tool for SurrealDB."""

from langchain_core.tools import tool
from loguru import logger

from db import get_db


@tool
async def explore_schema(target: str = "") -> str:
    """Explore the SurrealDB database schema.

    If target is empty, returns all tables in the database.
    If target is a table name (e.g. 'product', 'documents'), returns that table's fields and indexes.

    Use this to understand what data is available before querying.
    """
    logger.info(f"explore_schema: target='{target}'")
    try:
        async with get_db() as db:
            if not target:
                result = await db.query("INFO FOR DB")
                # SurrealDB 3.0: result is the dict directly or wrapped in result key
                tables = {}
                if result:
                    item = result[0] if isinstance(result, list) else result
                    if isinstance(item, dict):
                        if "result" in item:
                            tables = item["result"]
                        else:
                            tables = item

                if isinstance(tables, dict) and "tables" in tables:
                    table_info = tables["tables"]
                    table_names = list(table_info.keys()) if isinstance(table_info, dict) else []
                    return f"**Database tables ({len(table_names)}):** {', '.join(sorted(table_names))}"
                # Fallback: just show what we got
                return f"**Database info:** {tables}"
            else:
                result = await db.query(f"INFO FOR TABLE {target}")
                # SurrealDB 3.0: handle both formats
                info = {}
                if result:
                    item = result[0] if isinstance(result, list) else result
                    if isinstance(item, dict):
                        info = item.get("result", item)

                lines = [f"**Table: {target}**"]
                if isinstance(info, dict):
                    if "fields" in info:
                        fields = info["fields"]
                        field_names = list(fields.keys()) if isinstance(fields, dict) else []
                        lines.append(f"Fields ({len(field_names)}): {', '.join(sorted(field_names))}")
                    if "indexes" in info:
                        indexes = info["indexes"]
                        idx_names = list(indexes.keys()) if isinstance(indexes, dict) else []
                        lines.append(f"Indexes ({len(idx_names)}): {', '.join(sorted(idx_names))}")
                    if "events" in info:
                        events = info["events"]
                        evt_names = list(events.keys()) if isinstance(events, dict) else []
                        if evt_names:
                            lines.append(f"Events: {', '.join(sorted(evt_names))}")
                else:
                    lines.append(str(info))
                return "\n".join(lines)
    except Exception as e:
        logger.error(f"explore_schema error: {e}")
        return f"Error exploring schema: {e}"
