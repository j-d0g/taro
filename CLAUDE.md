# Taro.ai - SurrealDB Agentic Search Harness

## Project

E-commerce chatbot MVP: LangGraph ReAct agent with 9 SurrealFS tools (filesystem metaphor over SurrealDB's vector, BM25, graph models). Single SurrealDB backend for all data + checkpointing.

- **API code**: `taro-api/src/` — modular FastAPI (routes in `src/routes/`, agent in `src/agent.py`, models in `src/models.py`, helpers in `src/helpers.py`)
- **Frontend**: `taro-web/` (vanilla HTML/CSS/JS)
- **Schema**: `taro-api/schema/schema.surql` + `taro-api/schema/seed.py`
- **Config**: `taro-api/config/.env`
- **Run**: `cd taro-api && make serve` | `make studio` | `make seed`
- **Test**: `cd taro-api && make verify` (unit) | `make smoke` (3 quick queries) | `make stress` (43 adversarial queries)

## Workflow: 5-Phase Agent Swarm

> This workflow is optimized for AI-assisted development with Claude Code.

For ANY non-trivial task (3+ steps or architectural decisions), follow these phases. Use subagents liberally to keep the main context window clean.

### 1. Brainstorm

- Spawn a research agent to scan the repo for relevant patterns
- Propose 2-3 approaches with tradeoffs
- Write findings to `docs/internal/ideation.md` with decisions captured
- One task per subagent for focused execution

### 2. Plan

- Enter plan mode. Write detailed specs upfront to reduce ambiguity
- Spawn parallel agents: research (web/docs), codebase (scan files), docs (fetch references)
- Analyze plan for gaps, edge cases, and dependencies
- Output plan with checkable tasks, deps, and acceptance criteria to `docs/internal/todo.md`
- Check in with user before starting implementation

### 3. Work

- Swarm mode: spawn parallel agents per independent task
- System-wide check after every change (the Stop hook runs `make verify`)
- Incremental commits only when checks pass
- If something goes sideways, STOP and re-plan immediately -- don't keep pushing

### 4. Review

- Spawn multiple review agents across all changed areas
- Triage findings as P1 (must fix) / P2 (should fix) / P3 (nice to have)
- Validate no regressions across the codebase
- Ask: "Would a staff engineer approve this?"

### 5. Compound

- After ANY correction or bug fix: extract problem, solution, and prevention
- Update `docs/internal/lessons.md` with the pattern
- Write rules that prevent the same mistake recurring
- Future sessions: search lessons first before starting work

## Self-Improvement Loop

- After ANY correction from the user: update `docs/internal/lessons.md`
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for this project

## Verification Before Done

- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Run tests, check logs, demonstrate correctness
- The Stop hook (`make verify`) runs automatically -- respect its output

## Task Management

1. **Plan First**: Write plan to `docs/internal/todo.md` with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to `docs/internal/todo.md`
6. **Capture Lessons**: Update `docs/internal/lessons.md` after corrections

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Minimal code impact.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs.
- **Demand Elegance (Balanced)**: For non-trivial changes, pause and ask "is there a more elegant way?" Skip this for simple, obvious fixes -- don't over-engineer.
- **Autonomous Bug Fixing**: When given a bug report, just fix it. Point at logs, errors, failing tests -- then resolve them. Zero context switching required from the user.

## Tech Stack

- Python 3.11+, FastAPI, LangGraph, LangChain
- SurrealDB (vector HNSW + BM25 + graph RELATE + hybrid RRF)
- OpenAI embeddings (text-embedding-3-small, 1536 dims) -- cached in `fs_tools.py` LRU
- Tavily search (domain-scoped to lookfantastic.com)
- LangSmith for observability
- `langgraph-checkpoint-surrealdb` for persistent state

## Key Patterns

- `main.py` is a thin entrypoint (~60 lines) — routes use FastAPI `APIRouter` in `src/routes/`
- Shared helpers in `src/helpers.py`, agent cache + user context in `src/agent.py`, request/response schemas in `src/models.py`
- Tools use `async with get_db() as db:` for connection management
- All search tools return `source_id` to bridge `documents` -> `product` tables for graph traversal
- Hybrid search uses client-side RRF fusion (two separate queries, not `search::rrf()`)
- `doc_type` filtering uses parameterized queries (`$doc_type`), never f-string interpolation
- System prompts live in `src/prompts/templates/*.md` (file-based, swappable per request)

## SurrealDB 3.0 Rules (CRITICAL)

- `db.query()` returns flat lists, NOT `[{"result": [...]}]`. Always use `result or []` directly.
- KNN `<|N|>` operator is BROKEN. Use `ORDER BY vector::similarity::cosine(embedding, $vec) DESC LIMIT N`.
- BM25 `@1@` operator may return empty. Always add `CONTAINS` fallback path.
- `INFO FOR DB/TABLE` returns dict directly. Handle with `isinstance` checks for both formats.
- SurrealSaver v2.0.0 works but needs `checkpoint` + `write` SCHEMALESS tables pre-created. MemorySaver is the simpler default.
- After adding graph edges to schema, immediately update graph_traverse EDGE_TYPES and docstring.

## Integration Testing Rules

- **Always restart the API after code changes before running integration/stress tests.** Use `make restart`.
- **Never run 40+ LLM calls back-to-back without pacing.** Add 2s+ delay to avoid OpenAI rate limits.
- **Classify test failures by error type** (rate_limit vs logic vs tool_selection). Don't count rate limits as harness failures.
- **Use `make smoke` for quick validation** (3 queries, ~1 min) before running full `make stress` (43 queries, ~20 min).

## Custom Agents

- **`stress-test`**: Run adversarial stress test suite with pre-flight checks. Use via Task tool with `subagent_type: "stress-test"`.
- **`restart-api`**: Kill and restart the FastAPI server. Use via Task tool with `subagent_type: "restart-api"`.
