# One Database, Seven Roles: How We Use SurrealDB

> **Taro.ai** -- LangChain x SurrealDB Hackathon, London, March 6-8 2026

---

> **TL;DR**
>
> - A single SurrealDB instance serves seven distinct roles: vector store, keyword index, graph database, relational store, checkpoint backend, conversation memory, and web cache.
> - The `documents` table carries three indexes simultaneously -- HNSW vector (1536d cosine), BM25 full-text with snowball stemming, and a flat filter index on `doc_type` -- enabling hybrid search from one table.
> - Preference edges (`wants`, `interested_in`, `rejected`) are created live during conversation, turning user intent into graph structure that persists across sessions and feeds future recommendations.

---

## The Seven Roles

Most applications use SurrealDB for one or two things. We use it for seven. This was partly a hackathon constraint (minimize infrastructure) and partly a test of SurrealDB's multi-model thesis: can one database genuinely replace a vector store, a search engine, a graph database, and a key-value store?

### 1. Vector Store

The `documents` table holds 1536-dimensional embeddings from OpenAI's `text-embedding-3-small` model. An HNSW index (`schema.surql:19-20`) enables approximate nearest-neighbor search:

```sql
DEFINE INDEX idx_documents_embedding ON documents FIELDS embedding
    HNSW DIMENSION 1536 DIST COSINE;
```

The `find` tool queries this index using `ORDER BY vector::similarity::cosine(embedding, $vec) DESC` (`fs_tools.py:745-749`). We cannot use the KNN operator `<|N|>` because it is broken in SurrealDB 3.0 -- the workaround is explicit cosine ordering with a `LIMIT` clause. Embeddings are cached client-side in an LRU dict (`fs_tools.py:32-51`) to avoid redundant OpenAI API calls during stress testing.

The `review` table also has its own HNSW index (`schema.surql:99-100`) for semantic search over customer review comments, though the agent primarily searches the `documents` table.

### 2. Keyword Index (BM25)

The same `documents` table carries BM25 full-text indexes on both `content` and `title` (`schema.surql:23-27`):

```sql
DEFINE ANALYZER doc_analyzer TOKENIZERS blank, class FILTERS lowercase, snowball(english);
DEFINE INDEX idx_documents_content ON documents FIELDS content
    SEARCH ANALYZER doc_analyzer BM25;
DEFINE INDEX idx_documents_title ON documents FIELDS title
    SEARCH ANALYZER doc_analyzer BM25;
```

The `snowball(english)` filter provides stemming so that "moisturizing" matches "moisturiser". In practice, SurrealDB 3.0's BM25 `@1@` operator frequently returns empty results, so both `find` and `grep` include a `CONTAINS` fallback path that splits the query into words and uses case-insensitive string matching (`fs_tools.py:637-641`, `fs_tools.py:770-781`). This trades ranking precision for recall -- a reasonable tradeoff when the alternative is returning nothing.

### 3. Graph Database

Twelve edge types defined as `TYPE RELATION` tables (`schema.surql:133-176`) form a knowledge graph across products, customers, orders, reviews, categories, goals, and ingredients. SurrealDB's graph traversal syntax lets us chain edges in a single query:

```sql
-- 3-hop traversal: customer -> placed -> order -> contains -> product
SELECT ->placed->order->contains->product.{name, price} AS products
FROM customer:diego_carvalho
```

This query (`graph_traverse.py:23-24`, pattern `customer_history`) follows three edges in one statement -- no JOINs, no subqueries, no application-level stitching. The `graph_traverse` tool exposes 5 pre-built patterns (`also_bought`, `ingredients`, `similar`, `customer_history`, `goal_products`) that cover the most common relationship queries.

The `cat` tool also performs graph traversals in verbose mode. For example, `cat /products/{id}` fetches related products via `->related_to->product`, category via `->belongs_to->category`, and edge counts for `also_bought`, `ingredients`, `goals`, and `related_to` (`fs_tools.py:274-345`).

### 4. Relational Store

Seven `SCHEMAFULL` tables (`customer`, `product`, `order`, `review`, `category`, `goal`, `ingredient`) hold structured data with typed fields (`schema.surql:35-129`). These are conventional relational records: a product has a `name` (string), `price` (float), `avg_rating` (float), `dietary_tags` (array of strings), and so on.

The FastAPI endpoints (`main.py:663-1121`) query these tables directly for REST API responses -- product listings, customer profiles, category hierarchies, goal details. The `surrealql_query` tool (`raw_query.py:17-57`) gives the agent raw read-only access to these tables for ad-hoc aggregations like `SELECT count() FROM product WHERE price < 20 GROUP ALL`.

### 5. Checkpoint Backend

LangGraph agent state is persisted via `SurrealSaver` (`graph.py:101-108`), which stores conversation checkpoints in two `SCHEMALESS` tables:

```sql
DEFINE TABLE checkpoint SCHEMALESS;
DEFINE TABLE write SCHEMALESS;
```

