# Observability & Self-Improvement Pipeline Research

## 1. Current LangSmith Setup Status

### Configuration
The project uses LangSmith for tracing via environment variables defined in `taro-api/config/.env`:

```
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=lsv2_pt_xxxx...
LANGSMITH_PROJECT=taro
```

### How It Activates
In `taro-api/src/main.py` (lines 19-23), the LANGSMITH vars are mapped to LANGCHAIN equivalents before any LangChain imports:

```python
if os.getenv("LANGSMITH_TRACING", "").lower() == "true":
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_API_KEY", os.getenv("LANGSMITH_API_KEY", ""))
    os.environ.setdefault("LANGCHAIN_PROJECT", os.getenv("LANGSMITH_PROJECT", "taro-ai-hackathon"))
```

LangChain auto-instruments all agent runs, tool calls, and LLM invocations. Every `/chat` request produces a full trace in LangSmith.

### Python Client
`langsmith==0.7.14` is installed (part of `langchain-core` dependency chain). The `langsmith.Client` class is available for programmatic trace analysis.

---

## 2. LangSmith API Features for Batch Analysis

### Core Method: `Client.list_runs()`

```python
from langsmith import Client
client = Client()

runs = client.list_runs(
    project_name="taro",       # filter by project
    run_type="chain",          # "llm", "tool", "chain", "retriever"
    start_time=datetime.now() - timedelta(days=1),  # date range
    error=False,               # True = only errors, False = only successes
    is_root=True,              # top-level traces only (not sub-runs)
    filter='gt(total_tokens, 5000)',  # advanced filter syntax
    select=["inputs", "outputs", "error", "feedback_stats"],  # field selection
    limit=100,                 # max results
)
```

### Available Filters

| Filter | Syntax | Purpose |
|--------|--------|---------|
| Date range | `start_time=datetime(...)` | Runs after a given time |
| Error status | `error=True/False` | Success vs failure |
| Run type | `run_type="llm"/"tool"/"chain"` | Filter by component type |
| Token usage | `filter='gt(total_tokens, 5000)'` | High-cost runs |
| Latency | `filter='gt(latency, "5s")'` | Slow runs |
| Feedback | `filter='eq(feedback_key, "score")'` | By human feedback |
| Text search | `filter='search("moisturizer")'` | Full-text over inputs/outputs |
| Tags | `filter='has(tags, "stress-test")'` | By run tags |
| Root only | `is_root=True` | Top-level traces (one per user request) |

### Available Fields on Run Objects

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique run identifier |
| `name` | str | Run name (e.g., "AgentExecutor") |
| `run_type` | str | "llm", "tool", "chain", "retriever" |
| `inputs` | dict | Input parameters |
| `outputs` | dict | Output results |
| `error` | str/None | Error message if failed |
| `total_tokens` | int | Total token count |
| `prompt_tokens` | int | Input tokens |
| `completion_tokens` | int | Output tokens |
| `latency` | float | Execution time in seconds |
| `start_time` | datetime | When the run started |
| `end_time` | datetime | When the run ended |
| `trace_id` | UUID | Parent trace ID |
| `feedback_stats` | dict | Aggregated feedback |
| `tags` | list | Custom tags |
| `extra` | dict | Additional metadata |

### Batch Export Pattern

For large-scale analysis, use pagination and concurrent fetching:

```python
from concurrent.futures import ThreadPoolExecutor

# Get all root runs (one per chat request)
root_runs = client.list_runs(
    project_name="taro",
    is_root=True,
    start_time=since,
    select=["trace_id", "inputs", "outputs", "error", "total_tokens"],
)

# For each trace, fetch child runs (tool calls, LLM calls)
for root in root_runs:
    children = client.list_runs(trace_id=root.trace_id)
```

---

## 3. Data Flow Design

```
LangSmith Traces (cloud)
    |
    | Client.list_runs() -- batch pull every N hours
    v
[analyse_traces.py]
    |
    |-- Classify: success / failure / partial
    |-- Extract: tool sequences, token costs, latency
    |-- Identify: failure patterns, tool selection errors
    |
    v
SurrealDB Tables
    |
    +-- failure_record: individual failures with query + tool + error
    +-- learned_pattern: aggregated winning strategies
    |
    v
System Prompt Enhancement
    |
    +-- Load top N learned_patterns at agent init
    +-- "For queries like X, prefer tool Y"
    +-- Dynamic few-shot examples from successful traces
```

### Pipeline Steps

1. **Pull**: `analyse_traces.py` runs on schedule (cron or manual), pulls recent root runs from LangSmith
2. **Classify**: Each run is categorized as success/failure/partial based on error field and output quality heuristics
3. **Extract patterns**: Successful runs yield tool sequences and query patterns; failures yield anti-patterns
4. **Store to SurrealDB**: Write `failure_record` rows for failures, upsert `learned_pattern` rows for successful patterns
5. **Enhance prompts**: At agent build time, query `learned_pattern` table for top strategies and inject into system prompt

---

## 4. Failure vs Success Classification

### What Constitutes "Failure"

| Failure Type | Detection Method | Severity |
|-------------|-----------------|----------|
| **Tool selection error** | Agent picks wrong tool for query type (e.g., `web_search` when `find` would suffice) | P1 - harness issue |
| **Hallucination** | Agent responds without grounding in tool results; no tool calls in trace | P1 - trust issue |
| **No results returned** | Tools return empty, agent says "I couldn't find anything" for valid queries | P2 - coverage gap |
| **Error in tool execution** | Tool raises exception (SurrealDB connection, embedding API failure) | P2 - infra issue |
| **Incomplete answer** | Agent answers but misses key aspects of the question | P2 - quality issue |
| **Excessive token usage** | Run uses >10k tokens for a simple query | P3 - efficiency issue |
| **High latency** | Run takes >30s for a straightforward lookup | P3 - performance issue |

