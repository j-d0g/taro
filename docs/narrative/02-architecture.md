# SurrealFS: Filesystem Metaphor Over Multi-Model Search

> **Taro.ai** -- LangChain x SurrealDB Hackathon, London, March 6-8 2026

---

> **TL;DR**
>
> - 9 tools named after bash commands (`ls`, `cat`, `find`, `grep`, `tree`) give an LLM agent pre-trained intuition for navigating a SurrealDB graph -- no tool-use fine-tuning required.
> - A single SurrealDB instance serves as vector store, keyword index, graph database, relational store, checkpoint backend, conversation memory, and web cache -- seven roles, one connection string.
> - A GATHER-ACT-VERIFY harness (inspired by Codex/Claude Code research) structures every agent turn into orient, execute, confirm -- cutting hallucinated recommendations to near zero.

---

## System Architecture

```
                         Browser / API Client
                                |
                          POST /chat/stream
                                |
                       +--------v--------+
                       |    FastAPI       |  (main.py)
                       |  20 endpoints   |
                       |  SSE streaming   |
                       +--------+--------+
                                |
                    +-----------v-----------+
                    |  LangGraph StateGraph  |  (graph.py)
                    |                       |
                    |  +-----------------+  |
                    |  | ReAct SubGraph  |  |  create_react_agent()
                    |  | (agent node)    |  |
                    |  +--------+--------+  |
                    |           |            |
                    |  +--------v--------+  |
                    |  |   Judge Node    |  |  evaluate_turn()
                    |  +-----------------+  |
                    +-----------+-----------+
                                |
                  9 SurrealFS Tools (async)
                  |   |   |   |   |   |   |   |   |
                 ls  cat find grep tree  GT  ES  SQ  WS
                                |
                       +--------v--------+
                       |    SurrealDB    |
                       |  (single instance)  |
                       |  Vector + BM25 +   |
                       |  Graph + Relational |
                       +---------+----------+
                                 |
                    7 roles (see 03-surrealdb-deep-dive.md)
```

**GT** = `graph_traverse`, **ES** = `explore_schema`, **SQ** = `surrealql_query`, **WS** = `web_search`

The parent `StateGraph` (`graph.py:124-131`) has exactly two nodes. The `agent` node wraps LangGraph's `create_react_agent` with all 9 tools bound. The `judge` node runs after the agent completes, scoring tool selection quality and persisting verdicts to SurrealDB's `learned_pattern` and `failure_record` tables. The judge is observational only -- it returns empty messages so it never mutates conversation state (`graph.py:83`).

---

## The SurrealFS Tool Table

Every tool is a LangChain `@tool`-decorated async function. The naming convention is deliberate: LLMs already understand `ls`, `cat`, `find`, `grep`, and `tree` from pre-training on millions of bash sessions. This gives us zero-shot tool selection without fine-tuning.

| Tool | Bash Equiv. | Phase | DB Operation | Source |
|------|------------|-------|-------------|--------|
| `ls` | `ls /path` | GATHER | `SELECT` on routed table (13 path patterns) | `fs_tools.py:540-579` |
| `cat` | `cat /path` | GATHER/VERIFY | Same routes as `ls`, but with `verbose=True` for full field output | `fs_tools.py:582-612` |
| `tree` | `tree /path` | GATHER | Recursive `SELECT` with containment-edge expansion, capped at 100 lines | `fs_tools.py:1041-1080` |
| `explore_schema` | `SHOW TABLES` | GATHER | `INFO FOR DB` / `INFO FOR TABLE` | `explore_schema.py:10-68` |
| `find` | `find / -name` | ACT | Hybrid RRF: cosine vector + BM25 keyword, client-side fusion | `fs_tools.py:701-806` |
| `grep` | `grep term /scope` | ACT | BM25 keyword search with `CONTAINS` fallback | `fs_tools.py:615-698` |
| `graph_traverse` | N/A | ACT | 5 named traversal patterns over `RELATE` edges | `graph_traverse.py:33-112` |
| `surrealql_query` | `sqlite3` | ACT | Raw read-only SurrealQL (write keywords blocked via regex) | `raw_query.py:17-57` |
| `web_search` | `curl` | ACT | Tavily API scoped to lookfantastic.com, results cached in `web_cache` table | `web_search.py:14-68` |

