# Lessons Learned

## Harness Engineering Session (2026-03-08)

### L1: SurrealDB 3.0 Breaks Operators Silently
**Problem**: KNN `<|N|>` returns an error *string* (not exception). BM25 `@1@` returns empty arrays. Both appear as "no results" unless you inspect the actual return value.
**Solution**: Use `ORDER BY vector::similarity::cosine(embedding, $vec) DESC LIMIT N` for vector search. Use `CONTAINS` as BM25 fallback.
**Prevention**: Always test SurrealDB operators against the actual running version. Add integration tests that verify search returns non-empty results for known data.

### L2: SurrealDB 3.0 Result Format Changed
**Problem**: `db.query()` returns flat lists in 3.0 SDK, not `[{"result": [...]}]`. Code checking `result[0].get("result", {})` silently fails.
**Solution**: Use `result or []` directly, with `isinstance` checks for both formats.
**Prevention**: Wrap all DB result handling in a normalize function. Test against both formats.

### L3: Tool Duplication Hurts LLM Tool Selection
**Problem**: Having 13 tools with overlapping functionality (find vs hybrid_search vs semantic_search, cat vs get_record, grep vs keyword_search) confused the LLM's tool selection.
**Solution**: Consolidated to 9 unique tools using familiar bash metaphors (ls, cat, find, grep, tree).
**Prevention**: Before adding a new tool, check if an existing tool already covers the use case. Prefer extending over duplicating.

### L4: Filesystem Metaphor = Zero-Shot Tool Selection
**Problem**: LLMs don't reliably pick tools with unfamiliar names (e.g., "hybrid_search", "get_record").
**Solution**: Name tools after bash commands (`ls`, `cat`, `find`, `grep`, `tree`). LLMs already have strong priors on when to use these.
**Prevention**: Always prefer familiar metaphors over descriptive but novel names. This is "context engineering" — leverage the LLM's existing training.

### L5: Constraint Loops > More Tools
**Problem**: Agent would answer from its own knowledge instead of using tools, or skip verification.
**Solution**: GATHER->ACT->VERIFY constraint loop in the system prompt with worked examples. "You MUST use tools. NEVER answer from your own knowledge."
**Prevention**: System prompts need explicit constraint phases, not just tool descriptions. Worked examples are critical.

### L6: Rate Limiting Masquerades as Logic Failures
**Problem**: Under stress testing, 15/17 failures were `RateLimitError` from OpenAI, not harness logic bugs. Generic error handling hid the root cause.
**Solution**: 1) Include error type in response (`RateLimitError` vs generic). 2) Add retry with 5s backoff. 3) Add 2s delay between stress test queries.
**Prevention**: Always include error type in error responses. Add retry logic for transient errors. Don't run 43 LLM calls back-to-back without pacing.

### L7: `not_error()` Was Too Broad
**Problem**: Test helper checking `"error" not in reply.lower()` flagged legitimate responses containing the word "error" (e.g., "message sent in error").
**Solution**: Check for specific error phrases: "i encountered an error", "error processing your request", "RateLimitError".
**Prevention**: Error detection should match system error patterns, not the word "error" generally.

### L8: Graph Edge Types Need Complete Documentation
**Problem**: `graph_traverse` only documented 3 of 9 edge types. Agent couldn't traverse `also_bought`, `supports_goal`, `contains_ingredient`, etc.
**Solution**: Added EDGE_TYPES dict with all 9 edges, validation, and helpful error messages.
**Prevention**: When adding graph edges to schema, immediately update the traversal tool's docstring and validation.

### L9: Memory Distillation is Cheap and High-Value
**Problem**: No user personalization between sessions.
**Solution**: 50 lines of code: LLM summarizes conversation, stores in user's `context` field, loads on next request.
**Prevention**: Personalization doesn't need complex systems. A simple distill->store->load loop is sufficient for demos.

### L10: Stress Tests Need Pacing, Not Just Assertions
**Problem**: Running 43 API calls as fast as possible overwhelms OpenAI's rate limits, giving misleading failure rates.
**Solution**: Add `QUERY_DELAY = 2.0` between queries. Separate infrastructure failures from logic failures.
**Prevention**: Stress tests should distinguish "can the system handle the query?" from "can the system handle 43 queries in 2 minutes?"

### L11: Test with Weaker Models to Find Hidden Bugs
**Problem**: gpt-4o happened to avoid code paths with bugs (graph_traverse `->*` syntax, RecordID `.replace()`). It "worked" but only by luck.
**Solution**: Test with gpt-4o-mini which calls tools more aggressively and hits more code paths. Found 2 real bugs gpt-4o masked.
**Prevention**: Always validate with at least 2 model tiers. Weaker models are better fuzzers because they're less "polite" about tool calling.

### L12: SurrealDB 3.0 Returns RecordID Objects, Not Strings
**Problem**: `doc.get("source_id", "")` returns a `RecordID` object in SurrealDB 3.0, not a string. Calling `.replace()` on it crashes.
**Solution**: Always wrap in `str()`: `str(doc.get("source_id", ""))`.
**Prevention**: In SurrealDB 3.0, any field that references another record will be a RecordID. Always coerce to string before string operations.

### L13: SurrealSaver Needs Tables Pre-Created
**Problem**: `langgraph-checkpoint-surrealdb` v2.0.0's `setup()` is a no-op — it doesn't create the `checkpoint` or `write` tables. When those tables don't exist, SurrealDB 3.0 returns an error *string* (e.g., `"The table 'checkpoint' does not exist"`) instead of an empty list. SurrealSaver treats `result[0]` as a dict, but gets a character, causing `TypeError: string indices must be integers`.
**Solution**: Manually create `DEFINE TABLE checkpoint SCHEMALESS` and `DEFINE TABLE write SCHEMALESS` in the schema before first use. With empty tables, `db.query()` returns `[]` as expected.
**Prevention**: When integrating third-party LangGraph checkpointers, always check if they auto-create tables. For SurrealDB 3.0, verify that missing tables return error strings (not exceptions), which breaks libraries expecting list returns.

## Patterns to Reuse

### The SurrealFS Pattern
Map any database/API to bash commands. Works for any data source:
- `ls` = list/browse
- `cat` = read full record
- `find` = semantic search
- `grep` = keyword search
- `tree` = hierarchical view

### The GATHER->ACT->VERIFY Loop
Enforce 3 phases in every agent interaction:
1. GATHER: Orient (ls, tree, explore_schema)
2. ACT: Execute informed queries (find, grep, graph_traverse)
3. VERIFY: Ground-truth before responding (cat on recommended items)

### The Distill->Store->Load Loop
After each conversation:
1. DISTILL: LLM summarizes key preferences/context
2. STORE: Persist in user record (context field)
3. LOAD: Inject on next request as system context
