# Harness Engineering 2.0 — Comprehensive Audit

**Date**: 2026-03-08
**Scope**: 35 adversarial queries across 4 test suites + codebase analysis + external research
**Models**: GPT-4o (default) + Claude Sonnet 4 (multihop suite, due to rate limits)
**User context**: charlotte_gong (returning user with purchase history pre-injected)

---

## Executive Summary

**graph_traverse is severely underutilized.** Across 35 queries, the agent used `graph_traverse` in only 36% of cases where it was the ideal tool. The agent defaults to `find` (semantic search), `cat` (read profile), and `grep` (keyword search) — tools that work but produce shallower, less graph-aware answers.

When graph_traverse IS triggered, the agent uses it well (correct edge types, correct directions, multi-hop chains of 6-11 calls). The problem isn't capability — it's **routing**. The system prompt, tool descriptions, and data architecture all conspire to make flat search the path of least resistance.

---

## Test Results Summary

### Suite 1: Original Adversarial (10 queries)
| Metric | Value |
|--------|-------|
| CORRECT | 8 (80%) |
| SUBOPTIMAL | 2 (20%) |
| WRONG | 0 |
| Graph used when needed | 4/6 (67%) |

### Suite 2: Edge-Type Coverage (9 queries — 1 per edge type)
| Metric | Value |
|--------|-------|
| CORRECT | 1 (11%) |
| SUBOPTIMAL | 7 (78%) |
| WRONG | 1 (11%) |
| Graph used when needed | **1/9 (11%)** |

### Suite 3: Adversarial Edge Cases (8 queries)
| Metric | Value |
|--------|-------|
| CORRECT | 2 (25%) |
| SUBOPTIMAL | 5 (62.5%) |
| WRONG | 1 (12.5%) |
| Graph used when needed | 4/8 (50%) |

### Suite 4: Multi-Hop Chains (8 queries — Claude Sonnet 4)
| Metric | Value |
|--------|-------|
| CORRECT | 4 (50%) |
| SUBOPTIMAL | 3 (37.5%) |
| WRONG | 1 (12.5%) |
| Graph used when needed | 4/8 (50%) |

### Aggregate (35 queries)
| Metric | Value |
|--------|-------|
| CORRECT | 15/35 (43%) |
| SUBOPTIMAL | 17/35 (49%) |
| WRONG | 3/35 (8%) |
| **Graph used when needed** | **13/31 (42%)** |
| Queries with 0 graph calls | 18/35 (51%) |
| Total graph_traverse calls | ~54 |
| Total tool calls | ~189 |

---

## Edge-Type Coverage Matrix

| Edge Type | Queries Tested | graph_traverse Used? | Notes |
|-----------|---------------|---------------------|-------|
| **placed** | 4 | 2/4 (50%) | Often bypassed via `cat /users/{id}` which embeds orders |
| **contains** | 3 | 1/3 (33%) | Bypassed via `cat /users/{id}/orders/` |
| **has_review** | 2 | 1/2 (50%) | Bypassed via user profile pre-injection |
| **belongs_to** | 2 | 0/2 (0%) | Always uses `cat` which shows category inline |
| **child_of** | 1 | 0/1 (0%) | `tree /categories/` handles this |
| **also_bought** | 4 | 3/4 (75%) | **Best performing** — only edge NOT in cat/ls output |
| **supports_goal** | 2 | 0/2 (0%) | Uses `tree /goals/` or `ls /goals/` instead |
| **contains_ingredient** | 7 | 2/7 (29%) | **Worst performing** — agent systematically falls back to text search |
| **related_to** | 4 | 3/4 (75%) | Works well when explicitly prompted |

**Key finding**: `also_bought` is the ONLY edge type used reliably (75%) because it's the ONLY edge NOT surfaced by ls/cat/tree. All other edges have filesystem shortcuts.

---

## 7 Root Causes (Ranked by Impact)

### 1. HIGHEST: System prompt decision flow positions `find` as universal default
The prompt says:
```
1. Product search -> find
2. Exact name/term -> grep
3. Relationships -> graph_traverse (with a record ID from search results)
```
`graph_traverse` is #3 and requires a prior search. The agent reads this as "try find first, then maybe traverse."

### 2. HIGH: "Use the fewest tools possible" actively discourages exploration
The GATHER phase says: "Use the fewest tools possible. One good search is better than three mediocre ones." This directly kills multi-hop graph traversal, which requires 3-5 tool calls by nature.

### 3. HIGH: 4/5 prompt examples use find-first patterns
Only 1 of 5 examples shows `graph_traverse`. The agent learns from examples — 80% of its training signal says "use find."

