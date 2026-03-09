# Harness Analysis: Taro.ai Agentic Search

## Executive Summary

Deep analysis of the Taro.ai harness against harness engineering principles from OpenAI (Codex), Martin Fowler, and agent architecture best practices. The current implementation has a solid foundation but needs significant improvements in constraint enforcement, verification loops, personalization, and graph utilization.

---

## 1. Code Review Findings

### 1.1 Critical: SurrealDB 3.0 SDK Incompatibility

**All tools use the wrong result format.** Every tool does:
```python
result = await db.query(surql, params)
docs = result[0].get("result", []) if result else []
```

MEMORY.md states SurrealDB 3.0 returns a **flat list**, not `[{"result": [...]}]`. This means tools might silently return empty results on some SurrealDB 3.0 versions. The code appears to work currently (possibly SurrealDB 3.0.2 re-wrapped results), but this is fragile.

**Action**: Add defensive handling that works with both formats:
```python
raw = await db.query(surql, params)
if isinstance(raw, list) and raw and isinstance(raw[0], dict) and "result" in raw[0]:
    docs = raw[0]["result"] or []  # Old format
else:
    docs = raw or []  # New flat format
```

### 1.2 Critical: KNN Operator `<|N|>` May Be Broken

Both `hybrid_search.py` and `semantic_search.py` use:
```sql
WHERE embedding <|{limit}|> $embedding
```

MEMORY.md notes: "KNN operator `<|N|>` is BROKEN: Returns error string." If this is still broken, vector search silently fails and only BM25 results are returned in hybrid search.

**Action**: Test KNN operator. If broken, replace with:
```sql
ORDER BY vector::similarity::cosine(embedding, $embedding) DESC LIMIT {limit}
```

### 1.3 Critical: BM25 `@1@` Operator May Be Broken

`keyword_search.py` and `hybrid_search.py` use:
```sql
WHERE content @1@ $query
```

MEMORY.md notes: "BM25 `@1@` operator: Also broken in SurrealDB 3.0."

**Action**: Verify BM25 functionality. If broken, the entire keyword search and half of hybrid search is non-functional.

### 1.4 Schema vs Code Mismatch

**schema.surql** defines only 3 edge types:
- `belongs_to` (product -> category)
- `child_of` (category -> category)
- `related_to` (product -> product)

But **MEMORY.md** claims 9 edge types including:
- `placed_by` / `placed` (customer -> order)
- `contains` (order -> product)
- `has_review` (order -> review)
- `also_bought` (product -> product)
- `supports_goal` (product -> goal)
- `contains_ingredient` (product -> ingredient)

The missing edges are created in `seed.py` but **not defined in schema.surql**. This means SurrealDB treats them as schemaless tables with no type constraints.

### 1.5 Graph Traverse Tool - Incomplete Edge Coverage

`graph_traverse.py` docstring only mentions 3 edges:
```
edge_type: Relationship type: 'belongs_to', 'child_of', 'related_to'.
```

The agent doesn't know about:
- `placed` / `placed_by` (customer purchase history)
- `contains` (order contents)
- `has_review` (reviews for orders)
- `also_bought` (co-purchase recommendations)
- `supports_goal` (product-goal mapping)
- `contains_ingredient` (product ingredients)

This means the agent **cannot be asked** about purchase history, order contents, ingredient lookups, or goal-based recommendations via graph traversal.

### 1.6 System Prompt Gaps

The default.md prompt has several issues:

1. **Missing edge types**: Only 3 edges mentioned, but data has 6+
2. **No user context awareness**: Agent has no way to know who the user is or their preferences
3. **No explicit harness phases**: The prompt doesn't enforce GATHER->ACT->VERIFY explicitly
4. **No failure recovery guidance**: No instruction on what to do when tools return errors
5. **No chain-of-thought structure**: The agent isn't instructed to think step-by-step
6. **No guardrails for off-topic**: No explicit instruction to stay in domain
7. **No tool output format expectations**: Agent doesn't know what format each tool returns

### 1.7 No Error Handling in Chat Endpoint

`main.py`'s `/chat` endpoint had no try/except - any agent error crashes the API with 500.

**Fixed**: Added error handling (in this worktree).

### 1.8 No Personalization Infrastructure

- No user ID passed to the agent
- No user context or preference lookup
- No memory distillation after conversations
- `customer` table has data but agent has no tool to query it
- No way to build user-specific recommendations

### 1.9 Self-Improvement Tables Unused

`learned_pattern` and `failure_record` tables exist but:
- No code writes to them
- No code reads from them
- No feedback loop exists

---

## 2. Architectural Analysis

### 2.1 Strengths

