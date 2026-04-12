# Documents table metadata contract (Taro)

Applies to rows in SurrealDB `documents` used for hybrid search (`find` / `grep`).

## `doc_type` taxonomy

| Value | Meaning |
|-------|---------|
| `product` | Product catalogue copy; `source_id` → `product:…` |
| `faq` | Legacy FAQ rows from CSV seed |
| `article` | Long-form editorial (optional) |
| `policy` | FAQ / help / policy chunks from Layer 1 landing (markdown), ingested by the policy worker |

## Policy chunk metadata (`doc_type = policy`)

Stored in the `metadata` object (FLEXIBLE). Keys:

| Key | Type | Description |
|-----|------|-------------|
| `source_key` | string | Stable path from landing zone, e.g. `policy/shipping.md` |
| `chunk_index` | int | Zero-based index within the file |
| `content_hash` | string | SHA-256 hex of UTF-8 normalized chunk text |
| `indexed_at` | string | ISO8601 UTC when this row was last written by the worker |
| `version` | string | Optional; content hash of full source file or semver for campaigns |

## Record IDs for policy chunks

Deterministic: `pol_` + first 32 hex chars of  
`SHA256(source_key + "\\0" + str(chunk_index) + "\\0" + content_hash)`.

Surreal record: `documents:pol_<32 hex>`.

## Migrations

Existing DBs created before `policy` ingestion: no `ALTER TABLE` required; `metadata` remains optional object. New policy rows are additive. Re-run `schema.surql` only if you add new top-level fields (optional).

## Index lag

Compare event `occurred_at` (Layer 2) with `metadata.indexed_at` (Layer 3) for observability.
