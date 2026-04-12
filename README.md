# Taro.ai

**SurrealDB Agentic Search Harness** -- a multi-model database meets LangGraph ReAct agent.

Demonstrates SurrealDB as a **unified backend** for vector search, BM25 keyword search, graph traversal, hybrid retrieval, raw queries, and conversation checkpointing -- all orchestrated by a LangGraph ReAct agent through a single FastAPI server.

---

## Quick Start (2 minutes)

```bash
# 1. Clone and install
git clone https://github.com/j-d0g/taro.git && cd taro/taro-api
pip install -r requirements.txt

# 2. Add your API keys
cp config/.env.example config/.env
# Fill in your API keys (see .env.example for required variables)

# 3. Start SurrealDB (in a separate terminal; persists under taro-api/data/surreal)
make surrealdb

# 4. Seed the database with products, categories, FAQs
make seed

# 5. Run the server
make serve
# API live at http://localhost:8002

# 6. Open the frontend
open ../taro-web/index.html
# Or just open taro-web/index.html in your browser

# 7. Test it
make test-chat
```

> For the full demo walkthrough (product browsing, customer profiles, chat agent), see **[DEMO.md](DEMO.md)**.

---

## Ways to Use the Agent

### 1. LangGraph Studio (visual, recommended for debugging)

```bash
make studio
```

Opens a browser UI where you can:
- Chat with the agent interactively
- See which tools it calls and why
- Inspect the full reasoning chain
- Replay and compare conversations

Studio URL: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024

### 2. FastAPI (programmatic)

```bash
make serve
```

Then send requests:

```bash
# Basic chat
curl -X POST http://localhost:8002/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "recommend a hydrating moisturizer"}'

# Multi-turn conversation (reuse thread_id)
curl -X POST http://localhost:8002/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "which one is best for sensitive skin?", "thread_id": "THREAD_ID_FROM_ABOVE"}'

# Use a different model
curl -X POST http://localhost:8002/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "hello", "model_provider": "anthropic", "model_name": "claude-sonnet-4-20250514"}'

# Use a different prompt persona
curl -X POST http://localhost:8002/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "help me with my skincare routine", "prompt_id": "coaching"}'
```

### 3. API Docs (Swagger)

Visit http://localhost:8002/docs for interactive API documentation.

---

## LangSmith Traces (Observability)

Every agent run is traced in LangSmith. To view:

1. Go to https://smith.langchain.com
2. Open the **taro** project
3. Click any trace to see:
   - Which tools the agent called
   - What queries it sent to SurrealDB
   - The LLM's reasoning at each step
   - Token usage and latency

Set `LANGSMITH_TRACING=true` in your `.env` to enable tracing.

---

## Frontend

The frontend lives in `taro-web/` and is a **standalone vanilla HTML/CSS/JS** application with a lookfantastic-inspired editorial luxury design. No build step required -- just open `taro-web/index.html` in your browser.

**Features:**
- **Product grid** with vertical tabs (Skincare / Haircare / Body & Fragrance) and subcategory chip filters
- **Split-screen product detail modal** with star ratings, co-purchase recommendations, and reviews
- **Customer profile panel** showing purchase history, graph-based recommendations, and spend stats
- **Chat agent drawer** with tool trace cards that visualize SurrealDB multi-model search in real time
- **Navbar search** for instant product filtering

The frontend works offline with embedded mock data. When the API is running (`make serve`), it connects to the backend for live data, AI chat, and graph-based recommendations.

---

## Testing

```bash
# Run unit tests (pytest, ~1s)
cd taro-api && make verify

# Quick smoke test (3 queries, ~1 min)
cd taro-api && make smoke

# Full adversarial stress test (43 queries, ~20 min)
cd taro-api && make stress

# E2E browser tests (Playwright)
cd taro-web && npx playwright test
```

- **Unit**: 89 pytest tests covering tools, API endpoints, and agent behavior
- **Smoke**: 3 representative queries testing find, graph traversal, and schema awareness
- **Stress**: 43 adversarial queries with pacing to avoid rate limits
- **E2E**: 9 Playwright tests covering product browsing, search, detail modal, customer profile, and chat