1. **Document-Product bridging**: Clever separation of searchable documents (with embeddings) from structured products (with graph edges), linked by `source_id`. This is elegant.

2. **RRF fusion**: Client-side Reciprocal Rank Fusion is well-implemented and correctly handles deduplication.

3. **Multi-provider LLM support**: Model-agnostic design allows switching providers easily.

4. **Prompt swapping**: File-based template system allows runtime prompt selection.

5. **Web search caching**: Tavily results cached in SurrealDB to avoid repeated API calls.

6. **Read-only SurrealQL**: Whitelist approach to block write operations is sound.

### 2.2 Weaknesses

1. **No structured verification loop**: The prompt says "verify" but there's no mechanism to enforce it. The agent can skip verification entirely.

2. **No tool output validation**: Tools return formatted strings, not structured data. The agent receives markdown text and must parse it to use `source_id`.

3. **No retry/fallback mechanism**: If a tool fails, the agent sees an error string but has no structured guidance for recovery.

4. **Single DB connection per tool call**: Each tool creates a new WebSocket connection. For multi-tool chains, this means N connections for N tools.

5. **No observability beyond LangSmith**: No internal metrics on tool usage patterns, success rates, or latency.

6. **MemorySaver is ephemeral**: Conversation history lost on server restart.

### 2.3 Missing Harness Engineering Patterns

Per OpenAI/Fowler:

1. **Context engineering**: No dynamic context loading based on query type
2. **Constraint enforcement**: No structural validation of agent outputs
3. **Entropy management**: No mechanism to detect and fix degraded performance
4. **Feedback loops**: No learning from successful/failed interactions
5. **Architectural boundary enforcement**: Tools can be called in any order without structure

---

## 3. Comparison to Harness Engineering Principles

### OpenAI Codex Harness Patterns

| Pattern | Taro Status | Gap |
|---------|-------------|-----|
| Agent loop orchestration | Partial - ReAct but no structured phases | Need explicit phase gates |
| Tool execution with verification | Partial - suggested in prompt | Need enforcement |
| Context management | Weak - no dynamic context | Need user context, query analysis |
| Safety enforcement | Partial - read-only SurrealQL | Need output validation |
| Session persistence | Weak - MemorySaver only | Need SurrealDB checkpointing |
| Feedback for improvement | Missing | Need learned_pattern integration |

### Martin Fowler Harness Patterns

| Pattern | Taro Status | Gap |
|---------|-------------|-----|
| Architectural constraints via linters | Missing | No structural validation |
| Entropy management (garbage collection) | Missing | No degradation detection |
| Context as code design | Weak | Prompts are static |
| Feedback loops and control systems | Missing | No self-improvement |
| Solution space reduction | Partial | Tool selection guide helps |
| Iterative signal processing | Missing | No diagnostic from failures |

---

## 4. Recommended Improvements (Priority Order)

### P0: Critical (Must Fix)

1. **Fix SurrealDB query result handling** - Defensive parsing for both formats
2. **Test and fix KNN/BM25 operators** - Core search may be silently broken
3. **Add all edge types to graph_traverse** - Agent can't use most graph relationships
4. **Add error handling to all endpoints** - Prevent 500 crashes
5. **Add user context to the agent** - Pass user profile, preferences, history

### P1: High Priority (Should Fix for Demo)

6. **Rewrite system prompt with explicit harness phases** - GATHER->ACT->VERIFY gates
7. **Add user memory distillation** - After each chat, update user context in SurrealDB
8. **Add all edge types to schema.surql** - Formal type definitions
9. **Return structured data from tools** - Not just formatted strings
10. **Add conversation context injection** - User profile loaded at conversation start

### P2: Medium Priority (Impressive for Demo)

11. **Implement self-improvement loop** - Log to learned_pattern and failure_record
12. **Add tool output validation** - Verify results before returning to agent
13. **Add query classification** - Route queries to optimal tool chains
14. **Connection pooling** - Reuse DB connections across tool calls
15. **Add metrics/observability** - Track tool usage, success rates, latency

### P3: Nice to Have

16. **Multi-agent architecture** - Separate planner/executor/verifier agents
17. **Streaming responses** - SSE for real-time chat experience
18. **A/B testing prompts** - Compare prompt effectiveness
19. **User feedback collection** - Thumbs up/down on responses

---

## 5. Stress Test Scenarios (In Progress)

Running automated stress tests across:
- Tool selection accuracy (8 queries)
- Multi-hop reasoning (4 queries)
- Edge cases (6 queries)
- Adversarial attacks (5 queries)
- Graph reasoning (5 queries)
- Schema awareness (3 queries)
- Conversation continuity (3-turn thread)
- Failure recovery (3 queries)
- Domain-specific queries (10 queries)

Results will be appended when available.
