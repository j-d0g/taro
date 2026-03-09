# Taro.ai Hackathon Retrospective

> LangChain x SurrealDB Hackathon, London, March 6-8 2026
> 5-person team, 48 hours, 168 commits

---

## 1. The Build Story

### Friday Evening — Architecture on WhatsApp

The team formed Friday night. Before anyone opened an editor, we spent two hours on WhatsApp debating architecture. The question: how do you make an LLM reliably query a multi-model database (vector, BM25, graph, relational) without fumbling tool selection?

Someone suggested naming tools after bash commands. The logic: LLMs already have deep priors on `ls`, `cat`, `find`, `grep`, and `tree`. They know `ls` lists things, `cat` reads things, `find` searches things. If we map SurrealDB operations onto those names, the model should pick the right tool without needing elaborate descriptions.

That insight became **SurrealFS** — a filesystem metaphor over SurrealDB's multi-model engine. It turned out to be the single highest-leverage decision of the hackathon.

### Saturday — Backend Foundation

Saturday was heads-down backend work:

- **Morning**: SurrealDB schema design. One `documents` table with HNSW vector indexes and BM25 full-text indexes, bridged to structured `product` records via `source_id`. Twelve edge types connecting products, customers, orders, reviews, categories, goals, and ingredients.
- **Afternoon**: LangGraph `create_react_agent` wired up with 8 tools (later consolidated to 9). FastAPI endpoints for chat, products, customers, categories. Hybrid search with client-side RRF fusion because SurrealDB 3.0's `search::rrf()` was broken.
- **Evening**: Data seeding — 431 products scraped from lookfantastic.com, 2,526 synthetic customer profiles, 6,862 orders, 3,247 reviews. The seeder built the full graph (co-purchase edges, ingredient links, goal mappings) in one pass.

By midnight Saturday we had an agent that could answer product questions, traverse the graph, and run hybrid search. No frontend, no streaming, no persistence.

### Sunday Morning — Frontend Sprint

Sunday morning was a parallel sprint: one track on the vanilla JS frontend, one on SSE streaming, one on conversation persistence.

The frontend was deliberately kept vanilla — HTML, CSS, JavaScript, no build step. Product cards, streaming token rendering, tool trace cards with live spinners, copilot side-panel mode. Everything wired to the API in under 4 hours.

SSE streaming was the riskier bet. We added `POST /chat/stream` using LangGraph's `astream_events`, rendering tokens and tool calls as Server-Sent Events. The frontend consumed them with a progressive renderer that appended tokens, tool cards, and product cards in real time. Graceful fallback to blocking `/chat` if streaming failed.

Submission happened around noon Sunday.

### Sunday Afternoon — Stress Testing and Hardening

After submission, we ran the first adversarial stress test: **51.1% pass rate** (23/45). Brutal.

The failures fell into three buckets:
1. **Broken SurrealDB operators** — KNN `<|N|>` and BM25 `@1@` silently returning errors or empty arrays
2. **Tool confusion** — 13 tools with overlapping names (find vs hybrid_search vs semantic_search)
3. **No verification loop** — the agent hallucinated answers without checking them

Four hours of hardening followed. We consolidated 13 tools down to 9, fixed every SurrealDB 3.0 incompatibility, rewrote the system prompt with explicit GATHER→ACT→VERIFY phases, and added rate-limit retry logic.

Final score: **95.3% pass rate** (41/43). The two remaining failures were one OpenAI rate limit and one false-positive test assertion.

---

## 2. Key Technical Decisions

### SurrealFS: Bash Commands Over a Database

The defining pattern of the project. Instead of inventing tool names like `hybrid_search`, `get_record`, `keyword_search`, we used names LLMs already understand:

```python
ALL_TOOLS = [
    # GATHER phase: orient in the data graph
    ls,                 # Browse entities at a path (like bash ls)
    cat,                # Read full record details (like bash cat)
    tree,               # Recursive hierarchy view (like bash tree)
    explore_schema,     # Schema introspection (fields, indexes)
    # ACT phase: execute informed queries
    find,               # Hybrid RRF search: semantic + keyword (primary search)
    grep,               # BM25 keyword search within a scope (like bash grep)
    graph_traverse,     # Focused graph patterns (also_bought, ingredients, ...)
    surrealql_query,    # Raw read-only SurrealQL for aggregations
    web_search,         # Tavily web fallback with SurrealDB caching
]
```

