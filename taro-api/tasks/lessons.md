# Lessons Learned

Rules extracted from mistakes, corrections, and debugging sessions. Review at session start.

---

## SurrealDB

- `search::rrf()` takes arrays of result sets, NOT column aliases. Never use `ORDER BY search::rrf(col1, col2)`. Instead, run vector and BM25 as separate queries and fuse client-side with RRF algorithm.
- `SEARCH ANALYZER` syntax is SurrealDB 2.x. SurrealDB 3.x uses `FULLTEXT ANALYZER`. Check version with `surreal version` before writing schema.
- The `documents` table and `product` table are separate. Search tools query `documents`, graph edges connect `product`/`category`. Always include `source_id` in document records to bridge this gap.
- Never use f-string interpolation for user-facing query parameters (`doc_type`, etc.). Always use SurrealDB parameterized queries (`$doc_type`).
- Each `get_db()` call creates a new WebSocket connection. Use `async with get_db() as db:` pattern and do all queries within the same context.

## LangSmith

- LangChain auto-instruments if `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY` are in env. Map `LANGSMITH_*` vars to `LANGCHAIN_*` equivalents before any LangChain imports.

## Agent Prompts

- Always list ALL tools in the system prompt (was missing `surrealql_query` initially).
- Include negative guidance ("when NOT to use") -- LLMs route better with exclusion rules.
- Few-shot examples showing multi-tool chains dramatically improve tool selection quality.
- Include a VERIFICATION section telling the agent to validate results before answering.
