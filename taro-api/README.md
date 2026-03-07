# Taro.ai

**SurrealDB Agentic Search Harness** -- a multi-model database meets LangGraph ReAct agent.

A hackathon MVP that demonstrates SurrealDB as a **unified backend** for vector search, BM25 keyword search, graph traversal, hybrid retrieval, raw queries, and conversation checkpointing -- all orchestrated by a LangGraph ReAct agent through a single FastAPI server.

---

## Architecture

```
                         POST /chat
                             |
                        [ FastAPI ]
                             |
                   [ LangGraph ReAct Agent ]
                    /    |    |    |    \
                   /     |    |    |     \
    +----------------+   |    |    |   +-------------+
    | hybrid_search  |   |    |    |   | web_search  |
    | semantic_search|   |    |    |   | (Tavily)    |
    | keyword_search |   |    |    |   +-------------+
    +----------------+   |    |    |
         |          +----+    |    +----+
         |          |         |         |
         |   +-----------+ +------+ +----------------+
         |   | graph_    | | get_ | | surrealql_     |
         |   | traverse  | |record| | query          |
         |   +-----------+ +------+ +----------------+
         |          |         |         |
         v          v         v         v
    +-------------------------------------------+
    |              SurrealDB                    |
    |  Vector (HNSW) | BM25 | Graph (RELATE)   |
    |  Structured     | Cache | Checkpoints     |
    +-------------------------------------------+
```

---

## Features

- **8 search tools** in a single SurrealDB instance -- hybrid, semantic, keyword, graph, record lookup, schema explorer, web search, and raw SurrealQL
- **Persistent conversations** via `langgraph-checkpoint-surrealdb` -- resume any thread
- **Model-agnostic** -- swap between OpenAI, Anthropic, and Google models per request
- **Swappable system prompts** -- drop a `.md` file into `src/prompts/templates/`
- **Web search caching** -- Tavily results cached in SurrealDB to avoid redundant API calls
- **LangGraph Studio** compatible -- visualize and debug the agent graph
- **LangSmith observability** -- trace every tool call and LLM invocation

---

## Quick Start

### Prerequisites