---

## API Endpoints (21 total)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat` | Send a message to the agent |
| `POST` | `/chat/stream` | SSE streaming (tool traces + tokens in real time) |
| `GET` | `/conversations` | List recent conversations |
| `GET` | `/conversations/{thread_id}` | Get conversation history |
| `POST` | `/distill` | Distill conversation into user memory |
| `GET` | `/products` | List products (filterable by vertical, search, brand) |
| `GET` | `/products/{product_id}` | Product detail with also-bought and reviews |
| `GET` | `/customers/{customer_id}` | Customer record |
| `GET` | `/customers/{customer_id}/profile` | Enriched profile with graph-derived data |
| `GET` | `/customers/{customer_id}/orders` | Order history with product details |
| `GET` | `/customers/{customer_id}/recommendations` | Graph-based product recommendations |
| `POST` | `/preferences` | Record preference (cart/keep/remove) |
| `GET` | `/preferences/{user_id}` | Get user's product preferences |
| `GET` | `/categories` | Category hierarchy (verticals + subcategories) |
| `GET` | `/categories/{category_id}` | Category detail with products |
| `GET` | `/goals` | List wellness/beauty goals |
| `GET` | `/goals/{goal_id}` | Goal detail with supporting products |
| `GET` | `/verticals` | Distinct product verticals |
| `GET` | `/models` | Available LLM providers and models |
| `GET` | `/prompts` | Available system prompt templates |
| `GET` | `/health` | Health check |

### POST /chat

**Request:**

| Field | Type | Default | Description |
|---|---|---|---|
| `message` | string | *(required)* | User message |
| `thread_id` | string | auto-generated | Conversation thread ID (reuse for multi-turn) |
| `user_id` | string | `null` | Customer ID for personalized context (e.g. `"diego_carvalho"`) |
| `model_provider` | string | env `LLM_PROVIDER` | `openai`, `anthropic`, or `google` |
| `model_name` | string | env `LLM_MODEL` | Model identifier |
| `prompt_id` | string | `"default"` | System prompt template ID |

**Response:**

```json
{
  "reply": "Here are some great moisturizers for you...",
  "thread_id": "user-123",
  "tool_calls": [
    {"name": "find", "args": {"query": "hydrating moisturizer"}}
  ],
  "products": [
    {"id": "abc123", "name": "CeraVe Moisturising Cream", "price": 12.50, "image_url": "..."}
  ]
}
```

---

## SurrealFS Tools (9 total)

The agent uses a **filesystem metaphor** over SurrealDB -- familiar bash commands (`ls`, `cat`, `find`, `grep`, `tree`) mapped onto multi-model database operations. The agent decides which tool to use based on the query.

| Tool | Phase | What it does | When the agent uses it |
|---|---|---|---|
| `ls` | GATHER | Browse entities at a path | Discover tables, list records |
| `cat` | GATHER | Read full record details | Inspect a specific product/customer |
| `tree` | GATHER | Recursive hierarchy view | Explore category trees |
| `explore_schema` | GATHER | DB introspection | Understanding available tables/fields |
| `find` | ACT | Hybrid RRF search (vector + BM25) | Default for product queries |
| `grep` | ACT | BM25 keyword search within scope | Exact names, brands, specific terms |
| `graph_traverse` | ACT | Walk RELATE edges | Related products, categories, customer history |
| `surrealql_query` | ACT | Raw read-only SurrealQL | Aggregations, complex filters, GROUP BY |
| `web_search` | ACT | Tavily (lookfantastic.com) | Current promos, fallback when DB is empty |

---

## Makefile Commands

