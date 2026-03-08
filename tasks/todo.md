# Harness Improvement Plan

Based on stress test (51.1% pass rate) and code review.

## P0: Critical Fixes (Must complete)

- [ ] **1. Restore and consolidate fs_tools + search tools into unified 8-tool set**
  - Keep: `ls`, `cat`, `find`, `grep`, `tree` (SurrealFS metaphor)
  - Keep: `graph_traverse`, `explore_schema`, `web_search`
  - Remove duplicates: `hybrid_search` (= `find`), `keyword_search` (= `grep`), `semantic_search` (subset of `find`), `get_record` (= `cat`)
  - Result: 8 tools, no overlap, filesystem metaphor preserved
  - Update ALL_TOOLS in `__init__.py`

- [ ] **2. Fix the system prompt for unified toolset**
  - Explicit GATHER -> ACT -> VERIFY phases
  - Document ALL edge types (9 types)
  - Strong enforcement: "ALWAYS use tools, never answer from memory"
  - Tool decision matrix with clear routing
  - Failure recovery instructions
  - Few-shot examples for multi-hop chains

- [ ] **3. Fix error handling in chat endpoint**
  - Add try/except around agent invocation
  - Return graceful error responses, not HTTP 500
  - Already done in worktree, needs testing

- [ ] **4. Fix graph_traverse to support all edge types**
  - Add: `placed_by`, `contains`, `has_review`, `also_bought`, `supports_goal`, `contains_ingredient`
  - Update docstring with all available edges
  - Or: remove `graph_traverse` entirely since `cat` and `tree` already do graph navigation

- [ ] **5. Fix SurrealDB result format handling**
  - Defensive parsing: handle both `result[0]["result"]` and flat list formats
  - Add helper function for consistent result extraction

## P1: High Priority

- [ ] **6. Add user context injection**
  - Accept optional `user_id` in ChatRequest
  - Look up user profile from SurrealDB at conversation start
  - Inject user preferences/goals into system prompt
  - Enable personalized recommendations

- [ ] **7. Add memory distillation**
  - After each conversation, summarize key preferences/decisions
  - Store in user's `context` field in SurrealDB
  - Load on next conversation for continuity

- [ ] **8. Update schema.surql with all edge types**
  - Add TYPE RELATION definitions for all 9 edges

## P2: Demo Polish

- [ ] **9. Add self-improvement logging**
  - Log successful tool chains to `learned_pattern`
  - Log errors to `failure_record`
  - Use for analytics and prompt tuning

- [ ] **10. Re-run stress tests**
  - Verify pass rate improvement
  - Target: 85%+ pass rate

## Verification Criteria

- All 59 existing tests still pass (`make verify`)
- Stress test pass rate >= 85%
- No HTTP 500 errors on any stress test query
- Agent uses tools for every product/data question (no LLM-memory answers)
- Graph traversal works for at least also_bought, supports_goal, contains_ingredient
- Multi-hop chains work (search -> verify -> respond)