### 4. MEDIUM-HIGH: `cat`/`ls`/`tree` already surface single-hop graph data
`cat /users/{id}` returns orders, products, reviews inline. `ls /categories/{id}` shows products. `tree /goals/` shows products. The filesystem tools make `graph_traverse` feel redundant for 1-hop queries.

### 5. MEDIUM-HIGH: `graph_traverse` docstring lacks routing signals
Missing: `[ACT]` phase tag, "Best for:" section, trigger words ("also bought", "related", "ingredients in"), "Use INSTEAD of find when:" guidance. Compare to `find` which says "primary search tool."

### 6. MEDIUM: Pre-injected user context eliminates need for graph exploration
The API injects purchase history + reviews into the system prompt at request time. The agent "knows" Charlotte's purchases without needing to traverse the graph, leading to ungrounded answers.

### 7. MEDIUM: No fallback chains when graph data is empty
When `graph_traverse` returns empty (missing data), the agent gives up instead of trying `grep` → `find` → `surrealql_query` as fallbacks.

---

## Bright Spots (What Works)

1. **Query 4 edge-cases ("bad reviews")**: 11 graph traversals across 3 edge types with correct directions. Proves the agent CAN do deep multi-hop when the query clearly maps to graph operations.

2. **Query 8 original ("similar ingredients to purchases")**: 6 graph_traverse calls chaining customer→orders→products→ingredients→find. Multi-hop works when triggered.

3. **`also_bought` edge**: 75% usage rate — the agent correctly identifies "what do people also buy" as requiring graph traversal since this data isn't available elsewhere.

4. **Correct edge type selection**: When graph_traverse IS used, the agent picks the right edge type 100% of the time. Schema understanding is solid.

5. **Filesystem metaphor validated**: ls/cat/tree/find/grep selection is near-perfect. The agent navigates the SurrealFS naturally.

---

## Recommended Fixes (Priority Order)

### P0: System Prompt Rewrite
1. **Remove** "Use the fewest tools possible" → Replace with "Use the RIGHT tools. A 3-tool graph chain produces richer answers than a single search."
2. **Rewrite decision flow** — add explicit trigger routing:
   - "also bought / similar / related / complementary" → `graph_traverse` with `also_bought` or `related_to`
   - "ingredients in / what's in / contains" → `graph_traverse` with `contains_ingredient`
   - "category of / what category / subcategories" → `graph_traverse` with `belongs_to` or `child_of`
   - "who bought / purchase history / orders" → `graph_traverse` with `placed` + `contains`
   - "reviews / feedback / ratings" → `graph_traverse` with `has_review`
3. **Add 3-4 multi-hop worked examples** showing 3+ tool chains with `graph_traverse`
4. **Add graph-aware VERIFY**: "Before answering, verify at least one graph relationship is relevant."

### P1: Tool Description Engineering
5. **Rewrite `graph_traverse` docstring** — add `[ACT]` tag, "Best for:" section, trigger words, "Use INSTEAD of find when:"
6. **Add "when NOT to use" to `find`** — "Do NOT use find when the query is about relationships, co-purchases, ingredients, or categories — use graph_traverse."

### P2: Tool Output Breadcrumbs
7. **Add edge counts to `cat` output** — "Connected: also_bought(4), contains_ingredient(8), supports_goal(2)" → creates curiosity
8. **Add "next step" hints to `graph_traverse` output** — "Tip: Try `graph_traverse('{id}', 'contains_ingredient')` to see ingredients"
9. **Surface `also_bought` in `cat /products/{id}` output** — currently hidden

### P3: Architecture
10. **Reduce user context pre-injection** — make the agent EARN its knowledge via graph traversal rather than having it handed on a plate
11. **Add fallback chains** — graph_traverse(empty) → grep → find → surrealql_query
12. **Consider compound `explore` tool** — 1-hop on ALL edge types from a record simultaneously

---

## Files Modified (for implementation)
- `taro-api/src/prompts/templates/default.md` — P0 changes (decision flow, examples, VERIFY)
- `taro-api/src/tools/graph_traverse.py` — P1 (docstring rewrite)
- `taro-api/src/tools/fs_tools.py` — P1 (find "when NOT to use") + P2 (edge counts in cat)
- `taro-api/src/main.py` — P3 (reduce context pre-injection)

---

## Source Files
- `tasks/adversarial-graph-test-results.md` — Suite 1: Original adversarial (10 queries, GPT-4o)
- `tasks/adversarial-edge-coverage-results.md` — Suite 2: Edge-type coverage (9 queries, GPT-4o)
- `tasks/adversarial-edge-cases-results.md` — Suite 3: Adversarial edge cases (8 queries, GPT-4o)
- `tasks/adversarial-multihop-results.md` — Suite 4: Multi-hop chains (8 queries, Claude Sonnet 4)
- `tasks/research-agentic-patterns.md` — External research with 17 sources
