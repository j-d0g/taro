# Taro.ai — Hackathon Build Log

> LangChain x SurrealDB Hackathon, London, March 6-8 2026

## What We Built

An e-commerce AI shopping assistant powered by **SurrealDB's multi-model engine** — vector search, BM25 keyword search, graph traversal, and relational queries through a single database. The agent uses a filesystem metaphor (SurrealFS) that maps bash commands to database operations, achieving near-perfect tool selection accuracy.

**Live demo**: Frontend at `:3001`, API at `:8002`, SurrealDB at `:8000`

---

## Architecture

```
Frontend (vanilla JS)  →  FastAPI + LangGraph ReAct Agent  →  SurrealDB 3.0
                              ↓
                    9 SurrealFS Tools (ls/cat/find/grep/tree/graph_traverse/...)
                              ↓
                    Vector (HNSW) + BM25 + Graph + Relational
```

- **Agent**: `create_react_agent` with GATHER→ACT→VERIFY constraint loop
- **Search**: Hybrid RRF fusion (vector + BM25), graph traversal (9 edge types)
- **Models**: Model-agnostic (GPT-4o/5.4, Claude 4.6, Gemini 3.1) via `get_llm()` registry
- **Memory**: Per-user distillation (POST /distill → LLM summarizes → stores context)
- **Checkpointing**: LangGraph MemorySaver for conversation persistence

## Data

| Entity | Count |
|--------|-------|
| Products | 431 unique (scraped from lookfantastic.com) |
| Customers | 2,526 synthetic profiles |
| Orders | 2,912 with line items |
| Reviews | 2,515 with sentiment |
| Verticals | 3 (Skincare, Haircare, Body & Fragrance) |
| Subcategories | 9 |
| Graph edges | 12 types |

---

## Plans Executed

### Plan 1: Streaming + Visible Reasoning
**Plan**: `docs/plans/2026-03-08-streaming-visible-reasoning.md`
**Status**: Complete, merged to main, pushed

| Feature | Details |
|---------|---------|
| SSE streaming | `POST /chat/stream` — real-time token-by-token responses via Server-Sent Events |
| Tool trace cards | Live tool execution cards with spinner → duration badge on completion |
| Streaming renderer | `createStreamingMessage()` — appends tokens, tool cards, product cards progressively |
| Graceful fallback | If streaming fails, falls back to blocking `POST /chat` automatically |
| DRY refactor | Extracted `_build_message_content()` helper shared by both endpoints |
| 7 new tests | Endpoint existence, SSE events, validation, user context, errors, multi-tool, product extraction |

**Files changed**:
- `taro-api/src/main.py` — SSE endpoint, `_sse()`, `_extract_products()`, `_build_message_content()`
- `taro-api/tests/test_stream.py` — 7 streaming tests
- `taro-web/js/api.js` — `sendChatMessageStream()` SSE client
- `taro-web/js/chat.js` — `createStreamingMessage()`, updated `sendMessage()`
- `taro-web/css/style.css` — cursor animation, tool spinner, duration labels

### Plan 2: Frontend UX
**Plan**: `docs/plans/2026-03-08-frontend-ux.md`
**Status**: Complete, merged to main, pushed

| Feature | Details |
|---------|---------|
| Copilot mode | Expandable 50vw side panel (toggle via ⇄ button), persisted in localStorage |
| Preference actions | Cart / Keep / Remove buttons on product cards in chat |
| Preference backend | `POST /preferences` + `GET /preferences/{user_id}` — maps to graph edges |
| Preference graph | 3 new edge types: `wants`, `interested_in`, `rejected` (customer→product) |
| Tool trace cleanup | Collapsible summary with human-readable labels (Vector Search, Graph, Keyword, etc.) |
| 4 new tests | Preference endpoint unit tests |

**Files changed**:
- `taro-api/schema/schema.surql` — 3 new edge definitions
- `taro-api/src/main.py` — `PreferenceRequest`, `POST /preferences`, `GET /preferences/{user_id}`
- `taro-api/tests/test_preferences.py` — 4 preference tests
- `taro-web/index.html` — chat header controls with expand button
- `taro-web/js/api.js` — `sendPreference()`
- `taro-web/js/chat.js` — copilot toggle, swipe actions, collapsible tool trace
- `taro-web/css/style.css` — copilot mode, preference buttons, collapsible trace

---

## Test Suite

**91 unit tests passing** (`make verify`)