Tool selection accuracy went from 44% (with descriptive names) to 100% (with bash names). The LLM knew exactly when to `ls` vs `find` vs `grep` because it has seen millions of bash sessions in training. We did not teach it anything new — we spoke its language.

This is the core insight: **context engineering beats prompt engineering**. Instead of writing longer prompts explaining when to use each tool, we changed the names so no explanation was needed.

### GATHER→ACT→VERIFY Constraint Loop

Every agent interaction follows three phases enforced via the system prompt:

| Phase | Purpose | Tools |
|-------|---------|-------|
| GATHER | Orient in the data graph | `ls`, `cat`, `tree`, `explore_schema` |
| ACT | Execute informed queries | `find`, `grep`, `graph_traverse`, `surrealql_query`, `web_search` |
| VERIFY | Ground-truth before responding | `cat` (re-read), `graph_traverse` (confirm) |

The VERIFY phase was critical. Without it, the agent would run a search, get five results, and confidently recommend products it had not actually read. With it, the agent calls `cat /products/{id}` on each recommendation to verify price, description, and availability before responding.

The constraint is soft — it lives in the system prompt, not in code. But with worked examples showing the loop in action, compliance was near-total.

### Hybrid Search with Client-Side RRF

SurrealDB 3.0's `search::rrf()` function was broken in our version. Rather than wait for a fix, we implemented client-side Reciprocal Rank Fusion:

```python
def _rrf_fuse(vector_results: list, bm25_results: list, k: int = 60) -> list[dict]:
    """Fuse two ranked result lists using Reciprocal Rank Fusion."""
    scores: dict[str, float] = {}
    docs_by_id: dict[str, dict] = {}

    for rank, doc in enumerate(vector_results):
        doc_id = str(doc.get("id", ""))
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
        if doc_id not in docs_by_id:
            docs_by_id[doc_id] = doc

    for rank, doc in enumerate(bm25_results):
        doc_id = str(doc.get("id", ""))
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
        if doc_id not in docs_by_id:
            docs_by_id[doc_id] = doc

    ranked_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return [dict(**docs_by_id[did], rrf_score=scores[did]) for did in ranked_ids]
```

Two separate queries (vector similarity + keyword CONTAINS), fused client-side. Not elegant, but reliable — and it meant we were not blocked by a third-party bug.

### Unified Documents Table

A subtle but important design: all searchable content lives in a single `documents` table with embeddings and BM25 indexes. Each document has a `source_id` that links back to its structured record (product, category, goal, etc.) and a `doc_type` for filtering.

This meant we only needed one `find` tool and one `grep` tool — they searched the same table regardless of entity type. The `source_id` then bridged into the graph for traversal.

### Model-Agnostic Registry

We built `get_llm()` as a provider-agnostic factory from day one:

```python
def get_llm(provider="openai", model="gpt-5.4", temperature=0.3):
    if provider == "openai":
        return ChatOpenAI(model=model, temperature=temperature, reasoning_effort="low")
    if provider == "anthropic":
        return ChatAnthropic(model=model, temperature=temperature)
    if provider == "google":
        return ChatGoogleGenerativeAI(model=model, temperature=temperature)
```

This let us swap between GPT-4o, GPT-5.4, Claude Sonnet 4, and Gemini 3.1 during testing. Different models exposed different bugs — GPT-4o was polite and avoided edge cases; GPT-4o-mini was aggressive and found two real bugs that GPT-4o masked.

---

## 3. How Claude Code Was Used

Claude Code was our primary development tool throughout the hackathon. Several patterns emerged.

### Custom Agents for Operations

We defined two custom agents in `.claude/agents/`:

- **`stress-test`**: Pre-flight checks (is the API running? is SurrealDB reachable?), then runs the 43-query adversarial suite with rate-limit pacing and failure classification.
- **`restart-api`**: Kills any running FastAPI process and restarts it. Used before every integration test run.

These removed the operational tax of manually managing the server during rapid iteration.

### Git Worktrees for Parallel Features

We used git worktrees extensively — up to 8 active at peak (consolidated to 4 by the end). Each feature branch got its own worktree: streaming, frontend UX, harness stress testing, tool merging. This let us run parallel Claude Code sessions without branch conflicts.