- Python 3.11+
- [SurrealDB](https://surrealdb.com/install) installed locally
- OpenAI API key (for embeddings and default LLM)

### 1. Start SurrealDB

```bash
make surrealdb
# or: surreal start --user root --pass root memory
```

### 2. Install dependencies

```bash
cd app
make install
# or: pip install -r requirements.txt
```

### 3. Configure environment

Create `app/config/.env`:

```env
# LLM
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai          # openai | anthropic | google
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.3

# SurrealDB
SURREALDB_URL=ws://localhost:8000
SURREALDB_NAMESPACE=hackathon
SURREALDB_DATABASE=chatbot
SURREALDB_USER=root
SURREALDB_PASS=root

# Web search (optional)
TAVILY_API_KEY=tvly-...

# Observability (optional)
LANGSMITH_API_KEY=lsv2-...
LANGSMITH_TRACING=true

# Optional providers
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...
```

### 4. Seed the database

```bash
make seed
# or: python schema/seed.py
```

### 5. Run the server

```bash
make serve
# or: cd src && python main.py
```

The API is now live at `http://localhost:8000`.

---

## API Reference

### `POST /chat` -- Send a message

```bash
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "recommend a protein powder",
    "thread_id": "user-123",
    "model_provider": "openai",
    "model_name": "gpt-4o",
    "prompt_id": "default"
  }'
```

**Request body:**

| Field | Type | Default | Description |
|---|---|---|---|
| `message` | string | *(required)* | User message |
| `thread_id` | string | auto-generated UUID | Conversation thread ID |
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

### `GET /health` -- Health check

```bash
curl http://localhost:8000/health
# {"status": "ok", "service": "taro-ai"}
```

### `GET /models` -- List available models

```bash
curl http://localhost:8000/models
```

### `GET /prompts` -- List available prompt templates

```bash
curl http://localhost:8000/prompts
# {"prompts": ["coaching", "default"], "default": "default"}
```

---

## Tools Reference

| # | Tool | Description | Best For |
|---|---|---|---|
| 1 | `hybrid_search` | Combined vector + BM25 via Reciprocal Rank Fusion | Default for product queries and recommendations |
| 2 | `semantic_search` | Vector similarity using HNSW index | Conceptual queries, "find something similar" |
| 3 | `keyword_search` | BM25 full-text search | Exact product names, SKUs, specific terms |
| 4 | `graph_traverse` | Traverse RELATE edges (belongs_to, related_to, child_of) | Categories, related products, hierarchies |
| 5 | `get_record` | Direct lookup by SurrealDB record ID | Fetching full details of a known record |
| 6 | `explore_schema` | Database schema introspection (INFO FOR DB/TABLE) | Understanding available tables and fields |
| 7 | `web_search` | Tavily search scoped to myprotein.com, cached in SurrealDB | Current promotions, fallback when DB has no results |
| 8 | `surrealql_query` | Raw read-only SurrealQL (SELECT/INFO only) | Aggregations, complex filters, GROUP BY, JOINs |

---

## Extending the App

### Adding a New Tool

1. Create a new file in `src/tools/`, e.g. `src/tools/my_tool.py`:

```python
from langchain_core.tools import tool
from db import get_db

@tool
async def my_tool(query: str) -> str:
    """Description of what this tool does (the agent reads this)."""
    db = await get_db()
    try:
        result = await db.query("SELECT * FROM my_table WHERE field = $query", {"query": query})
        return str(result)
    finally:
        await db.close()
```

2. Register it in `src/tools/__init__.py`:

```python
from tools.my_tool import my_tool

ALL_TOOLS = [
    # ... existing tools ...
    my_tool,
]
```

The agent will automatically discover and use the new tool based on its docstring.

### Adding a New Prompt

Drop a Markdown file into `src/prompts/templates/`:

```bash
echo "You are a helpful assistant." > src/prompts/templates/minimal.md
```

It is immediately available via the `/prompts` endpoint and can be selected per request with `"prompt_id": "minimal"`.

### Adding a New Model Provider

1. Install the LangChain provider package:

```bash
pip install langchain-{provider}
```

2. Add the import and factory branch in `src/graph.py`:

```python
try:
    from langchain_{provider} import Chat{Provider}
except ImportError:
    Chat{Provider} = None

# Then in get_llm():
if provider == "{provider}":
    if Chat{Provider} is None:
        raise ImportError("Install langchain-{provider}")
    return Chat{Provider}(model=model, temperature=temperature)
```

3. Set the API key in `config/.env`.

---

## Project Structure

```
app/
  config/.env              # Environment variables (API keys, DB config)
  langgraph.json           # LangGraph Studio graph definition
  Makefile                 # Dev commands (serve, studio, seed, etc.)
  requirements.txt         # Python dependencies
  schema/
    schema.surql           # SurrealDB table/index definitions
    seed.py                # Seed script (products, categories, FAQs, graph edges)
  src/
    main.py                # FastAPI app (/chat, /health, /models, /prompts)
    graph.py               # LangGraph ReAct agent + model registry
    db.py                  # SurrealDB connection helper
    prompts/
      system.py            # File-based prompt loader (load_prompt, list_prompts)
      templates/
        default.md         # Default system prompt
        coaching.md         # Coaching persona prompt
    tools/
      __init__.py          # Tool registry (ALL_TOOLS)
      hybrid_search.py     # Vector + BM25 via RRF
      semantic_search.py   # HNSW vector similarity
      keyword_search.py    # BM25 full-text
      graph_traverse.py    # RELATE edge traversal
      get_record.py        # Direct record lookup
      explore_schema.py    # Schema introspection
      web_search.py        # Tavily with SurrealDB caching
      raw_query.py         # Read-only SurrealQL execution
```

---

## LangGraph Studio

Visualize and debug the agent graph interactively:

```bash
make studio
# or: langgraph dev --port 2024
```

The `langgraph.json` config points to `src/graph.py:graph`. Open `http://localhost:2024` to interact with the agent, inspect tool calls, and replay conversations.

---

## Built With

- [LangGraph](https://github.com/langchain-ai/langgraph) -- agent orchestration (ReAct pattern)
- [SurrealDB](https://surrealdb.com) -- multi-model database (vector, BM25, graph, relational)
- [FastAPI](https://fastapi.tiangolo.com) -- REST API
- [LangChain](https://github.com/langchain-ai/langchain) -- LLM integrations and tool framework
- [Tavily](https://tavily.com) -- web search API
- [LangSmith](https://smith.langchain.com) -- observability and tracing

---

## Team

**Taro.ai** @ LangChain x SurrealDB Hackathon, London, March 2026
