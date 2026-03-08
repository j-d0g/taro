# Stress Test Results: Round 1

## Summary: 23/45 passed (51.1%)

**Average latency**: 11,213ms per query | **Total runtime**: 505s

## Results by Category

### Tool Selection: 8/18 (44%) - CRITICAL
- PASS: "recommend a protein powder" -> hybrid_search, get_record x2
- PASS: "something for muscle recovery" -> semantic_search, get_record x5
- FAIL: "Impact Whey Protein" -> HTTP 500 (no tools)
- FAIL: "what tables exist?" -> HTTP 500 (no tools)
- FAIL: "how many Beauty products?" -> HTTP 500 (no tools)
- FAIL: "show me product:impact_whey" -> HTTP 500 (no tools)
- PASS: "latest myprotein deals" -> web_search
- FAIL: "what category is Impact Whey in?" -> HTTP 500 (no tools)

**Domain queries (10 tests)**:
- FAIL x5: Skincare, anti-aging, hydration, marathon, budget queries -> HTTP 500
- PASS x5: Recovery, sleep, vegan, ingredient, comparison -> Used `find`, `cat`, `grep`

**Pattern**: Agent uses fs_tools (`find`/`cat`/`grep`) when it works, but 500-crashes on many queries.

### Multi-hop Reasoning: 0/4 (0%) - CRITICAL
ALL queries returned HTTP 500. The agent cannot chain tools for complex queries.

### Edge Cases: 5/6 (83%) - GOOD
- PASS: Empty query, gibberish, SQL injection, long query, emoji
- FAIL: Non-existent product -> HTTP 500

### Adversarial: 5/5 (100%) - EXCELLENT
- PASS: Prompt extraction blocked
- PASS: Write operations blocked
- PASS: Jailbreak/off-domain rejected
- PASS: Off-topic handled gracefully
- PASS: Code generation refused

### Graph Reasoning: 1/5 (20%) - CRITICAL
- PASS: "subcategories under Fitness" -> used `tree` (fs_tool)
- FAIL: "also_bought" -> HTTP 500
- FAIL: "ingredients" -> HTTP 500
- FAIL: "goals" -> HTTP 500
- FAIL: "order history" -> HTTP 500

### Schema Awareness: 0/3 (0%) - CRITICAL
Agent never uses `explore_schema`. Either answers from LLM memory or crashes.

### Conversation Continuity: 1/1 (100%) - GOOD
Multi-turn thread works with `find`, `cat` tools.

### Failure Recovery: 3/3 (100%) - GOOD
Graceful handling of non-existent products, categories, records.

## Root Cause Analysis

### 1. HTTP 500 Crashes (22/45 queries)
The agent crashes on many queries. Likely causes:
- Tool errors not caught (no try/except on /chat endpoint)
- SurrealDB query failures (KNN `<|N|>` operator, BM25 `@1@` operator issues)
- Result format mismatches between SurrealDB 3.0 and code expectations

### 2. Wrong Tool Selection
When the agent DOES work, it prefers fs_tools (`find`, `cat`, `tree`, `grep`) over search tools (`hybrid_search`, `semantic_search`). This happens because:
- fs_tools are listed first in ALL_TOOLS (GATHER phase)
- Their descriptions match more naturally to LLM expectations
- The prompt doesn't strongly differentiate them

### 3. No Graph Traversal
The agent NEVER uses `graph_traverse`. It uses `tree` (fs_tool) for hierarchy but can't follow edges like `also_bought`, `supports_goal`, `contains_ingredient`.

### 4. Duplicate Tools Confuse Agent
13 tools with overlapping functionality:
- `find` ≈ `hybrid_search` (both do RRF fusion)
- `cat` ≈ `get_record` (both fetch record details)
- `grep` ≈ `keyword_search` (both do BM25)

## Key Insights for Improvement

1. **Consolidate tools**: Merge fs_tools and search tools. Keep the filesystem metaphor but eliminate duplicates.
2. **Fix error handling**: Add try/except to /chat endpoint. Handle SurrealDB query format changes.
3. **Rewrite prompt**: Stronger tool selection guidance. Explicit harness phases. All edge types documented.
4. **Add user context**: No personalization currently possible.
5. **Fix search operators**: Test and fix KNN `<|N|>` and BM25 `@1@` for SurrealDB 3.0.
