# FAQ / help / policy: 6-layer data path in Taro (implementation)

This document maps the ingestion stack to the codebase. **Product catalogue** remains batch-seeded; **policy/help** chunks use incremental ingestion from `content/policy/` with hash-stable IDs.

## Layer 1 — Landing (storage)

- **Location:** [`taro-api/content/policy/`](../taro-api/content/policy/) — markdown files (e.g. `shipping.md`, `returns.md`).
- **Stable key:** `source_key` = path relative to `content/`, e.g. `policy/shipping.md`.

## Layer 2 — Events (async boundary)

- **Abstraction:** [`taro-api/src/ingestion/queue.py`](../taro-api/src/ingestion/queue.py) — `INGESTION_BACKEND`: `none` | `file` (JSONL under `.ingest_queue/`) | `redis` (optional `pip install redis`).
- **HTTP enqueue:** `POST /ingest/policy` with header `X-Ingest-Token` (requires `INGEST_WEBHOOK_SECRET` in env). Body: `{ "source_key": "policy/shipping.md", "op": "upsert" | "delete" }`.
- **CLI:** `cd taro-api/src && python -m ingestion.cli enqueue policy/shipping.md` (with `INGESTION_BACKEND=file`).

## Layer 3 — Processing / indexing

- **Package:** [`taro-api/src/ingestion/processor.py`](../taro-api/src/ingestion/processor.py) — chunk text, **SHA-256** `content_hash`, deterministic `documents:pol_<32hex>` record ids, embed with `text-embedding-3-small`, **CREATE** rows with `doc_type = 'policy'`.
- **CLI:** `make ingest-policy` (from `taro-api`) or `python -m ingestion.cli ingest-all`.

## Layer 4 — Retrieval index

- SurrealDB [`documents`](../taro-api/schema/schema.surql) table — same vector + BM25 indexes as products.

## Layer 5 — Query / serving

- **`find(query, doc_type="policy")`** and **`grep(query, "/policy")`** — see [`fs_tools.py`](../taro-api/src/tools/fs_tools.py); tool output includes `id`, `source_key` for citations.
- **`GET /documents/{chunk_ref}`** — e.g. `/documents/pol_<32hex>` for citation UI.

## Layer 6 — Generation + governance

- Prompts: [`default.md`](../taro-api/src/prompts/templates/default.md), [`harness.md`](../taro-api/src/prompts/templates/harness.md) — ground shipping/returns/policy answers in tool results; cite **source_key**.
- Chat logs `retrieval_citation` when tool output contains `source_key:` ([`chat.py`](../taro-api/src/routes/chat.py)).

## Metadata contract

See [documents-metadata.md](./documents-metadata.md).

## Phased rollout

1. Run `make ingest-policy` locally (requires `OPENAI_API_KEY` + SurrealDB).
2. Optional: set `INGESTION_BACKEND=file`, enqueue events, `make ingest-drain`.
3. Production: pair **S3 + SQS** (or **GCS + Pub/Sub**) using the same event payload and worker.

## Operational notes

- **Index lag:** compare webhook `occurred_at` (when added) to `metadata.indexed_at` on rows.
- **Freshness vs cost:** optional debounce in worker (not implemented in MVP).
