# Plan: Strip Chatbot to Hackathon MVP with SurrealDB Agentic Search Harness

## Context

Hackathon (LangChain x SurrealDB, London, March 6-8 2026, team "Taro.ai") requires stripping the production THG LOOKFANTASTIC chatbot down to a barebones MVP. The core idea: replace all backend services (gRPC, AlloyDB, Horizon API, Redis, BigQuery) with a single SurrealDB backend, and give the agent a rich toolkit of 7 search tools spanning SurrealDB's multi-model capabilities (vector, BM25, graph, hybrid). The agent reasons about WHICH tool to use per query.

## Target Architecture

```
FastAPI (/chat, /health) → LangGraph ReAct Agent (7 SurrealDB tools)
                            ↓
                     SurrealDB (single backend)
                     ├── Vector search (HNSW)
                     ├── Keyword search (BM25)
                     ├── Graph traversal (RELATE edges)
                     ├── Hybrid search (RRF fusion)
                     ├── Checkpoints (langgraph-checkpoint-surrealdb)
                     └── Learned patterns (self-improvement)
```

## Target File Structure

Fresh directory at repo root. The old `services/api/` is left intact for reference but not used.

```
app/
├── src/
│   ├── main.py                 # FastAPI entry point
│   ├── graph.py                # LangGraph ReAct agent + checkpointer
│   ├── state.py                # Minimal AgentState extending MessagesState
│   ├── db.py                   # SurrealDB connection singleton
│   ├── tools/                  # SurrealDB Agentic Search Harness
│   │   ├── __init__.py         # Exports ALL_TOOLS list
│   │   ├── semantic_search.py  # Vector similarity (HNSW)
│   │   ├── keyword_search.py   # BM25 full-text
│   │   ├── graph_traverse.py   # RELATE edge traversal
│   │   ├── hybrid_search.py    # Vector + BM25 via search::rrf()
│   │   ├── get_record.py       # Direct record lookup by ID
│   │   ├── explore_schema.py   # Schema introspection
│   │   └── web_search.py       # Tavily fallback + SurrealDB caching
│   ├── nodes/                  # LangGraph nodes (for extensions)
│   │   └── __init__.py
│   ├── prompts/
│   │   └── system.py           # System prompt with tool selection guide
│   └── utils/
│       ├── __init__.py
│       └── helpers.py          # get_last_user_message(), Timer (ported from services/api)
├── schema/
│   ├── schema.surql            # SurrealDB schema (tables, indexes, relations)
│   └── seed.py                 # Seed data script (products, categories, FAQs)
├── config/
│   └── .env                    # Environment variables
├── langgraph.json              # LangGraph Studio config
├── requirements.txt            # Minimal deps (~15 packages)
└── Makefile                    # Make targets: install, serve, studio, seed, surrealdb
```

The old `services/api/` remains as reference for patterns (prompts, reflection node, etc.) but all new work goes in `app/`.

## Dependencies

```
# Core framework
langgraph>=0.6.0
langchain>=0.3.0
langchain-openai>=0.3.0
langchain-core>=0.3.0

# SurrealDB
langchain-surrealdb
langgraph-checkpoint-surrealdb
surrealdb

# External search
langchain-tavily

# API layer
fastapi
uvicorn[standard]
pydantic>=2.0

# Config & logging
python-dotenv
loguru

# Observability
langsmith
```

~15 direct deps vs 182 in the existing `requirements.txt`.

## Existing Patterns to Port

| Pattern | Source File | Port To |
|---------|-----------|---------|
| `get_last_user_message()` | `services/api/src/utils/common.py` | `app/src/utils/helpers.py` |
| `Timer` context manager | `services/api/src/utils/timing.py` | `app/src/utils/helpers.py` |
| `create_react_agent` usage | `services/api/src/agents/nodes/product_suggestion_subgraph.py:53` | `app/src/graph.py` |
| Reflection node pattern | `services/api/src/agents/nodes/reflection.py` | `app/src/nodes/reflection.py` (Phase 6) |
| State-reset for multi-turn | `services/api/src/agents/nodes/input_preprocessor.py` | Reference if extending beyond ReAct |

## SurrealDB Tool Harness Design

Each tool is a `@tool`-decorated function in its own file. The agent receives all 7 tools and decides which to use.

| Tool | SurrealDB Mode | Use Case | Implementation |
|------|---------------|----------|----------------|
| `semantic_search` | Vector (HNSW) | Conceptual queries: "something for recovery" | `SurrealDBVectorStore.similarity_search_with_score()` |
| `keyword_search` | Full-text (BM25) | Exact terms: "Impact Whey Protein" | SurrealQL `WHERE content @1@ $query` |
| `graph_traverse` | Graph (RELATE) | Relationships: "related products", "same category" | SurrealQL arrow syntax `->edge->` |
| `hybrid_search` | Vector + BM25 (RRF) | Default for general queries | `search::rrf()` fusion |
| `get_record` | Direct lookup | Already have a record ID | `db.select(record_id)` |
| `explore_schema` | Schema introspection | Discover what data exists | `INFO FOR DB` / `INFO FOR TABLE` |
| `web_search` | External (Tavily) | Last resort fallback | `TavilySearch` + cache to SurrealDB |

## SurrealDB Schema Overview