The path router in `fs_tools.py:55-69` defines 13 regex patterns that map filesystem-style paths to handler functions. For example, `/users/diego_carvalho/orders/` matches the pattern `^/users/([^/]+)/orders/?$` and dispatches to `_handle_list_user_orders`, which runs a graph traversal query: `SELECT ->placed->order.* AS orders FROM customer:{user_id}`.

The key difference between `ls` and `cat` is a single boolean: both use the same path router and handler functions, but `ls` passes `verbose=False` (`fs_tools.py:576`) while `cat` passes `verbose=True` (`fs_tools.py:609`). In verbose mode, handlers fetch all fields, related records, and graph edge counts.

---

## GATHER -> ACT -> VERIFY Harness

The 3-phase harness is encoded in the system prompt (`prompts/templates/default.md`) and in the tool docstrings themselves. Each tool's docstring begins with a phase tag like `[GATHER]`, `[ACT]`, or `[GATHER/VERIFY]`.

### Phase 1: GATHER -- Orient in the data graph

The agent uses `ls`, `cat`, `tree`, or `explore_schema` to understand what data exists before searching. The system prompt explicitly says: "Use filesystem-style tools to understand the data landscape." This prevents the common failure mode where an LLM agent immediately calls a search tool without knowing what entities are available.

### Phase 2: ACT -- Execute informed queries

With context from GATHER, the agent picks the right search tool. The system prompt includes a decision flow (`default.md:40-49`) that maps query types to tools:

- "What do people also buy?" -> `graph_traverse(product_id, "also_bought")`
- Conceptual product search -> `find` (semantic + keyword hybrid)
- Exact name lookup -> `grep` with scope
- Stats/aggregations -> `surrealql_query` (read-only SELECT only)
- Nothing in DB -> `web_search` as last resort

### Phase 3: VERIFY -- Ground-truth before responding

The system prompt enforces verification: "NEVER recommend a product without having verified it with `cat`" (`default.md:57`). The `cat` tool serves double duty -- it is both a GATHER tool (for initial exploration) and a VERIFY tool (for confirming details before the agent responds). This is reflected in its docstring tag: `[GATHER/VERIFY]` (`fs_tools.py:584`).

The harness pattern draws from research on how Codex and Claude Code structure their tool usage. Rather than inventing a novel agent loop, we encode the pattern into prompt engineering and tool metadata, letting LangGraph's `create_react_agent` handle the underlying ReAct cycle.

---

## Graph Schema -- 12 Edge Types

All edges are defined as `TYPE RELATION` tables in SurrealDB (`schema.surql:133-176`), giving them first-class status with typed `IN` and `OUT` constraints.

| Edge | From -> To | Meaning | Extra Fields |
|------|-----------|---------|-------------|
| `placed` | customer -> order | Purchase event | -- |
| `contains` | order -> product | Line item in order | -- |
| `has_review` | order -> review | Customer feedback on order | -- |
| `belongs_to` | product -> category | Product classification | -- |
| `child_of` | category -> category | Hierarchy (subcategory -> vertical) | -- |
| `also_bought` | product -> product | Co-purchase signal (derived) | `weight` (int) |
| `supports_goal` | product -> goal | Product supports beauty goal | -- |
| `contains_ingredient` | product -> ingredient | Active ingredient link | `concentration` (string) |
| `related_to` | product -> product | Cross-reference | `reason` (string) |
| `wants` | customer -> product | Added to cart (live) | `added_at` (datetime) |
| `interested_in` | customer -> product | Saved for later (live) | `added_at` (datetime) |
| `rejected` | customer -> product | Not interested (live) | `reason`, `added_at` |

The last three edge types (`wants`, `interested_in`, `rejected`) are preference edges created during conversation via the `POST /preferences` endpoint (`main.py:947-980`). They form a live preference graph that evolves as the user interacts with the chatbot.

The `graph_traverse` tool exposes 5 of these edge types as named patterns (`graph_traverse.py:8-29`). Each pattern is a pre-built SurrealQL graph traversal query. For example, `customer_history` chains three edges: `customer ->placed-> order ->contains-> product`, returning the full purchase history in a single query.

---

## Data Architecture

The data model uses a deliberate two-layer design:

**Layer 1: `documents` table (search layer).** Triple-indexed for search: HNSW vector (1536d, cosine), BM25 full-text, and a `doc_type` filter index (`schema.surql:8-31`). Every searchable piece of content -- product descriptions, FAQs, articles -- lives here as a flat document with an `embedding` field. The `source_id` field is a native SurrealDB record link (e.g., `product:cerave_cleanser`) that bridges to Layer 2.

