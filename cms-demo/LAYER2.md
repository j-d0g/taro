# Optional Layer 2 publish path (enqueue + drain)

The default CMS **Publish** runs **direct** ingestion: `python -m ingestion.cli ingest-file …` (Layers 1 → 3 synchronously).

To demonstrate the **async boundary** from the FAQ RAG plan (queue + worker):

1. In **taro-api** `.env`: set `INGESTION_BACKEND=file` (JSONL queue under `taro-api/.ingest_queue/`).
2. Set **`INGEST_WEBHOOK_SECRET`** in both **taro-api** and **cms-demo** `.env` (same value).
3. In **cms-demo** `.env`: `PUBLISH_MODE=enqueue` and `INGEST_WEBHOOK_SECRET=...`.
4. Start **Taro** (`make serve`) so `POST /ingest/policy` is available.
5. From CMS, **Publish** will: `POST /ingest/policy` with `X-Ingest-Token`, then run `python -m ingestion.cli drain` in `taro-api/src` (same env as subprocess, including `OPENAI_API_KEY` from merged `.env` files).

If `INGEST_WEBHOOK_SECRET` is unset in Taro, the ingest endpoint returns 503 — configure it first.

For production you would replace file queue + drain with Redis/SQS and a long-running worker; the **event payload** shape stays `{ "source_key", "op" }` as in [`taro-api/src/routes/ingestion_route.py`](../taro-api/src/routes/ingestion_route.py).
