# Taro.ai - SurrealDB Agentic Search Harness

## Project

E-commerce chatbot MVP: LangGraph ReAct agent with 8 SurrealDB search tools (vector, BM25, graph, hybrid RRF, schema introspection, direct lookup, raw SurrealQL, web fallback). Single SurrealDB backend for all data + checkpointing.

- **API code**: `taro-api/src/` (FastAPI + LangGraph agent)
- **Frontend**: `taro-web/` (placeholder)
- **Schema**: `taro-api/schema/schema.surql` + `taro-api/schema/seed.py`
- **Config**: `taro-api/config/.env`
- **Run**: `cd taro-api && make serve` | `make studio` | `make seed`

## Workflow: 5-Phase Agent Swarm

For ANY non-trivial task (3+ steps or architectural decisions), follow these phases. Use subagents liberally to keep the main context window clean.

### 1. Brainstorm

- Spawn a research agent to scan the repo for relevant patterns
- Propose 2-3 approaches with tradeoffs
- Write findings to `tasks/ideation.md` with decisions captured
- One task per subagent for focused execution

### 2. Plan

- Enter plan mode. Write detailed specs upfront to reduce ambiguity
- Spawn parallel agents: research (web/docs), codebase (scan files), docs (fetch references)
- Analyze plan for gaps, edge cases, and dependencies
- Output plan with checkable tasks, deps, and acceptance criteria to `tasks/todo.md`
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
- Update `tasks/lessons.md` with the pattern
- Write rules that prevent the same mistake recurring
- Future sessions: search lessons first before starting work

## Self-Improvement Loop

- After ANY correction from the user: update `tasks/lessons.md`
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for this project

## Verification Before Done

- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Run tests, check logs, demonstrate correctness
- The Stop hook (`make verify`) runs automatically -- respect its output

## Task Management

1. **Plan First**: Write plan to `tasks/todo.md` with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to `tasks/todo.md`
6. **Capture Lessons**: Update `tasks/lessons.md` after corrections

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Minimal code impact.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs.
- **Demand Elegance (Balanced)**: For non-trivial changes, pause and ask "is there a more elegant way?" Skip this for simple, obvious fixes -- don't over-engineer.
- **Autonomous Bug Fixing**: When given a bug report, just fix it. Point at logs, errors, failing tests -- then resolve them. Zero context switching required from the user.

## Tech Stack

- Python 3.11+, FastAPI, LangGraph, LangChain
- SurrealDB (vector HNSW + BM25 + graph RELATE + hybrid RRF)
- OpenAI embeddings (text-embedding-3-small, 1536 dims)
- Tavily search (domain-scoped to myprotein.com)
- LangSmith for observability
- `langgraph-checkpoint-surrealdb` for persistent state

## Key Patterns

- Tools use `async with get_db() as db:` for connection management
- All search tools return `source_id` to bridge `documents` -> `product` tables for graph traversal
- Hybrid search uses client-side RRF fusion (two separate queries, not `search::rrf()`)
- `doc_type` filtering uses parameterized queries (`$doc_type`), never f-string interpolation
- System prompts live in `src/prompts/templates/*.md` (file-based, swappable per request)
