# Taro.ai — Frontend

SurrealDB-themed product catalogue with floating chat agent.

## Quick Start

```bash
# No build step needed — just open in browser
open index.html

# Or use any local server
python -m http.server 3000
# then visit http://localhost:3000
```

## File Structure

```
taro-web/
├── index.html          # Main HTML (navbar, grid, modal, chat, profile panel)
├── css/
│   └── style.css       # SurrealDB dark theme, all components
├── js/
│   ├── mock-data.js    # Mock products, reviews, also-bought, chat responses
│   ├── api.js          # API abstraction — flip USE_MOCK to false for real backend
│   ├── graph-viz.js    # Canvas-based graph traversal visualization in chat
│   ├── products.js     # Product grid rendering, subcategory chips, detail modal
│   ├── chat.js         # Chat panel, messages, tool trace cards, typing indicator
│   ├── profile.js      # Customer profile panel (purchase history + recommendations)
│   └── app.js          # Entry point — wires everything on DOMContentLoaded
└── README.md
```

## Connecting to Backend

1. Start the FastAPI server (`taro-api`) on `localhost:8000`
2. Open `js/api.js` and set `USE_MOCK = false`
3. The frontend expects the endpoints listed below

---

## API Endpoints

### `GET /products?vertical=&search=`

Returns a list of products, optionally filtered.

**Response:** `product[]` — each product has:
```json
{
  "id": "ce5b9184",
  "name": "Clinique Moisture Surge Hydration Set",
  "vertical": "Fitness",
  "subcategory": "Equipment",
  "price": 32.02,
  "avg_rating": 5.0,
  "image_url": "https://...",
  "description": "Intensive hydration set..."
}
```

### `GET /products/{id}`

Returns a single product with graph-traversed recommendations and reviews.

**Response:** product fields (above) plus:
```json
{
  "also_bought": [ ...product[] ],
  "reviews": [
    { "score": 5, "comment": "Amazing!", "sentiment": "positive" }
  ]
}
```

Notes:
- `also_bought` comes from `product->also_bought->product` graph edges
- `reviews` are connected through orders, not directly: `order->contains->product` + `order->has_review->review`. The backend must join these to return reviews for a given product.

### `GET /verticals`

Returns list of vertical names: `["Beauty", "Fitness", "Wellness"]`

Maps to `category` records where `level = 'vertical'`.

### `GET /subcategories?vertical=Fitness`

Returns subcategory names for a vertical: `["Equipment", "Tech", "Nutrition", ...]`

Maps to `category` records where `level = 'subcategory'` linked via `child_of` edge to the vertical.

### `GET /customers/{id}`

Returns customer profile with purchase history.

Purchase history is derived by traversing `customer->placed->order->contains->product`. Each order includes its products.

**Response:**
```json
{
  "id": "dfa8a1b5",
  "name": "Diego Carvalho",
  "city": "forquilhinha",
  "state": "SC",
  "orders": [
    { "order_id": "73fa93bf", "price": 104.65, "products": ["8d777214", "b8960327", "d92239d3", "728cfef9"] }
  ]
}
```

### `GET /customers/{id}/recommendations`

Returns recommended products via graph traversal:
`customer->placed->order->contains->product->also_bought->product`, excluding already-purchased items.

**Response:** `product[]`

### `POST /chat`

**Request:**
```json
{
  "message": "string",
  "thread_id": "uuid",
  "channel": "myprotein",
  "model_provider": "openai",
  "model_name": "gpt-4o",
  "prompt_id": "default"
}
```

**Response:**
```json
{
  "reply": "markdown string",
  "thread_id": "uuid",
  "tool_calls": [
    { "name": "hybrid_search",   "args": { "query": "...", "doc_type": "product" } },
    { "name": "semantic_search",  "args": { "query": "...", "table": "documents" } },
    { "name": "keyword_search",   "args": { "query": "...", "table": "documents" } },
    { "name": "graph_traverse",   "args": { "start": "product:abc", "edge": "also_bought" } },
    { "name": "get_record",       "args": { "record_id": "product:abc" } },
    { "name": "explore_schema",   "args": {} },
    { "name": "web_search",       "args": { "query": "..." } },
    { "name": "surrealql_query",  "args": { "query": "SELECT ..." } }
  ]
}
```

The frontend classifies each `tool_calls[].name` for color-coded display (see `api.js`):
- name contains `semantic` or `vector` → **vector** (magenta)
- name contains `graph` or `traverse` → **graph** (purple)
- name contains `keyword` or `hybrid` → **bm25** (green)
- everything else → **relational** (yellow)

### `GET /models`

Returns available model providers and models.

### `GET /prompts`

Returns available prompt template IDs.

### `GET /health`

Health check: `{ "status": "ok", "service": "taro-ai" }`

---

## SurrealDB Schema

The actual schema lives in `taro-api/schema/schema.surql`. Here's how it maps to the frontend.

### Tables