### What Constitutes "Success"

| Success Indicator | Detection Method |
|-------------------|-----------------|
| **Correct tool selection** | Tool calls match expected pattern for query type |
| **Grounded response** | Agent cited data from tool results in final answer |
| **Efficient execution** | Reasonable token count (<5k for simple, <15k for complex) |
| **Complete answer** | Response addresses all aspects of the query |
| **No error** | `run.error is None` |

### What is NOT a Failure

| Event | Classification | Reason |
|-------|---------------|--------|
| **Rate limit error** | Infra/transient | Not a harness or logic issue; retry handles it |
| **Unknown product query** | Correct behavior | Agent correctly reports product not found |
| **Adversarial prompt rejection** | Success | Agent correctly refuses prompt injection |

---

## 5. Batch Analysis Schedule

### Recommended Cadence

| Environment | Frequency | Rationale |
|-------------|-----------|-----------|
| **Development** | On-demand / after stress tests | Analyze specific test runs |
| **Hackathon demo** | Every 2 hours or manual | Quick feedback loop |
| **Production** | Every 6 hours (cron) | Balance freshness vs API cost |

### Trigger Events

- After every `make stress` run (43 queries generate rich trace data)
- After any user-reported issue
- Daily summary report generation
- Before system prompt updates (to establish baseline)

### API Rate Considerations

LangSmith's `list_runs` paginates automatically. For our scale (tens to hundreds of runs/day during hackathon), a single batch pull is well within limits. No pacing needed for analysis reads (unlike OpenAI LLM calls).

---

## 6. Proposed Schema Usage

### `failure_record` Table

Stores individual failure events pulled from LangSmith traces.

```sql
-- Existing schema (schema.surql lines 188-193):
DEFINE TABLE failure_record SCHEMAFULL;
DEFINE FIELD query ON failure_record TYPE string;       -- user's original query
DEFINE FIELD tool_used ON failure_record TYPE string;    -- tool that was called
DEFINE FIELD error ON failure_record TYPE string;        -- error message or failure description
DEFINE FIELD created_at ON failure_record TYPE datetime DEFAULT time::now();
```

**Usage pattern**:
```python
# After classifying a run as failed
await db.query("""
    CREATE failure_record SET
        query = $query,
        tool_used = $tool,
        error = $error
""", {"query": run.inputs["messages"][-1], "tool": failed_tool.name, "error": str(run.error)})
```

**Proposed additions** (future schema migration):
- `trace_id` (string) -- link back to LangSmith for deep inspection
- `failure_type` (string) -- "tool_selection", "hallucination", "no_results", "infra"
- `resolved` (bool) -- mark when a pattern fix addresses this failure

### `learned_pattern` Table

Stores aggregated successful strategies, derived from analyzing winning traces.

```sql
-- Existing schema (schema.surql lines 180-186):
DEFINE TABLE learned_pattern SCHEMAFULL;
DEFINE FIELD pattern_type ON learned_pattern TYPE string;     -- "tool_sequence", "query_routing", "fallback"
DEFINE FIELD query_pattern ON learned_pattern TYPE string;    -- regex or keyword pattern matching query types
DEFINE FIELD best_tool ON learned_pattern TYPE string;        -- recommended first tool
DEFINE FIELD success_count ON learned_pattern TYPE int DEFAULT 0;
DEFINE FIELD created_at ON learned_pattern TYPE datetime DEFAULT time::now();
```

**Usage pattern**:
```python
# After identifying a successful pattern
await db.query("""
    UPDATE learned_pattern SET success_count += 1
    WHERE pattern_type = $ptype AND query_pattern = $qp
""", {"ptype": "tool_sequence", "qp": "price comparison"})

# Or create new pattern
await db.query("""
    CREATE learned_pattern SET
        pattern_type = 'tool_sequence',
        query_pattern = 'ingredient lookup',
        best_tool = 'grep -> graph_traverse',
        success_count = 1
""")
```

**Proposed additions** (future schema migration):
- `tool_sequence` (array<string>) -- full ordered list of tools used
- `avg_tokens` (int) -- average token cost for this pattern
- `avg_latency` (float) -- average execution time
- `last_seen` (datetime) -- most recent occurrence
- `example_query` (string) -- representative query for few-shot injection

### Prompt Enhancement Loop

At agent initialization, load top patterns:

```python
patterns = await db.query("""
    SELECT * FROM learned_pattern
    ORDER BY success_count DESC LIMIT 10
""")

# Inject into system prompt as dynamic few-shot examples
prompt_suffix = "\n## Learned Patterns (from past successes)\n"
for p in patterns:
    prompt_suffix += f"- For '{p['query_pattern']}' queries, start with {p['best_tool']}\n"
```

---

## References

- [LangSmith Client.list_runs() API reference](https://langsmith-sdk.readthedocs.io/en/latest/client/langsmith.client.Client.list_runs.html)
- [Query traces (SDK) - LangChain docs](https://docs.langchain.com/langsmith/export-traces)
- [LangSmith Observability Platform](https://www.langchain.com/langsmith/observability)
- [LangSmith REST API tracing guide](https://docs.smith.langchain.com/observability/how_to_guides/tracing/trace_with_api)
- [LangSmith Python SDK on PyPI](https://pypi.org/project/langsmith/)
