"""Direct record lookup by SurrealDB ID."""

from langchain_core.tools import tool
from loguru import logger

from db import get_db


@tool
async def get_record(record_id: str) -> str:
    """Fetch a specific record by its SurrealDB ID (e.g. 'product:abc123' or 'documents:xyz').

    Use this when you already know the exact record ID and want its full details.
    """
    logger.info(f"get_record: {record_id}")
    try:
        async with get_db() as db:
            result = await db.select(record_id)
            if not result:
                return f"No record found with ID: {record_id}"

            # Format fields into readable output
            record = result if isinstance(result, dict) else result[0] if result else {}
            lines = [f"**Record: {record_id}**"]
            for key, value in record.items():
                if key == "embedding":
                    lines.append(f"- {key}: [vector, {len(value)} dims]")
                else:
                    lines.append(f"- {key}: {value}")
            return "\n".join(lines)
    except Exception as e:
        logger.error(f"get_record error: {e}")
        return f"Error fetching record {record_id}: {e}"