| Test file | Tests | What it covers |
|-----------|-------|----------------|
| test_api.py | ~40 | All REST endpoints, chat, error handling |
| test_stream.py | 7 | SSE streaming endpoint |
| test_preferences.py | 4 | Preference CRUD |
| test_tools.py | 5 | Tool safety (write blocking, async, descriptions) |
| test_rrf.py | 4 | RRF fusion algorithm |
| test_raw_query.py | ~30 | SQL injection prevention |

Plus: `make smoke` (3 queries, ~1min), `make stress` (43 adversarial queries, ~20min)

---

## API Endpoints (18 total)

| Method | Path | Purpose |
|--------|------|---------|
| POST | /chat | Blocking chat with tool execution |
| POST | /chat/stream | SSE streaming chat |
| POST | /distill | Memory distillation |
| POST | /preferences | Save product preference (cart/keep/remove) |
| GET | /preferences/{user_id} | Get user preferences |
| GET | /products | List/search products |
| GET | /products/{id} | Product detail + also_bought + reviews |
| GET | /verticals | List verticals |
| GET | /categories | Category tree |
| GET | /customers/{id} | Customer profile |
| GET | /customers/{id}/profile | Rich customer profile |
| GET | /customers/{id}/orders | Order history |
| GET | /customers/{id}/recommendations | Personalized recommendations |
| GET | /models | Available LLM models |
| PUT | /models | Switch active model |
| GET | /prompts | Available prompt templates |
| PUT | /prompts | Switch active prompt |
| GET | /health | Health check |

---

## Graph Schema (12 edge types)

```
customer -placed-> order -contains-> product
                        -has_review-> review
product -belongs_to-> category -child_of-> category
product -also_bought-> product
product -supports_goal-> goal
product -contains_ingredient-> ingredient
product -related_to-> product (with reason field)
customer -wants-> product (cart)
customer -interested_in-> product (saved)
customer -rejected-> product (removed)
```

---

## SurrealFS Tools (9)

The "wow factor" — filesystem metaphor over SurrealDB that gives LLMs near-perfect tool selection:

| Tool | DB Operation | Example |
|------|-------------|---------|
| `ls` | List tables/records | `ls /products` |
| `cat` | Read record detail | `cat /products/abc123` |
| `tree` | Hierarchical view | `tree /categories/skincare` |
| `explore_schema` | INFO FOR DB/TABLE | `explore_schema` |
| `find` | Hybrid vector+BM25 (RRF) | `find "moisturizer for dry skin"` |
| `grep` | Keyword search (CONTAINS) | `grep "retinol" --type=product` |
| `graph_traverse` | Graph edge traversal | `graph_traverse product:x -also_bought->` |
| `surrealql_query` | Raw SurrealQL (read-only) | `SELECT * FROM product WHERE price < 30` |
| `web_search` | Tavily (lookfantastic.com) | External product research |

---

## Key Commits (March 8, 2026)

### Streaming
- `fda28ca` feat: add sendChatMessageStream() SSE client
- `eb575e3` feat: streaming-aware sendMessage with fallback to blocking
- `08d967f` feat: add streaming CSS — cursor, tool spinner, duration label
- `0c484d5` feat: add POST /chat/stream SSE endpoint with astream_events

### Frontend UX
- `85a79e7` schema: add wants, interested_in, rejected edges
- `eb3ba98` feat: add expandable copilot chat mode with localStorage persistence
- `577ce70` feat: clean up tool trace display with collapsible cards
- `5d8de1b` feat: add POST /preferences endpoint
- `61d4499` feat: add cart/keep/remove swipe actions to chat product cards

### Earlier (March 8)
- `825bb92` feat: enrich chat context with purchase history and proactive personality
- `bd73e60` Add 4 demo customer profiles with orders and reviews
- `08a718e` fix: make agent responses concise and conversational
- `433fd22` Harness engineering: 95% stress test pass rate

---

## Demo Flow (suggested)

1. Open http://localhost:3001 — show product grid with real lookfantastic products
2. Click chat bubble — show streaming response to "Best sellers under £30"
3. Watch tool trace cards appear with live spinners → completion durations
4. Click ⇄ to expand copilot mode — side-by-side browsing + chat
5. Ask "Compare retinol serums" — shows product cards with cart/keep/remove buttons
6. Click Cart on a product — saves preference to SurrealDB graph
7. Ask "What do customers who bought LANEIGE Water Bank also buy?" — graph traversal
8. Show SurrealDB Studio (`:8000`) — vector, graph, relational all in one DB

---

## Remaining Backlog

1. Multi-model optimisation (GPT-5.4 vs Claude 4.6 vs Gemini 3.1)
2. Review augmentation (parallel Haiku agents for synthetic reviews)
3. Rich mock data (FAQs, ingredient docs, deep user histories)
4. Repo audit & cleanup
