# Taro.ai — Project Changelog

Everything built so far, organized by phase.

---

## Phase 1: Backend Foundation (commits `2daaebf` → `314709e`)

**What:** LangGraph ReAct agent with 8 SurrealDB search tools, FastAPI server.

- Built the core agent: LangGraph ReAct loop with tool-calling LLM
- 8 SurrealDB tools:
  - `semantic_search` — HNSW vector similarity (1536d, cosine)
  - `keyword_search` — BM25 full-text search
  - `hybrid_search` — client-side RRF fusion of vector + BM25
  - `graph_traverse` — walk RELATE edges between records
  - `get_record` — direct record lookup by ID
  - `explore_schema` — introspect SurrealDB tables/fields
  - `surrealql_query` — raw SurrealQL for complex multi-hop queries
  - `web_search` — Tavily web fallback (domain-scoped to lookfantastic.com)
- FastAPI endpoints: `/chat`, `/health`, `/models`, `/prompts`
- File-based prompt registry (`src/prompts/templates/*.md`)
- Model-agnostic: supports OpenAI, Anthropic, Google via config
- 20 unit tests with `make verify` stop hook
- LangGraph Studio integration (`langgraph.json` + `pyproject.toml`)
- LangSmith observability

**Files:**
```
taro-api/src/main.py              — FastAPI app
taro-api/src/graph.py             — LangGraph agent graph
taro-api/src/state.py             — Agent state definition
taro-api/src/db.py                — SurrealDB connection manager
taro-api/src/tools/*.py           — All 8 tools
taro-api/src/prompts/             — System prompt templates
taro-api/tests/                   — Unit tests
taro-api/Makefile                 — serve, seed, verify, studio
```

---

## Phase 2: Dataset Preparation (commits `51f743c` → `4fa91fe`)

**What:** Curated e-commerce dataset from Olist, remapped to THG-style verticals.

- Trimmed Olist dataset: 5K customers, 3.9K products, 5.1K reviews, 5.8K orders
- Added Bitext FAQ dataset (26K Q&A pairs) for support-style queries
- Remapped 64 generic Olist categories → 3 verticals (Fitness, Beauty, Wellness) with 18 subcategories
- Generated realistic product names, prices, descriptions
- Overlaid 53 real THG product names + descriptions + image URLs via `apply_scraped.py`
- Replaced all Portuguese review text with English (template-matched to score)
- Fixed orphan records, filled all nulls
- Added integrity checker (`check_schema.py`)

**Files:**
```
Datasets/trimmed/customers.csv    — 5,153 customers (id, name, city, state)
Datasets/trimmed/products.csv     — 3,943 products (id, name, vertical, subcategory, price, avg_rating, description, image_url)
Datasets/trimmed/orders.csv       — 5,849 orders (order_id, customer_id, product_id, price)
Datasets/trimmed/reviews.csv      — 5,101 reviews (review_id, order_id, score, comment, sentiment)
Datasets/trimmed/payments.csv     — 5,394 payments (order_id, type, value)
Datasets/bitext_faq.csv           — 26K FAQ Q&A pairs
Datasets/DATA_README.md           — Dataset documentation
Datasets/remap_products.py        — Category remapping script
Datasets/apply_scraped.py         — Real product name/image overlay
Datasets/trim_dataset.py          — Original dataset trimming
Datasets/check_schema.py          — Integrity validation
```

---

## Phase 3: SurrealDB Schema + Seed Script (commits `1417ab6` → `11e43af`)

**What:** Designed multimodel SurrealDB schema and automated seeding from CSVs.

### Schema Design — 6 Graph Edges

```
customer  ──placed──>      order
order     ──contains──>    product
order     ──has_review──>  review
product   ──also_bought──> product    (derived, weighted)
product   ──belongs_to──>  category
category  ──child_of──>    category   (subcategory → vertical)
```

### Tables

| Table | Purpose | Indexes |
|-------|---------|---------|
| `product` | Structured product data | — |
| `customer` | Customer profiles | — |
| `order` | Orders with price | — |
| `review` | Reviews (score, comment, sentiment) | HNSW vector (1536d) |
| `category` | Verticals + subcategories | — |
| `documents` | Unified search index (products + FAQs) | HNSW vector + BM25 full-text |
| `web_cache` | Cached web search results | Unique on `query` |
| `learned_pattern` | Agent self-improvement patterns | — |
| `failure_record` | Failed tool invocations | — |

### Seed Script (`seed.py`)

7-step automated pipeline:
1. Categories (3 verticals + 18 subcategories + `belongs_to` + `child_of` edges)
2. Products (from CSV + `belongs_to` edges)
3. Customers (from CSV)
4. Orders (from CSV + `placed` + `contains` edges)
5. Reviews (from CSV + `has_review` edges + vector embeddings)
6. Also-bought edges (derived from co-purchase patterns with weights)
7. Documents (products + FAQs embedded via OpenAI, dual vector + BM25 indexed)

