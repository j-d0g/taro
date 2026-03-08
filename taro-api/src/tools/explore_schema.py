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
                tables = result if isinstance(result, dict) else (result[0] if result else {})
                if isinstance(tables, dict) and "tables" in tables:
                    table_names = list(tables["tables"].keys())
                    return f"**Database tables:** {', '.join(table_names)}"
                return f"**Database info:** {tables}"
            else:
                result = await db.query(f"INFO FOR TABLE {target}")
                info = result if isinstance(result, dict) else (result[0] if result else {})
                lines = [f"**Table: {target}**"]
                if isinstance(info, dict):
                    if "fields" in info:
                        lines.append(f"Fields: {', '.join(info['fields'].keys())}")
                    if "indexes" in info:
                        lines.append(f"Indexes: {', '.join(info['indexes'].keys())}")
                    if "events" in info:
                        lines.append(f"Events: {', '.join(info['events'].keys())}")
                else:
                    lines.append(str(info))
                return "\n".join(lines)
    except Exception as e:
        logger.error(f"explore_schema error: {e}")
        return f"Error exploring schema: {e}"
