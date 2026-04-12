"""Consume ingestion events and run processor (Layers 2 + 3)."""

from __future__ import annotations

import os
from pathlib import Path

from ingestion.events import IngestionEvent
from ingestion.logutil import logger
from ingestion.processor import ingest_policy_file
from ingestion.queue import get_queue


def _content_path_for_source_key(source_key: str) -> Path:
    """Resolve landing file under taro-api/content/."""
    api_root = Path(__file__).resolve().parent.parent.parent
    return api_root / "content" / source_key


async def handle_event(event: IngestionEvent) -> dict:
    from ingestion.processor import delete_policy_by_source_key

    if event.op == "delete":
        import db

        async with db.get_db() as conn:
            await delete_policy_by_source_key(conn, event.source_key)
        return {"deleted": event.source_key}

    path = _content_path_for_source_key(event.source_key)
    if not path.is_file():
        logger.error(f"Ingestion: file not found for {event.source_key} -> {path}")
        return {"error": "file_not_found", "path": str(path)}
    return await ingest_policy_file(path, source_key=event.source_key)


async def run_worker_loop(once: bool = False) -> None:
    """Poll queue and process events until empty (or one shot if once=True)."""
    q = get_queue()
    while True:
        ev = await q.dequeue(timeout_sec=2.0 if not once else 0.5)
        if not ev:
            if once:
                break
            continue
        try:
            await handle_event(ev)
        except Exception as e:
            logger.exception(f"Ingestion worker failed: {e}")