| Table | Purpose | Indexes |
|-------|---------|---------|
| `documents` | **Unified search index** for products + FAQs + articles. This is the main table the agent tools query. | HNSW vector (1536d cosine) on `embedding`, BM25 on `title` + `content`, filter on `doc_type` |
| `product` | Structured product data for graph queries, filtering, and direct lookups | — |
| `customer` | Customer profiles (name, city, state) | — |
| `order` | Orders with price | — |
| `review` | Reviews with score, comment, sentiment | HNSW vector on `embedding` (semantic search over review comments) |
| `category` | Verticals and subcategories. `level` field = `"vertical"` or `"subcategory"` | — |
| `web_cache` | Cached Tavily web search results (TTL-based) | Unique on `query` |
| `learned_pattern` | Agent self-improvement: maps query patterns to best tools. Fields: `pattern_type`, `query_pattern`, `best_tool`, `success_count` | — |
| `failure_record` | Failed tool invocations for the agent to learn from | — |

### Key design: `documents` vs `product`

Products exist in **two** places:
- **`product`** table — structured fields (price, rating, vertical, subcategory, image_url) used for filtering, graph edges, and direct lookups
- **`documents`** table (where `doc_type = 'product'`) — text content + embedding for semantic/BM25 search, linked back to the product via `source_id` (a native record link to `product:xyz`)

FAQs only live in `documents` (with `doc_type = 'faq'`). There is no separate `faq` table.

### `documents` fields

```
doc_type    — "product" | "faq" | "article"
title       — product name or FAQ question
content     — product description or FAQ answer
source_id   — record link back to product (e.g. product:ce5b9184), null for FAQs
metadata    — flexible object: { product_id, price, vertical, subcategory } for products;
              { category, intent } for FAQs
embedding   — float array (1536d, text-embedding-3-small)
```

### Graph Edges (6 total)

```
customer -placed->      order         (from orders.csv: customer_id + order_id)
order    -contains->    product       (from orders.csv: order_id + product_id)
order    -has_review->  review        (from reviews.csv: order_id + review_id)
product  -also_bought-> product       (derived: co-purchased by same customer, carries weight)
product  -belongs_to->  category
category -child_of->    category      (subcategory -> vertical)
```

### Key SurrealQL Queries

```surql
-- Product detail: "also bought" recommendations
SELECT ->also_bought->product.* FROM product:ce5b9184;

-- Product detail: reviews (through orders — no direct product->review link)
SELECT <-contains<-order->has_review->review.* FROM product:ce5b9184;

-- Customer purchase history (3-hop traversal, then aggregate)
SELECT ->placed->order->contains->product.* FROM customer:154e666b;

-- Customer recommendations (traverse to products, then co-purchases, exclude owned)
LET $owned = SELECT ->placed->order->contains->product FROM customer:154e666b;
SELECT ->placed->order->contains->product->also_bought->product.*
  FROM customer:154e666b
  WHERE id NOT IN $owned;

-- Semantic search on documents (products + FAQs)
SELECT *, vector::similarity::cosine(embedding, $query_vec) AS score
  FROM documents
  WHERE embedding <|5|> $query_vec;

-- BM25 keyword search on documents
SELECT *, search::score(1) AS score FROM documents
  WHERE title @1@ $query OR content @1@ $query;

-- Semantic search on reviews
SELECT *, vector::similarity::cosine(embedding, $query_vec) AS score
  FROM review
  WHERE embedding <|5|> $query_vec;

-- Category hierarchy: subcategories for a vertical
SELECT <-child_of<-category.* FROM category:fitness;
```

### Subcategories per Vertical

| Vertical  | Subcategories                                                    |
|-----------|------------------------------------------------------------------|
| Fitness   | Equipment, Tech, Nutrition, Accessories, Drinks                  |
| Beauty    | Skincare, Tools, Bath & Body, Fragrance, Body Care, Grooming     |
| Wellness  | Mindfulness, Family Health, Home Wellness, Sleep, Gifts, Lifestyle|

---

## SurrealDB Theme Colors

| Token     | Hex       | Usage                     |
|-----------|-----------|---------------------------|
| magenta   | `#ff00a0` | Primary accent, CTA       |
| purple    | `#9600ff` | Secondary accent, graph   |
| success   | `#00d4aa` | Fitness badge, BM25 tools |
| warning   | `#ffaa00` | Stars, relational tools   |
| bg-deep   | `#0E0C14` | Page background           |
| bg-card   | `#15131D` | Cards, navbar             |

## Tool Trace Color Coding

Each chat response shows the SurrealDB tools the agent used:

- **Magenta** — Vector (`semantic_search` via HNSW)
- **Purple** — Graph (`graph_traverse` via RELATE edges)
- **Green** — BM25 (`keyword_search`, `hybrid_search`)
- **Yellow** — Relational (`get_record`, `explore_schema`, `surrealql_query`, `web_search`)

## Graph Visualization Node Colors

| Node Type  | Color     |
|------------|-----------|
| query      | `#ff00a0` |
| product    | `#00d4aa` |
| customer   | `#9600ff` |
| category   | `#ffaa00` |
| review     | `#ff4466` |
| order      | `#5e9eff` |
| faq        | `#c77dff` |
| learned    | `#c77dff` |