```sql
-- Core tables
documents     -- Unified searchable content (HNSW vector + BM25 full-text indexes)
product       -- Structured product data with embeddings
category      -- Hierarchical categories

-- Graph edges (RELATE tables)
belongs_to    -- product → category
child_of      -- category → category (hierarchy)
related_to    -- product → product (with relation_type)

-- Self-improvement
learned_pattern  -- Persisted agent learnings
failure_record   -- Failed query traces

-- Caching
web_cache     -- Cached Tavily search results
```

## Implementation Steps

### Phase 1: Foundation (~30 min)

1. **Create `app/` directory structure** (src/, schema/, config/, src/tools/, src/nodes/, src/prompts/, src/utils/)
2. **Write `app/requirements.txt`** with minimal deps listed above
3. **Write `app/config/.env`** - SurrealDB, OpenAI, Tavily, LangSmith keys
4. **Write `app/src/db.py`** - SurrealDB connection singleton (`@lru_cache`, reads env vars, returns `Surreal` instance + `get_db_config()` dict for SurrealSaver)

### Phase 2: Schema + Seed Data (~30 min)

5. **Write `app/schema/schema.surql`** - All tables, indexes (HNSW + BM25), RELATE edge tables
6. **Write `app/schema/seed.py`** - Seeds ~5 products, ~5 categories, graph relations, ~2 FAQs. Generates embeddings via OpenAI. Standalone: `python schema/seed.py`
7. **Verify**: Start SurrealDB, run seed, query manually

### Phase 3: Tool Harness (~1.5 hours)

Build simplest tools first, progressively more complex:

8. **`app/src/tools/get_record.py`** - Direct record lookup
9. **`app/src/tools/explore_schema.py`** - Schema introspection
10. **`app/src/tools/keyword_search.py`** - BM25 full-text search
11. **`app/src/tools/semantic_search.py`** - Vector similarity search
12. **`app/src/tools/graph_traverse.py`** - Graph edge traversal
13. **`app/src/tools/hybrid_search.py`** - RRF fusion search (flagship)
14. **`app/src/tools/web_search.py`** - Tavily + SurrealDB caching
15. **`app/src/tools/__init__.py`** - Exports `ALL_TOOLS` list

### Phase 4: LangGraph Wiring (~30 min)

16. **Write `app/src/state.py`** - `AgentState(MessagesState)` with optional `channel`, `locale`
17. **Write `app/src/prompts/system.py`** - System prompt with tool selection guide
18. **Write `app/src/graph.py`** - `build_graph()` with `create_react_agent` + `SurrealSaver` checkpointer. Module-level `graph = build_graph()` for LangGraph Studio
19. **Write `app/langgraph.json`** - Point to `./src/graph.py:graph`
20. **Test in LangGraph Studio**: `langgraph dev --port 2024`

### Phase 5: API Layer (~30 min)

21. **Write `app/src/main.py`** - FastAPI with `POST /chat` and `GET /health`
22. **Write `app/src/utils/helpers.py`** - Port utilities from existing codebase
23. **Write `app/Makefile`** - `install`, `serve`, `studio`, `seed`, `surrealdb` targets
24. **Test**: `curl -X POST localhost:8000/chat -d '{"message":"recommend a protein powder"}'`

### Phase 6: Self-Improvement (stretch, if time permits)

25. Add `app/src/nodes/reflection.py` - post-response analysis, writes learnings to SurrealDB
26. Extend graph to custom `StateGraph`: `agent_node → reflection_node → END`

## Key Design Decisions

- **`create_react_agent` over custom StateGraph**: Proven pattern from existing codebase. One line gives full tool loop. Extend later if needed.
- **Raw SurrealQL for most tools**: `langchain-surrealdb` only exposes vector store, not BM25/hybrid/graph/schema. Raw queries give full control.
- **`ChatOpenAI` over `AzureChatOpenAI`**: Provider-agnostic. Works with OpenAI, Azure, or any compatible API.
- **Single `documents` table + separate `product` table**: Unified search across all content types via `doc_type` filter, with structured product data separate for graph relations.
- **`SurrealSaver` over `MemorySaver`**: Persists checkpoints to SurrealDB (20% judging on persistent state). SurrealDB = truly single backend.

## Hackathon Scoring Alignment

| Criteria | Weight | How We Score |
|----------|--------|--------------|
| Structured Memory (SurrealDB) | 30% | Knowledge graph with evolving context, vector + graph + BM25 hybrid queries, all in one DB |
| Agent Workflow (LangGraph) | 20% | ReAct agent with 7-tool routing, conditional tool selection, LangGraph Studio |
| Persistent Agent State | 20% | SurrealDB checkpointer, resumable conversations, self-improvement loop persists learnings |
| Practical Use Case | 20% | E-commerce product recs that improve over time |
| Observability | 10% | LangSmith traces showing agent tool selection reasoning |

## Verification

All commands from `app/` directory:

1. Start SurrealDB: `surreal start --user root --pass root memory`
2. Install deps: `pip install -r requirements.txt`
3. Seed data: `python schema/seed.py`
4. Start server: `cd src && python main.py`
5. Test chat: `curl -X POST localhost:8000/chat -H 'Content-Type: application/json' -d '{"message":"recommend a protein powder"}'`
6. Test multi-turn: reuse same `thread_id` in subsequent requests
7. Test LangGraph Studio: `langgraph dev --port 2024`
8. Verify LangSmith traces at https://smith.langchain.com
9. Verify tool diversity: ask different query types and check different tools are invoked
