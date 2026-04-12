"""Enqueue policy ingestion events (Layer 2) — protect with shared secret in production."""

import os

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from ingestion.events import IngestionEvent
from ingestion.queue import get_queue

router = APIRouter(prefix="/ingest", tags=["ingestion"])


class IngestRequest(BaseModel):
    source_key: str
    op: str = "upsert"  # upsert | delete


def _check_token(x_ingest_token: str | None) -> None:
    expected = os.getenv("INGEST_WEBHOOK_SECRET", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="INGEST_WEBHOOK_SECRET not configured")
    if x_ingest_token != expected:
        raise HTTPException(status_code=401, detail="Invalid ingest token")


@router.post("/policy")
async def enqueue_policy(
    body: IngestRequest,
    x_ingest_token: str | None = Header(None, alias="X-Ingest-Token"),
):
    """Enqueue upsert/delete for a policy source_key (requires X-Ingest-Token)."""
    _check_token(x_ingest_token)
    if body.op not in ("upsert", "delete"):
        raise HTTPException(status_code=400, detail="op must be upsert or delete")
    ev = IngestionEvent(source_key=body.source_key, op=body.op)
    q = get_queue()
    await q.enqueue(ev)
    return {"queued": True, "event": ev.to_json()}