### Stop Hook as CI Gate

The CLAUDE.md `make verify` stop hook ran automatically before every commit. If any of the 93 unit tests failed, the commit was blocked. This caught regressions immediately — we never committed broken code.

### Parallel Agent Swarms

For complex tasks (like the harness rewrite), we spawned parallel agent swarms:
- A research agent scanning external documentation
- A codebase agent scanning our own files for patterns
- An implementation agent writing the code
- A review agent triaging changes as P1/P2/P3

The 5-phase workflow (Brainstorm → Plan → Work → Review → Compound) was codified in CLAUDE.md and followed for every non-trivial task.

### Bug-to-Lesson Extraction

After every bug fix, we extracted the pattern:

1. **Problem**: What went wrong (with specific code/error)
2. **Solution**: What fixed it
3. **Prevention**: What rule prevents recurrence

This produced 13 documented lessons over the hackathon. Each lesson became a rule in CLAUDE.md or a code pattern that future sessions could reference. The self-improvement loop was simple but effective — the same class of bug never occurred twice.

---

## 4. What Worked Well

### Filesystem Metaphor as Context Engineering

The single biggest win. By naming tools after bash commands, we borrowed the LLM's existing training on Unix systems. Tool selection became a non-problem. The model intuitively knew `ls /products/` lists products, `cat /products/xyz` reads a product, and `find "moisturizer"` searches for one.

This is context engineering in its purest form: instead of writing more prompt text to explain the tools, we changed the tools so they needed no explanation.

### Adversarial Stress Testing with Failure Classification

The 43-query stress test suite covered 8 categories: tool selection, multi-hop reasoning, edge cases, adversarial attacks, graph reasoning, schema awareness, personalization, and failure recovery.

Critically, we classified failures by root cause — not just pass/fail. This revealed that 15 of 17 initial failures were OpenAI rate limits, not harness bugs. Without classification, we would have wasted hours debugging phantom logic errors.

| Round | Pass Rate | Key Insight |
|-------|-----------|-------------|
| Round 1 | 51.1% | Wrong tools, HTTP 500s, no graph traversal |
| Round 2 | 68.9% | Tests using old tool names |
| Round 3 | 60.5% | All failures were OpenAI rate limits |
| Round 4 | 95.3% | 1 rate limit, 1 false-positive assertion |

### Self-Improvement Loop

The bug→lesson→prevention cycle kept our error rate dropping. Lesson L1 (SurrealDB broken operators) caught 3 separate bugs. Lesson L6 (rate limits masquerading as logic failures) saved hours of misdiagnosed debugging. Lesson L11 (weaker models as fuzzers) found 2 bugs GPT-4o hid.

### Vanilla Frontend with Mock/Live Toggle

No React, no Next.js, no build step. Vanilla HTML/CSS/JS with a mock data mode for offline development. This meant any team member could open the frontend, edit it, and refresh — no toolchain knowledge required.

### Single SurrealDB Backend

One database for everything: products, customers, orders, reviews, categories, goals, ingredients, graph edges, conversation checkpoints, self-improvement patterns, and web search cache. No Postgres+Redis+Neo4j+Pinecone stack. SurrealDB's multi-model engine handled vector, BM25, graph, and relational queries in a single instance.

### Per-Turn Judge Node

The agent graph has a judge node that evaluates tool selection quality after every turn. A cheap LLM call scores the turn as success/partial/failure, identifies the query pattern, and persists the verdict to SurrealDB. Successes become `learned_pattern` records; failures become `failure_record` entries. This created a self-improving feedback loop.

---

## 5. What Could Be Improved

### SurrealDB 3.0 Compatibility (~8 hours lost)

Three separate compatibility issues burned significant time:

1. **`db.query()` returns flat lists** in the 3.0 SDK, not `[{"result": [...]}]`. Code silently returned empty results.
2. **KNN `<|N|>` operator broken** — returns an error string, not an exception. Vector search silently failed.
3. **BM25 `@1@` operator broken** — returns empty arrays. Keyword search returned nothing.

Each bug was hard to diagnose because SurrealDB returned valid-looking responses (empty arrays, error strings) rather than throwing exceptions. We had to add defensive checks for every query result format.

**Lesson**: When using a database at a new major version during a hackathon, budget time for compatibility issues. Test every operator against the running version before building on it.