### Key Design Decisions

- **`documents` vs `product`**: Products exist in two places — `product` table for structured data/graph edges, `documents` table (where `doc_type = 'product'`) for semantic/BM25 search. Linked via `source_id` record link.
- **Reviews via orders, not products**: No direct product→review link. Path is `product<-contains<-order->has_review->review`. This matches real e-commerce data where reviews belong to order line items.
- **`also_bought` is derived**: Computed from co-purchase patterns (customers who bought X also bought Y). Edges carry a `weight` field (e.g., w=3 means 3 customers bought both).
- **Payments table kept in CSV but not seeded**: Simplified out of the schema since it doesn't serve the agent's search/recommendation use cases.

**Files:**
```
taro-api/schema/schema.surql      — Full SurrealDB schema definition
taro-api/schema/seed.py           — Automated seeding from CSVs
taro-api/src/tools/graph_traverse.py — Updated with 6 edge types
```

---

## Phase 4: Frontend (commits `11e43af` → `b2fb208`)

**What:** SurrealDB-themed product catalogue with chat agent panel, graph visualization, and customer profile.

### Features

- **Product grid** — filterable by vertical (Fitness/Beauty/Wellness), subcategory chips, search bar
- **Product detail modal** — image, price, rating, stars, "also bought" recommendations, reviews
- **Chat panel** — floating bubble, message history, tool trace cards (color-coded by SurrealDB query type), typing indicator, graph traversal visualization
- **Customer profile panel** — purchase history (order-based), graph-derived recommendations via `also_bought` edges
- **Graph visualization** — Canvas-rendered node/edge diagrams showing agent's SurrealDB traversal paths
- **Tool trace cards** — expandable cards showing which SurrealDB tools the agent used (vector=magenta, graph=purple, BM25=green, relational=yellow)

### Mock Data (aligned with real dataset)

- Real product IDs (8-char prefix of 32-char hex from CSV)
- Real customer: Diego Carvalho (`dfa8a1b5`) with 1 order containing 4 products
- Reviews keyed by `order_id` (matching `order->has_review->review` schema)
- Real `also_bought` weights from co-purchase data
- 3 mock chat responses with realistic tool call traces
- 3 graph visualizations using correct edge names

### Architecture

No build step — vanilla HTML/CSS/JS. `USE_MOCK` flag in `api.js` switches between mock data and live backend.

**Files:**
```
taro-web/index.html               — Main HTML (navbar, grid, modal, chat, profile)
taro-web/css/style.css            — SurrealDB dark theme (1232 lines)
taro-web/js/mock-data.js          — Mock data matching real dataset schema
taro-web/js/api.js                — API abstraction (mock/live toggle)
taro-web/js/products.js           — Product grid, filters, detail modal
taro-web/js/chat.js               — Chat panel, messages, tool traces
taro-web/js/profile.js            — Customer profile (orders + recommendations)
taro-web/js/graph-viz.js          — Canvas graph traversal visualization
taro-web/js/app.js                — Entry point
taro-web/README.md                — Full API contract + schema docs
```

---

## What's Left

### Must Do (for working demo)

- [ ] Run `make seed` to populate SurrealDB with real data
- [ ] Implement REST endpoints (`/products`, `/products/{id}`, `/customers/{id}`, etc.)
- [ ] Verify agent tools work against seeded data
- [ ] Set `USE_MOCK = false` in `js/api.js`

### Nice to Have (hackathon differentiators)

- [ ] Self-improvement loop: agent writes to `learned_pattern` after successful queries, reads before tool selection
- [ ] Failure recording: agent logs to `failure_record` on tool errors
- [ ] Live "Learned" counter in chat (currently mocked)
- [ ] Product images for all items (currently 53/3943 have real images)

---

## Repo Structure

```
taro_repo/
├── CLAUDE.md                     — AI assistant instructions
├── HACK.md                       — Hackathon notes
├── README.md                     — Project overview
├── CHANGELOG.md                  — This file
├── Datasets/
│   ├── trimmed/                  — Cleaned CSVs (customers, products, orders, reviews, payments)
│   ├── bitext_faq.csv            — 26K FAQ pairs
│   ├── DATA_README.md            — Dataset documentation
│   └── *.py                      — Data processing scripts
├── taro-api/
│   ├── schema/                   — SurrealDB schema + seed script
│   ├── src/                      — FastAPI + LangGraph agent + 8 tools
│   ├── tests/                    — 20 unit tests
│   ├── config/                   — Environment config
│   └── Makefile                  — serve, seed, verify, studio
└── taro-web/
    ├── index.html                — Main HTML
    ├── css/style.css             — SurrealDB dark theme
    ├── js/                       — 7 JS modules (mock-data, api, products, chat, profile, graph-viz, app)
    └── README.md                 — API contract + schema reference
```