**Layer 2: `product`, `customer`, `order`, `review`, `category`, `goal`, `ingredient` tables (graph layer).** These are structured, schema-full tables connected by the 12 edge types above. They hold the relational and graph data: prices, ratings, order history, ingredient lists, category hierarchies.

The `find` tool queries Layer 1 (documents) for search, then every result includes a `source_id` reference (`fs_tools.py:799-801`) formatted as `-> /products/{id}`. This lets the agent (or the frontend) resolve search hits back to structured product records in Layer 2. The `cat` tool queries Layer 2 directly for full record details.

---

## Hybrid RRF Fusion

The `find` tool implements client-side Reciprocal Rank Fusion rather than using SurrealDB's built-in `search::rrf()`. This was a deliberate choice because SurrealDB 3.0's KNN operator `<|N|>` is broken, and the native RRF function depends on it.

The implementation (`fs_tools.py:86-113`) runs two separate queries against the `documents` table:

1. **Vector search**: `ORDER BY vector::similarity::cosine(embedding, $vec) DESC LIMIT N` (`fs_tools.py:743-750`)
2. **BM25 keyword search**: `WHERE content @1@ $query ORDER BY search::score(1) DESC LIMIT N` (`fs_tools.py:753-760`)

If BM25 returns empty (which happens often in SurrealDB 3.0), a `CONTAINS` fallback splits the query into words and uses `string::lowercase(content) CONTAINS string::lowercase(term)` (`fs_tools.py:770-781`).

The two result lists are then fused using the standard RRF formula: `score(d) = sum(1 / (k + rank))` with `k=60` (`fs_tools.py:86-113`). The fused results include both `vec_score` and `bm25_score` for transparency, along with the combined `rrf_score`.

Embedding calls go through a cache layer (`fs_tools.py:32-51`) that stores up to 128 query embeddings in an LRU dict, cutting OpenAI API calls roughly in half during stress testing.

---

## Model-Agnostic Design

The `get_llm()` function (`graph.py:50-74`) is a provider registry that returns the appropriate LangChain chat model based on a `provider` string:

- **OpenAI**: `ChatOpenAI` with `reasoning_effort` and `use_responses_api=True` for GPT-5.x reasoning summaries
- **Anthropic**: `ChatAnthropic` (optional import, graceful fallback)
- **Google**: `ChatGoogleGenerativeAI` (optional import, graceful fallback)

The default provider and model are set via environment variables (`LLM_PROVIDER`, `LLM_MODEL`). The FastAPI `/chat` and `/chat/stream` endpoints accept optional `model_provider` and `model_name` overrides in the request body (`main.py:39-40`), and agents are cached by config tuple to avoid rebuilding (`main.py:81-97`).

The `/models` endpoint (`main.py:1137-1144`) returns the available provider/model matrix, which the frontend uses to populate a model selector dropdown.

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Single agent vs. multi-agent | Single ReAct agent + judge | Simpler to debug; judge is observational only, never blocks the agent. Multi-agent adds latency and complexity for minimal gain at this scale. |
| Client-side RRF vs. `search::rrf()` | Client-side | SurrealDB 3.0's KNN `<|N|>` is broken. Client-side gives us control over fallback paths. |
| Filesystem naming convention | `ls`, `cat`, `find`, `grep`, `tree` | LLMs have strong pre-trained priors on bash commands. Zero-shot tool selection accuracy is high without fine-tuning. |
| `documents` + `product` two-layer | Separate search and graph layers | Search needs flat documents with embeddings; graph traversal needs structured records with typed edges. `source_id` bridges them. |
| SurrealDB for everything | Single database, 7 roles | Hackathon constraint: minimize infrastructure. SurrealDB's multi-model capabilities (vector, BM25, graph, relational) make this viable. |
| Preference edges created live | `wants`/`interested_in`/`rejected` | The graph evolves during conversation. Cart actions become edges immediately, enabling graph queries over user intent. |
| Judge as graph node, not middleware | Post-agent node in StateGraph | Keeps the agent's critical path clean. Judge failures never block responses. Verdicts accumulate in SurrealDB for offline analysis. |
| BM25 `CONTAINS` fallback | Always applied when `@1@` returns empty | SurrealDB 3.0's BM25 operator is unreliable. The fallback trades ranking quality for recall -- acceptable for a keyword search tool. |