These tables (`schema.surql:228-229`) must be created manually -- SurrealSaver v2.0.0 will not auto-create them, and without them, `db.query()` returns an error string instead of an empty list, crashing `aget_tuple`. The `SurrealSaver` is initialized with the same connection parameters as the rest of the application (`graph.py:102-107`), with a `MemorySaver` fallback if the connection fails (`graph.py:112`).

### 6. Conversation Memory

The `conversation` table (`schema.surql:210-222`) stores full chat history independent of LangGraph checkpoints:

```sql
DEFINE TABLE conversation SCHEMAFULL;
DEFINE FIELD thread_id ON conversation TYPE string;
DEFINE FIELD messages ON conversation TYPE array;
DEFINE FIELD summary ON conversation TYPE option<string>;
```

Each conversation is keyed by `thread_id` (unique index) and contains an array of message objects with `role`, `content`, `tool_calls`, and `timestamp`. The `_save_conversation` function (`main.py:203-234`) upserts after every chat turn -- appending new messages to existing conversations or creating new ones. This survives server restarts, unlike the MemorySaver fallback.

The `POST /distill` endpoint (`main.py:581-653`) reads from this table first (`main.py:594-601`), falling back to the LangGraph checkpointer only if the conversation table has no data. This two-source approach means distillation works even after the in-memory checkpointer has been cleared by a restart.

### 7. Web Cache

The `web_cache` table (`schema.surql:181-188`) caches Tavily web search results:

```sql
DEFINE TABLE web_cache SCHEMAFULL;
DEFINE FIELD query ON web_cache TYPE string;
DEFINE FIELD results ON web_cache TYPE array;
DEFINE FIELD cached_at ON web_cache TYPE datetime DEFAULT time::now();
DEFINE INDEX idx_web_cache_query ON web_cache FIELDS query UNIQUE;
```

The `web_search` tool checks this cache before calling the Tavily API (`web_search.py:31-39`). Results are cached with a 24-hour TTL, checked via `time::now() - cached_at < 24h`. This prevents redundant API calls when multiple users ask similar questions about current promotions or deals on lookfantastic.com.

---

## Triple-Indexed Documents

The `documents` table is the most heavily indexed table in the schema. A single row carries:

1. **HNSW vector index** (`idx_documents_embedding`): 1536-dimensional float array, cosine distance. Used by `find` for semantic search.
2. **BM25 full-text indexes** (`idx_documents_content`, `idx_documents_title`): English snowball stemming with blank/class tokenization. Used by `find` and `grep` for keyword search.
3. **Filter index** (`idx_documents_doc_type`): Plain index on `doc_type` string. Used to scope searches to `"product"`, `"faq"`, or `"article"`.

The `find` tool runs two queries against this table in parallel -- one vector, one BM25 -- and fuses the results with client-side RRF (`fs_tools.py:762-783`). The `doc_type` filter is applied as a `WHERE` clause in both queries via parameterized queries (`$doc_type`), never f-string interpolation (`fs_tools.py:735`).

Each document's `source_id` field is typed as `option<record>` (`schema.surql:13`), a native SurrealDB record link. This means `source_id = product:cerave_cleanser` is not just a string -- it is a typed reference that SurrealDB can validate and traverse. The tools format this as `-> /products/{id}` in their output (`fs_tools.py:660-661`, `fs_tools.py:799-801`), which the frontend regex-extracts to render product cards.

---

## Graph as Knowledge Structure

The 12 edge types encode four categories of knowledge:

**Commerce relationships** (3 edges): `placed`, `contains`, `has_review` -- the transactional backbone. A customer places orders, orders contain products, orders have reviews. This enables multi-hop queries like "what did customer X buy, and how did they review it?"

**Taxonomy** (2 edges): `belongs_to`, `child_of` -- category hierarchy. Three verticals (Skincare, Haircare, Body & Fragrance) contain 9 subcategories. The `tree /categories` command expands this hierarchy recursively (`fs_tools.py:888-926`).

**Domain knowledge** (4 edges): `also_bought`, `supports_goal`, `contains_ingredient`, `related_to` -- the recommendation engine's fuel. `also_bought` edges are derived from co-purchase patterns. `supports_goal` maps products to beauty goals like "clear skin" or "hydration". `contains_ingredient` links products to active ingredients with optional `concentration` metadata. `related_to` captures editorial cross-references with a `reason` field ("same category", "complementary", "alternative").

**Live preferences** (3 edges): `wants`, `interested_in`, `rejected` -- created during conversation (see next section).

---

## Evolving Context -- Live Preference Edges

When a user interacts with product cards in the frontend (add to cart, save, remove), the `POST /preferences` endpoint (`main.py:947-980`) creates or replaces graph edges:

| Action | Edge Created | Meaning |
|--------|-------------|---------|
| `cart` | `customer ->wants-> product` | Active purchase intent |
| `keep` | `customer ->interested_in-> product` | Saved for later consideration |
| `remove` | `customer ->rejected-> product` | Explicitly not interested |

