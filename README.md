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
# Edit config/.env with real keys (ask Jordan for the .env file)

# 3. Start SurrealDB (in a separate terminal)
make surrealdb

# 4. Seed the database with products, categories, FAQs
make seed

# 5. Run the server
make serve
# API live at http://localhost:8000

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

Studio URL: https://eu.smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024

### 2. FastAPI (programmatic)

```bash
make serve
```

Then send requests:

```bash
# Basic chat
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "recommend a protein powder"}'

# Multi-turn conversation (reuse thread_id)
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "which one is best for muscle building?", "thread_id": "THREAD_ID_FROM_ABOVE"}'

# Use a different model
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "hello", "model_provider": "anthropic", "model_name": "claude-sonnet-4-20250514"}'

# Use a different prompt persona
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "help me build muscle", "prompt_id": "coaching"}'
```

### 3. API Docs (Swagger)

Visit http://localhost:8000/docs for interactive API documentation.

---

## LangSmith Traces (Observability)

Every agent run is traced in LangSmith. To view:

1. Go to https://eu.smith.langchain.com
2. Open the **taro** project
3. Click any trace to see:
   - Which tools the agent called
   - What queries it sent to SurrealDB
   - The LLM's reasoning at each step
   - Token usage and latency

This is 10% of the hackathon judging criteria. Make sure `LANGSMITH_TRACING=true` is set in your `.env`.

---

## Frontend

The frontend lives in `taro-web/` and is a **standalone vanilla HTML/CSS/JS** application with a lookfantastic-inspired editorial luxury design. No build step required -- just open `taro-web/index.html` in your browser.

**Features:**
- **Product grid** with vertical tabs (Fitness / Beauty / Wellness) and subcategory chip filters
- **Split-screen product detail modal** with star ratings, co-purchase recommendations, and reviews
- **Customer profile panel** showing purchase history, graph-based recommendations, and spend stats
- **Chat agent drawer** with tool trace cards that visualize SurrealDB multi-model search in real time
- **Navbar search** for instant product filtering

The frontend works offline with embedded mock data. When the API is running (`make serve`), it connects to the backend for live data, AI chat, and graph-based recommendations.

---

## Testing

```bash
# Run backend tests (pytest)
cd taro-api && make verify

# Run E2E browser tests (Playwright)
cd taro-web && npx playwright test

# Run backend tests directly
cd taro-api && make test
```

- **Backend**: 40 pytest tests covering tools, API endpoints, and agent behavior
- **E2E**: 9 Playwright tests covering product browsing, search, detail modal, customer profile, and chat
- The `make verify` command is also used by the Claude Code Stop hook to gate changes

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat` | Send a message to the agent |
| `GET` | `/health` | Health check |
| `GET` | `/models` | List available LLM providers and models |
| `GET` | `/prompts` | List available system prompt templates |

### POST /chat

**Request:**

| Field | Type | Default | Description |
|---|---|---|---|
| `message` | string | *(required)* | User message |
| `thread_id` | string | auto-generated | Conversation thread ID (reuse for multi-turn) |
| `model_provider` | string | env `LLM_PROVIDER` | `openai`, `anthropic`, or `google` |
| `model_name` | string | env `LLM_MODEL` | Model identifier |
| `prompt_id` | string | `"default"` | System prompt template ID |

**Response:**

```json
{
  "reply": "Here are some great protein powders...",
  "thread_id": "user-123",
  "tool_calls": [
    {"name": "hybrid_search", "args": {"query": "protein powder"}}
  ]
}
```

---

## Search Tools (8 total)

The agent decides which tool to use based on the query. This is the core of the project.

| Tool | What it does | When the agent uses it |
|---|---|---|
| `hybrid_search` | Vector + BM25 fused via RRF | Default for product queries |
| `semantic_search` | Vector similarity (HNSW) | "Find something similar to X" |
| `keyword_search` | BM25 full-text | Exact names, SKUs, specific terms |
| `graph_traverse` | Walk RELATE edges | Categories, related products, hierarchies |
| `get_record` | Direct ID lookup | Fetch full details of a known record |
| `explore_schema` | DB introspection | Understanding available tables/fields |
| `web_search` | Tavily (myprotein.com) | Current promos, fallback when DB is empty |
| `surrealql_query` | Raw read-only SurrealQL | Aggregations, complex filters, GROUP BY |

---

## Makefile Commands

```bash
make install     # pip install -r requirements.txt
make surrealdb   # Start SurrealDB (in-memory, port 8001)
make seed        # Seed DB with products, categories, FAQs, graph edges
make serve       # Start FastAPI server (port 8000)
make studio      # Start LangGraph Studio (port 2024)
make test        # Run pytest
make verify      # Run tests (used by Claude Code Stop hook)
make health      # curl the health endpoint
make test-chat   # Send a test chat message
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
echo "You are a fitness coach." > src/prompts/templates/fitness.md
```

Immediately available via `"prompt_id": "fitness"` in chat requests.

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
    seed.py                # Seed script (5 products, 5 categories, 2 FAQs, 10 relations)
  src/
    main.py                # FastAPI app
    graph.py               # LangGraph ReAct agent + model registry
    db.py                  # SurrealDB async connection helper
    state.py               # Agent state (extends MessagesState)
    prompts/
      system.py            # File-based prompt loader
      templates/
        default.md         # Default system prompt with tool selection guide
        coaching.md        # Coaching persona
    tools/
      __init__.py          # Tool registry (ALL_TOOLS)
      hybrid_search.py     # Vector + BM25 via RRF
      semantic_search.py   # HNSW vector similarity
      keyword_search.py    # BM25 full-text
      graph_traverse.py    # RELATE edge traversal
      get_record.py        # Direct record lookup
      explore_schema.py    # Schema introspection
      web_search.py        # Tavily + SurrealDB caching
      raw_query.py         # Read-only SurrealQL
  tests/                   # 20 unit tests
```

---

## Tech Stack

- [LangGraph](https://github.com/langchain-ai/langgraph) -- ReAct agent orchestration
- [SurrealDB](https://surrealdb.com) -- multi-model database (vector, BM25, graph, relational)
- [FastAPI](https://fastapi.tiangolo.com) -- REST API
- [Tavily](https://tavily.com) -- web search (domain-scoped to myprotein.com)
- [LangSmith](https://smith.langchain.com) -- observability and tracing

---

**Taro.ai** @ LangChain x SurrealDB Hackathon, London, March 2026
