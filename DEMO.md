# Taro.ai Demo Guide

## Quick Start

1. **Start SurrealDB**: `surreal start --user root --pass root`
2. **Seed data**: `cd taro-api && make seed`
3. **Start API**: `cd taro-api && make serve`
4. **Open frontend**: Open `taro-web/index.html` in your browser

> The frontend works offline with mock data if the API isn't running.

## Demo Flow

### 1. Browse Products
- **Filter** by Fitness / Beauty / Wellness tabs
- **Search** by product name in the navbar search bar
- **Subcategory chips** appear when filtering by vertical

### 2. Product Detail
- **Click any product card** to open the split-screen detail modal
- See product info, star ratings, and description
- **"Customers also bought"** section shows graph-based co-purchase recommendations
- **"Recent reviews"** section shows order-linked reviews
- Click **"Ask the agent"** to open chat pre-filled with a product question

### 3. Customer Profile
- Click **Diego's avatar** (top-right) to open the profile panel
- View purchase history with order details
- See graph-based recommendations (via `also_bought` edges)
- Stats: total products, orders, and spend

### 4. Chat Agent
- Click the **chat bubble** (bottom-right) to open the AI assistant
- Try suggested prompts or ask freely:
  - "Best sellers under 30 pounds"
  - "Skincare routine for dry skin"
  - "Compare retinol serums"
- Watch **tool trace cards** showing SurrealDB multi-model search:
  - Vector (semantic search)
  - BM25 (keyword matching)
  - Graph (relationship traversal)
  - Relational (direct queries)

## Architecture Highlights

- **13 tools** organized by GATHER / ACT / VERIFY harness pattern
- **Hybrid search**: Client-side RRF fusion (vector + BM25)
- **Graph-as-filesystem**: Navigate `/users/`, `/products/{id}`, `/categories/`
- **Model-agnostic**: Swap between OpenAI, Anthropic, Google per request
- **SurrealDB multi-model**: Single database for vector, graph, relational, and full-text

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /products` | List products (with `?search=` and `?vertical=` params) |
| `GET /products/{id}` | Product detail with also_bought and reviews |
| `GET /customers/{id}` | Customer profile |
| `GET /customers/{id}/orders` | Customer order history |
| `POST /chat` | Send message to AI agent |
| `GET /models` | Available LLM providers |
| `GET /prompts` | Available system prompts |

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+ / FastAPI / LangGraph |
| Database | SurrealDB (vector + graph + relational) |
| AI Agent | LangGraph ReAct with 13 tools |
| Embeddings | OpenAI text-embedding-3-small (1536d) |
| Frontend | Vanilla HTML/CSS/JS |
| Design | lookfantastic-inspired editorial luxury theme |
| Tests | pytest (40 backend) + Playwright (9 E2E) |