The endpoint is idempotent: before creating a new edge, it deletes any existing preference edges for that user-product pair (`main.py:961-963`). This means a user can move a product from "saved" to "cart" without accumulating stale edges.

These edges carry timestamps (`added_at`) and the `rejected` edge has an optional `reason` field. They are immediately queryable by the agent via `graph_traverse` or `surrealql_query`, meaning the agent's recommendations can adapt within the same conversation. The `GET /preferences/{user_id}` endpoint (`main.py:983-1007`) returns all three edge types grouped by action.

---

## Memory Distillation

The `POST /distill` endpoint (`main.py:581-653`) implements a two-stage memory pipeline:

1. **Load conversation**: Try the `conversation` table first (`main.py:594-601`), then fall back to the LangGraph checkpointer (`main.py:604-608`). This ensures distillation works even after server restarts clear the in-memory checkpointer.

2. **LLM distillation**: The last 20 messages are formatted into a text block and sent to the LLM with a distillation prompt (`main.py:632-640`). The prompt instructs the model to extract key preferences, interests, goals, and insights, merging with any existing context rather than overwriting it.

3. **Persist**: The distilled context string is written to the `customer.context` field (`main.py:644-648`). On subsequent conversations, this context is injected into the user message via `_build_message_content` (`main.py:100-168`), which also prepends profile fields, purchase history, and review sentiment.

The customer record also has a `memory` field (`schema.surql:54`) typed as `array<string>` -- a list of key facts for personalization that persists across sessions.

---

## Self-Improvement Tables

Two tables form a feedback loop for tool selection quality:

**`learned_pattern`** (`schema.surql:193-200`): Records successful tool selections. Each row has a `pattern_type` (e.g., "product_search", "graph_query"), a `query_pattern` (e.g., "find products by ingredient"), a `best_tool`, a `success_count`, and an `insight` string. The judge node (`judge.py:142-178`) upserts these records -- if the same pattern/tool combination already exists, it increments `success_count` and updates the insight.

**`failure_record`** (`schema.surql:202-207`): Records tool selection failures with the query, tool used, and error description.

The agent can read these tables via `ls /system/patterns/` (`fs_tools.py:496-511`), which returns the top 20 patterns by success count and the 10 most recent failures. This gives the agent visibility into its own historical performance -- though in practice, the system prompt's decision flow is the primary driver of tool selection.

The judge itself (`judge.py:108-139`) is a lightweight LLM call using GPT-5.4 at `temperature=0`. It receives the user query, tools called, and agent response, then returns a structured JSON verdict. The prompt (`judge.py:24-45`) asks for a verdict (`success`/`partial`/`failure`), pattern classification, and a one-sentence insight. The judge runs as a post-agent node in the LangGraph StateGraph, so it never blocks the user-facing response.

During SSE streaming, the frontend receives a `learn` event (`main.py:416-428`) if the judge recorded a new insight during the current turn. This is checked by querying `learned_pattern` for records created after the turn start timestamp.

---

## What SurrealDB Gets Right

Having built an entire application on a single SurrealDB instance for three days, here is an honest assessment.

**Graph traversal syntax is genuinely excellent.** Writing `SELECT ->placed->order->contains->product.{name, price} FROM customer:X` is more readable and more concise than the equivalent in Neo4j Cypher, and dramatically simpler than doing this with SQL JOINs. The arrow syntax reads like a sentence. Multi-hop queries that would require recursive CTEs in PostgreSQL are one-liners.

**Multi-model in one process works.** Having vector search, BM25, graph, and relational queries against the same data with the same connection is a real productivity win. No ETL pipeline, no data sync, no schema drift between services. For a hackathon, this is the difference between shipping and not shipping.

**Record links are typed.** The `source_id` field on `documents` is `option<record>`, not a string. SurrealDB knows it points to a real record. Relation tables with `IN customer OUT product` constraints prevent edge type errors at the schema level. This catches bugs that would silently corrupt data in a document store.

**SCHEMALESS and SCHEMAFULL coexist.** The `checkpoint` and `write` tables are `SCHEMALESS` because SurrealSaver writes arbitrary serialized state. Everything else is `SCHEMAFULL` with typed fields. This flexibility in a single database is unusual and useful.

**Where it falls short (SurrealDB 3.0 specifically):**

- The KNN `<|N|>` operator is broken, forcing us to use explicit `ORDER BY vector::similarity::cosine() DESC LIMIT N` -- functional but less efficient.
- BM25 `@1@` often returns empty results, requiring a `CONTAINS` fallback that loses ranking quality.
- `db.query()` returns flat lists, not the `[{"result": [...]}]` format from earlier versions. Every result handler needs `isinstance` checks.
- SurrealSaver does not auto-create its tables. Without manual `DEFINE TABLE checkpoint SCHEMALESS`, the checkpoint system crashes with an opaque error.

These are rough edges on a young database. The core multi-model thesis -- vector + keyword + graph + relational in one engine -- holds up well in practice. For a hackathon MVP, the tradeoff of fighting a few SurrealDB 3.0 quirks versus managing four separate databases was clearly worth it.