### Tool Duplication Before Consolidation

We started with 13 tools — `find`, `hybrid_search`, `semantic_search`, `cat`, `get_record`, `grep`, `keyword_search`, etc. The overlap confused the LLM's tool selection (44% accuracy). We should have designed the consolidated 9-tool SurrealFS set from the start, not after discovering the problem under stress testing.

**Lesson**: Tool design is architecture. Do it in the design phase, not as a post-hoc fix.

### Rate Limits Masquerading as Logic Failures

Running 43 LLM calls back-to-back hit OpenAI's rate limits. Our error handling was generic (`"error processing your request"`), so rate limits looked identical to logic bugs. We wasted time debugging code that was actually correct.

**Lesson**: Always include the error type in error responses. Classify failures by root cause before investigating.

### No E2E Tests During Hackathon

We had 93 unit tests and 43 stress test queries, but no end-to-end tests that validated the full flow from frontend to database and back. The unit tests mocked the database; the stress tests called the API but not the frontend. A few frontend rendering bugs slipped through.

**Lesson**: Even a single E2E test (send a chat message, verify a product card renders) catches an entire class of integration bugs.

### Test Helper Too Broad

The `not_error()` test helper checked `"error" not in reply.lower()`, which matched the word "error" in legitimate responses like "a message sent in error". This created false-positive test failures that took time to diagnose.

**Lesson**: Error detection should match system error patterns (e.g., "I encountered an error", "RateLimitError"), not arbitrary occurrences of the word "error."

---

## 6. Reusable Patterns

### Pattern 1: SurrealFS Metaphor — Speak the LLM's Language

**The pattern**: Map any database or API to bash commands that LLMs already understand.

| Bash Command | Database Operation | When to Use |
|---|---|---|
| `ls` | List/browse records | Orientation, discovery |
| `cat` | Read full record | Detail retrieval, verification |
| `find` | Semantic + keyword search | Discovery by concept |
| `grep` | Keyword search in scope | Exact term matching |
| `tree` | Hierarchical view | Category/hierarchy browsing |

**Why it works**: LLMs have seen millions of bash sessions in their training data. They have strong, accurate priors on when to use each command. By naming tools after these commands, you get near-perfect tool selection for free — no prompt engineering required.

**How to apply**: For any new data source, ask "what would the bash equivalent be?" A REST API becomes `curl`. A file system stays `ls`/`cat`. A search index becomes `grep`/`find`. The metaphor should feel obvious.

### Pattern 2: GATHER→ACT→VERIFY — Three-Phase Constraint Loop

**The pattern**: Enforce three phases in every agent interaction via the system prompt.

1. **GATHER**: Orient in the data space (browse, list, read schema)
2. **ACT**: Execute informed queries (search, traverse, aggregate)
3. **VERIFY**: Ground-truth before responding (re-read recommended items, confirm graph edges)

**Why it works**: Without constraints, agents take shortcuts — they search once and answer, or skip verification entirely. The three-phase loop ensures every answer is grounded in actual data. The VERIFY phase alone eliminated most hallucinated recommendations.

**How to apply**: Define phases with clear tool mappings and worked examples in the system prompt. The constraint is soft (prompt-based, not code-enforced), but with good examples, compliance is high.

### Pattern 3: Bug→Lesson→Prevention — Structured Knowledge Extraction

**The pattern**: After every bug fix, extract three things:

1. **Problem**: What went wrong, with specific code or error output
2. **Solution**: What fixed it
3. **Prevention**: A rule that prevents recurrence

**Why it works**: Bugs cluster. The same class of mistake (wrong result format, overly broad assertion, missing error type) recurs unless you explicitly codify the lesson. Over 13 lessons, our bug recurrence rate dropped to near zero.

**How to apply**: Maintain a `lessons.md` file. After any correction — from a user, a failing test, or a debugging session — add an entry. Reference lessons at the start of each new session.

### Pattern 4: Weaker Models as Fuzzers

**The pattern**: Test your agent with multiple model tiers, including weaker/cheaper models.

**Why it works**: Stronger models (GPT-4o, GPT-5.4) are polite — they avoid code paths with bugs because they can infer intent and work around issues. Weaker models (GPT-4o-mini) are aggressive — they call tools in unexpected ways, pass edge-case arguments, and hit code paths the stronger model never touches.

