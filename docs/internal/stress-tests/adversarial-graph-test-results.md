# Adversarial Graph Tool Usage Analysis

**Date**: 2026-03-08
**User ID**: charlotte_gong
**API**: localhost:8002/chat (GPT-4o default model)
**Pacing**: 5s delay between queries

## Summary

| Metric | Value |
|--------|-------|
| Total queries | 10 |
| CORRECT | 8 (80%) |
| SUBOPTIMAL | 2 (20%) |
| WRONG | 0 (0%) |
| ERROR | 0 (0%) |
| Graph needed | 6 queries |
| Graph used when needed | 4/6 (67%) |

## Detailed Results

### Category 1: Explicit Graph Queries

| # | Query | Expected | Actual Tools | Graph? | Verdict |
|---|-------|----------|-------------|--------|---------|
| 1 | What do customers who bought LANEIGE Water Bank also buy? | graph_traverse, find | grep, **graph_traverse** x3, cat x2, surrealql_query x2 | YES | CORRECT |
| 2 | Show me products related to Clinique Moisture Surge | graph_traverse, find | grep, find, cat, **graph_traverse** x2, grep, cat x2 | YES | CORRECT |
| 3 | What ingredients are in The Ordinary Niacinamide? | graph_traverse, cat | grep, find, cat | **NO** | SUBOPTIMAL |

**Findings**: 2/3 queries correctly used graph_traverse. Query 3 fell back to grep+find+cat to extract ingredients from the product description text instead of traversing `contains_ingredient` edges. The agent found the answer (niacinamide + zinc) but missed the graph structure.

### Category 2: Exploration Queries

| # | Query | Expected | Actual Tools | Verdict |
|---|-------|----------|-------------|---------|
| 4 | What categories do you have? | ls, tree | **ls** | CORRECT |
| 5 | Show me everything in the anti-aging category | ls, cat, graph_traverse | grep, **ls**, **tree**, grep x2, ls, find, cat x3 | CORRECT |
| 6 | What goals can products help with? | ls, tree | **ls** | CORRECT |

**Findings**: Perfect. All exploration queries correctly used ls/tree. Query 5 was thorough -- it searched for "anti-aging" across multiple paths (categories, goals) and explored alternatives when the exact category didn't exist. Notably, query 5 used 10 tool calls, suggesting the agent compensated for the ambiguous query well.

### Category 3: Multi-hop Queries

| # | Query | Expected | Actual Tools | Graph? | Verdict |
|---|-------|----------|-------------|--------|---------|
| 7 | What's the most popular product in the same category as CeraVe cleanser? | find, graph_traverse, cat | grep, cat, **surrealql_query** x2, cat | **NO** | SUBOPTIMAL |
| 8 | Find me products with similar ingredients to what I've bought | graph_traverse, cat | cat, **graph_traverse** x6, find x4, cat x4 | YES | CORRECT |

**Findings**: Query 7 bypassed graph_traverse by using raw SurrealQL to directly query for category membership and products. This is functionally correct (got the right answer) but reveals the agent prefers surrealql_query over graph_traverse for multi-hop category lookups. Query 8 was excellent -- 6 graph_traverse calls chaining through purchase history to ingredients to similar products.

### Category 4: User Context Queries

| # | Query | Expected | Actual Tools | Graph? | Verdict |
|---|-------|----------|-------------|--------|---------|
| 9 | What have I bought before? | cat, graph_traverse | **cat** | N/A | CORRECT |
| 10 | Based on my purchase history, what should I try next? | graph_traverse, cat, find | cat, **graph_traverse** x3, find, cat x2 | YES | CORRECT |

**Findings**: Query 9 is interesting -- the agent used ONLY `cat` because the user's purchase history was already injected in the system prompt context (the API injects user profile at request time). So `cat /users/charlotte_gong` returned the full profile with purchases already visible. This is actually efficient -- no need for graph_traverse when the data is pre-fetched. Query 10 was excellent -- graph traversal into also_bought and supports_goal edges.

## Root Cause Analysis: Why Graph Traverse Was Skipped

### Query 3 (Ingredients): SUBOPTIMAL
- **What happened**: Agent used grep to search for "niacinamide", found the product via find, then read it with cat. The product description already contains "niacinamide" and "zinc" in the text.
- **Why graph was skipped**: The `contains_ingredient` edge exists in the schema, but the agent found the answer faster through text search. The product's description field already has ingredient info embedded.
- **Impact**: Low. Got the right answer. But misses structured ingredient data (dosage, INCI names) that would be in the ingredient nodes.

### Query 7 (Most popular in same category): SUBOPTIMAL
- **What happened**: Agent used grep to find CeraVe, cat to read it, then surrealql_query to find products in the same subcategory sorted by avg_rating.
- **Why graph was skipped**: The agent chose raw SurrealQL (`SELECT * FROM product WHERE subcategory = 'Cleansers' ORDER BY avg_rating DESC LIMIT 5`) instead of graph_traverse through `belongs_to` edges. This is arguably more efficient for this particular query.
- **Impact**: Low. The SurrealQL approach is actually more direct for "find products in same category sorted by popularity." Graph traverse would require: find product -> traverse belongs_to -> get category -> traverse back to all products -> sort. The agent found a shortcut.

## Key Observations

1. **Graph traverse usage is decent (67%) but not reflexive.** The agent uses it for relationship-heavy queries (also_bought, ingredients similarity, user history) but skips it for queries that can be answered with simpler tools.

2. **surrealql_query is a graph_traverse escape hatch.** Query 7 shows the agent using raw SurrealQL instead of the structured graph_traverse tool. This works but bypasses the harness's intended tool routing.

3. **grep is overused as a first step.** 6/10 queries started with grep before anything else. The agent uses grep as a "find the product ID first" step, which is reasonable but adds an extra tool call.

4. **User context injection reduces tool calls.** When the API pre-injects user profile data (purchases, reviews), the agent doesn't need to re-fetch it via graph_traverse. This is efficient but means we can't measure "would the agent use graph_traverse for user data" since the data is already there.

5. **Multi-hop chains work well when triggered.** Query 8 (similar ingredients) triggered 6 graph_traverse calls in a chain. The agent CAN do multi-hop -- it just needs the right signal.

## Recommendations

1. **Boost graph_traverse in tool description** -- Add explicit examples like "Use graph_traverse to find ingredients (contains_ingredient), related products (also_bought), category siblings (belongs_to)."

2. **Add ingredient-specific routing** -- When query mentions "ingredients", the system prompt should hint at `contains_ingredient` edges.

3. **Consider demoting surrealql_query** -- It's being used as a shortcut around graph_traverse. If graph awareness is the goal, make surrealql_query a last-resort tool.

4. **grep-first pattern is acceptable** -- Using grep to locate entities before graph traversal is reasonable. Don't fight this pattern.