```bash
# Setup
make install      # pip install -r requirements.txt
make surrealdb    # SurrealDB + RocksDB in ./data/surreal (use surrealdb-memory for ephemeral)
make seed         # Seed DB with products, categories, FAQs, graph edges

# Run
make serve        # Start FastAPI server (port 8002, foreground)
make restart      # Restart API in background
make frontend     # Start frontend on :3001
make studio       # Start LangGraph Studio (port 2024)

# Test
make verify       # Unit tests (89 tests, ~1s)
make smoke        # Quick smoke test (3 queries, ~1 min)
make stress       # Full stress test (43 queries, ~20 min)
make eval-basic   # Eval suite, basic assertions (10 queries, ~5 min)
make eval         # Eval suite, DeepEval LLM-as-judge

# Tools
make health       # API health check
make test-chat    # Send a test chat message
make test-distill # Test memory distillation flow
make conversations # List persisted conversations
make help         # Show all available commands
```

---

## Extending

### Add a new tool

1. Create `src/tools/my_tool.py`:

```python
from langchain_core.tools import tool
from db import get_db

@tool
async def my_tool(query: str) -> str:
    """Description the agent reads to decide when to use this tool."""
    async with get_db() as db:
        result = await db.query("SELECT * FROM my_table WHERE field = $query", {"query": query})
        return str(result)
```

2. Add to `src/tools/__init__.py`:

```python
from tools.my_tool import my_tool
ALL_TOOLS = [..., my_tool]
```

### Add a new prompt

Drop a `.md` file into `src/prompts/templates/`:

```bash
echo "You are a skincare expert." > src/prompts/templates/skincare.md
```

Immediately available via `"prompt_id": "skincare"` in chat requests.

### Add a new model provider

1. `pip install langchain-{provider}`
2. Add import + factory branch in `src/graph.py`
3. Set API key in `config/.env`

---

## Project Structure

```
taro-api/
  config/.env              # API keys and DB config (gitignored)
  config/.env.example      # Template for .env
  langgraph.json           # LangGraph Studio config
  Makefile                 # Dev commands
  requirements.txt         # Python deps
  schema/
    schema.surql           # SurrealDB tables, indexes, relations
    seed.py                # CSV-based seeder (1,890 products + demo customers)
  src/
    main.py                # FastAPI app entry point (~60 lines)
    agent.py               # Agent cache, user context builder
    models.py              # Pydantic request/response models
    helpers.py             # Shared utilities (product ID extraction, SSE formatting)
    graph.py               # LangGraph ReAct agent + model registry
    judge.py               # Judge feedback loop for refinement
    db.py                  # SurrealDB async connection helper
    state.py               # Agent state (extends MessagesState)
    routes/
      chat.py              # POST /chat, POST /chat/stream (SSE streaming)
      conversations.py     # GET /conversations, POST /distill
      products.py          # GET /products, GET /products/{id}
      customers.py         # GET /customers/{id}, /profile, /orders, /recommendations
      preferences.py       # POST /preferences, GET /preferences/{user_id}
      catalog.py           # GET /categories, /goals, /verticals
      config.py            # GET /models, /prompts, /health
    prompts/
      system.py            # File-based prompt loader
      templates/           # default.md, coaching.md, harness.md
    tools/
      __init__.py          # Tool registry (ALL_TOOLS, 9 tools)
      fs_tools.py          # SurrealFS core: ls, cat, grep, find, tree
      graph_traverse.py    # RELATE edge traversal
      explore_schema.py    # Schema introspection
      web_search.py        # Tavily + SurrealDB caching
      raw_query.py         # Read-only SurrealQL
  tests/                   # 89 unit tests
taro-web/                  # Vanilla HTML/CSS/JS frontend
```

---

## Tech Stack

- [LangGraph](https://github.com/langchain-ai/langgraph) -- ReAct agent orchestration
- [SurrealDB](https://surrealdb.com) -- multi-model database (vector, BM25, graph, relational)
- [FastAPI](https://fastapi.tiangolo.com) -- REST API
- [Tavily](https://tavily.com) -- web search (domain-scoped to lookfantastic.com)
- [LangSmith](https://smith.langchain.com) -- observability and tracing

---

## Built at

Built at the [LangChain x SurrealDB Hackathon](https://lu.ma/lcsqwmf3), London, March 2026.

---

## License

[MIT](LICENSE)