In our case, GPT-4o-mini found two real bugs that GPT-4o masked: a `RecordID.replace()` crash and a broken `->*` graph syntax. Both were valid bugs in our code, invisible under the "polite" model.

**How to apply**: Run your stress tests with at least two model tiers. Treat the weaker model as a fuzzer, not a lesser version.

### Pattern 5: Context Engineering > Prompt Engineering

**The pattern**: Instead of writing longer prompts, change the environment so the prompt can be shorter.

Examples from this project:
- **Tool names** (`ls` not `list_records`) — eliminated the need for tool-selection prompts
- **Filesystem paths** (`/products/xyz`) — eliminated the need for explaining record IDs
- **Phase labels** (`[GATHER]`, `[ACT]`, `[VERIFY]` tags on tools) — eliminated routing logic in the prompt
- **Worked examples** — eliminated the need for abstract rules

**Why it works**: Prompts are fragile. They get long, contradictory, and hard to maintain. Environmental constraints (tool names, data formats, schema design) are structural — they shape behavior without relying on the model to read and follow instructions.

**How to apply**: For every prompt instruction, ask "can I encode this in the tool name, the data format, or the schema instead?" If yes, do that. Reserve the prompt for constraints that genuinely cannot be expressed structurally.

---

## 7. Final Metrics

### Scale

| Metric | Value |
|--------|-------|
| Duration | 48 hours |
| Team size | 5 |
| Total commits | 168 |
| Products | 431 unique (scraped lookfantastic.com) |
| Customers | 2,526 synthetic profiles |
| Orders | 6,862 with line items |
| Reviews | 3,247 with sentiment |
| Graph edge types | 12 |

### Architecture

| Component | Detail |
|-----------|--------|
| SurrealFS tools | 9 (ls, cat, tree, explore_schema, find, grep, graph_traverse, surrealql_query, web_search) |
| API endpoints | 21 |
| Unit tests | 93 |
| Stress test queries | 43 adversarial |
| System prompt | 203 lines (GATHER→ACT→VERIFY + 7 worked examples) |
| Database | Single SurrealDB instance (vector + BM25 + graph + relational) |

### Quality

| Metric | Before | After |
|--------|--------|-------|
| Tool selection accuracy | 44% | 100% |
| Stress test pass rate | 51.1% | 95.3% |
| Graph traversal utilization | 36% | 75%+ |
| Bug recurrence rate | (unmeasured) | ~0% (13 lessons codified) |

### Technology

| Layer | Stack |
|-------|-------|
| Agent | LangGraph `create_react_agent` + per-turn judge node |
| API | FastAPI (20+ endpoints, SSE streaming) |
| Database | SurrealDB 3.0 (HNSW vector, BM25, graph RELATE, relational) |
| Embeddings | OpenAI text-embedding-3-small (1536 dims, LRU cached) |
| Models | GPT-5.4 (default), Claude Sonnet 4, Gemini 3.1 via `get_llm()` |
| Frontend | Vanilla HTML/CSS/JS (no build step) |
| Observability | LangSmith traces, per-turn judge verdicts |
| Checkpointing | SurrealSaver (LangGraph state in SurrealDB) |

---

## Appendix: Lessons Index

For quick reference, all 13 lessons extracted during the hackathon:

| # | Lesson | Category |
|---|--------|----------|
| L1 | SurrealDB 3.0 breaks operators silently | Database |
| L2 | SurrealDB 3.0 result format changed | Database |
| L3 | Tool duplication hurts LLM tool selection | Agent Design |
| L4 | Filesystem metaphor = zero-shot tool selection | Agent Design |
| L5 | Constraint loops beat more tools | Agent Design |
| L6 | Rate limiting masquerades as logic failures | Testing |
| L7 | `not_error()` was too broad | Testing |
| L8 | Graph edge types need complete documentation | Agent Design |
| L9 | Memory distillation is cheap and high-value | Architecture |
| L10 | Stress tests need pacing, not just assertions | Testing |
| L11 | Test with weaker models to find hidden bugs | Testing |
| L12 | SurrealDB 3.0 returns RecordID objects, not strings | Database |
| L13 | SurrealSaver needs tables pre-created | Database |

Full details in [lessons.md](./lessons.md).
