# Adversarial Edge Cases — Stress Test Results

**Date**: 2026-03-08
**User**: charlotte_gong
**Endpoint**: POST http://localhost:8002/chat
**Pacing**: 15-30s between queries (rate limits required longer waits)

---

## Individual Query Results

### Query 1: "Why did I buy what I bought?"
**What this tests**: Can agent reason about purchase motivations using graph context (goals, reviews)?
**Actual tools**: NONE (0 tool calls)
**Graph traverse calls**: 0
**Response quality**: ADEQUATE
**Key observation**: Agent answered entirely from pre-loaded user context (injected at chat start) without making any tool calls. The response mentioned "Clinique Moisture Surge and LANEIGE products" and their hydrating properties — plausible but unverified. It never actually looked up purchase history, reviews, or goals to ground its reasoning.
**Verdict**: SUBOPTIMAL — should have used `graph_traverse(customer->placed->contains)` and `graph_traverse(product->supports_goal)` to ground the answer in actual data.

---

### Query 2: "What am I missing from a complete skincare routine based on what I already own?"
**What this tests**: Gap analysis — needs category/goal knowledge + user purchase history
**Actual tools**: `cat(/users/charlotte_gong)`, `tree(/categories, depth=2)`
**Graph traverse calls**: 0
**Response quality**: GOOD
**Key observation**: Agent correctly used `cat` to get user profile and `tree` to see category hierarchy. It identified serums and sunscreen as gaps. However, it did NOT traverse the graph to find what categories Charlotte's purchases belong to — it relied on the pre-loaded context to know her purchases rather than verifying via `graph_traverse(customer->placed->contains->belongs_to)`.
**Verdict**: SUBOPTIMAL — correct answer direction but lacked graph-grounded verification of which categories are already covered.

---

### Query 3: "Find me the cheapest product with the same key ingredient as my most expensive purchase"
**What this tests**: Multi-hop with numerical reasoning — purchases->ingredients->products->price sort
**Actual tools**: `cat(/users/charlotte_gong)`, `cat(/products/...)` x3, `graph_traverse(product->contains_ingredient)` x3
**Graph traverse calls**: 3 (all `contains_ingredient`, `out` direction)
**Response quality**: POOR
**Key observation**: The agent correctly identified the multi-hop chain: (1) look up user profile, (2) cat most expensive products, (3) traverse `contains_ingredient` edges. However, all 3 ingredient traversals returned empty (no ingredient data in DB), and the agent gave up rather than falling back to text-based ingredient extraction from product descriptions. The reasoning chain was sound but the data gap killed it.
**Verdict**: CORRECT (tool selection was right) — but response was POOR because it didn't try `grep` or `find` as fallback when graph data was missing.

---

### Query 4: "Do any of my past purchases have bad reviews from other customers?"
**What this tests**: Reverse traversal — product<-contains<-order<-has_review<-review, filter by sentiment
**Actual tools**: `graph_traverse(customer->placed)` x1, `ls(/products/)` x1, `graph_traverse(order->contains)` x5, `graph_traverse(product->has_review, in)` x5
**Graph traverse calls**: 11 (1 placed + 5 contains + 5 has_review)
**Response quality**: GOOD
**Key observation**: EXCELLENT graph usage. The agent executed the full multi-hop chain: customer -> orders -> products -> reviews. It correctly used `direction: "in"` for `has_review` to find reviews pointing at products. The `ls(/products/)` call was unnecessary overhead. Response said "no negative reviews" — this could be data-accurate or could mean it didn't properly filter by sentiment (unclear without checking raw data).
**Verdict**: CORRECT — best graph traversal example in this test suite. 11 graph calls with correct edge types and directions.

---

### Query 5: "What's trending that I haven't tried yet?"
**What this tests**: Requires knowing what user HAS bought (graph) + what's popular (aggregation) + set difference
**Actual tools**: `ls(/products/)`, `graph_traverse(customer->placed)`, `cat(/users/charlotte_gong/orders/)`
**Graph traverse calls**: 1 (placed only)
**Response quality**: ADEQUATE
**Key observation**: Agent used `graph_traverse` for purchase history and `ls` for product catalog. However, it has no aggregation tool for "trending" — it can't count orders per product or sort by popularity. It returned 3 products but the "trending" claim is unverifiable. The set difference logic (what she hasn't tried) required the graph traversal which was correctly done. Missing: `surrealql_query` for aggregation (COUNT orders per product, ORDER BY DESC).
**Verdict**: SUBOPTIMAL — correct purchase history lookup, but "trending" was fabricated without actual popularity data. Should have used `surrealql_query` for aggregation.

---

### Query 6: "Build me a gift set of 3 products under £50 total that complement each other"
**What this tests**: Complex constraint satisfaction — price filtering + related_to/also_bought for complementary items
**Actual tools**: `find("hydrating moisturizer")`, `find("gentle cleanser")`, `find("lightweight serum")`, `cat(/products/...)` x3
**Graph traverse calls**: 0
**Response quality**: POOR
**Key observation**: The agent used `find` (semantic search) to get products by category but NEVER used `graph_traverse(related_to)` or `graph_traverse(also_bought)` to verify the products actually complement each other. Worse: **the total was £69.96, exceeding the £50 budget** — the agent acknowledged this failure in its response. It also didn't use price filtering or sorting. No graph traversal was used to find genuinely complementary products.
**Verdict**: WRONG — failed the core constraint (£50 budget) and didn't use graph edges for complementarity.

---

### Query 7: "If I liked LANEIGE Water Bank, would I like anything from a completely different category?"
**What this tests**: Cross-category recommendation — needs also_bought or related_to across category boundaries
**Actual tools**: `graph_traverse(product->also_bought)`, `graph_traverse(product->related_to)`
**Graph traverse calls**: 2 (also_bought + related_to)
**Response quality**: POOR
**Key observation**: The agent correctly identified the right tool calls — `also_bought` and `related_to` graph edges — but used the wrong product ID (`product:laneige_water_bank_gentle_gel_cleanser` — a slug, not the actual hash ID). Both returned empty. The agent then gave up rather than (a) looking up the correct product ID first via `find` or `grep`, or (b) trying `cat` on the product to get real ID, or (c) falling back to `find` for similar products in other categories.
**Verdict**: SUBOPTIMAL — correct strategy (graph traversal for recommendations) but wrong execution (bad product ID, no fallback).

---

### Query 8: "Summarize my relationship with this store — what I've bought, reviewed, and what you'd suggest next"
**What this tests**: Comprehensive graph exploration — placed, contains, has_review, also_bought, supports_goal all relevant
**Actual tools**: `cat(/users/charlotte_gong)`, `graph_traverse(customer->placed)`
**Graph traverse calls**: 1 (placed only)
**Response quality**: ADEQUATE
**Key observation**: For a query requesting a comprehensive summary, the agent only made 2 tool calls. It got purchase history via `graph_traverse` but never followed through to `contains` (what products), `has_review` (what she reviewed), or `supports_goal` / `also_bought` (what to suggest next). The response was plausible but shallow — it mentioned specific products and ratings that likely came from pre-loaded context rather than verified graph traversal.
**Verdict**: SUBOPTIMAL — should have done 5+ graph traversals (placed->contains->has_review, supports_goal, also_bought) for a truly comprehensive answer.

---

## Summary Stats

| # | Query | Tools | Graph Calls | Edge Types Used | Quality | Verdict |
|---|-------|-------|-------------|-----------------|---------|---------|
| 1 | Why did I buy what I bought? | 0 | 0 | none | ADEQUATE | SUBOPTIMAL |
| 2 | Missing from skincare routine? | 2 | 0 | none | GOOD | SUBOPTIMAL |
| 3 | Cheapest with same ingredient | 7 | 3 | contains_ingredient | POOR | CORRECT* |
| 4 | Bad reviews on my purchases? | 12 | 11 | placed, contains, has_review | GOOD | CORRECT |
| 5 | Trending I haven't tried? | 3 | 1 | placed | ADEQUATE | SUBOPTIMAL |
| 6 | Gift set under £50 | 6 | 0 | none | POOR | WRONG |
| 7 | Cross-category from LANEIGE? | 2 | 2 | also_bought, related_to | POOR | SUBOPTIMAL |
| 8 | Summarize my relationship | 2 | 1 | placed | ADEQUATE | SUBOPTIMAL |

**Overall**: 1 CORRECT, 1 CORRECT* (right tools, poor response), 5 SUBOPTIMAL, 1 WRONG

*Query 3 is CORRECT on tool selection but POOR on response quality due to missing data fallbacks.

### Aggregate Metrics
- **Total tool calls across 8 queries**: 34
- **Total graph_traverse calls**: 18
- **Queries with 0 graph calls**: 3/8 (37.5%)
- **Queries that exceeded constraints**: 1/8 (Query 6 busted £50 budget)
- **Rate limit errors**: 3 retries needed (queries 2 and 3)

---

## Biggest Gaps

### 1. Over-reliance on Pre-loaded Context
Queries 1, 2, 5, and 8 all relied heavily on user context injected at chat start rather than verifying via graph traversal. The agent "knows" things about Charlotte from the context blob but doesn't ground its claims in actual data lookups. This creates hallucination risk when the context is stale or incomplete.

### 2. No Fallback When Graph Data is Missing
Queries 3 and 7 both had correct graph traversal strategies that returned empty results. In both cases, the agent gave up rather than trying alternative approaches (`grep` for ingredient text, `find` for similar products, `surrealql_query` for raw queries). A robust agent should have 2-3 fallback strategies.

### 3. No Numerical Constraint Enforcement
Query 6 failed a hard £50 budget constraint. The agent doesn't have a mechanism to enforce numerical constraints — it selected products individually without tracking running totals. This is a fundamental gap for e-commerce use cases.

### 4. Missing Aggregation Capabilities
Query 5 ("trending") required counting orders per product — an aggregation the agent couldn't do with its current tool set without `surrealql_query`. The agent fabricated "trending" without actual popularity data.

### 5. Wrong Product IDs for Graph Traversal
Query 7 used a slugified product name (`product:laneige_water_bank_gentle_gel_cleanser`) instead of the actual hash ID. The agent should first resolve product names to IDs via `find` or `grep` before attempting graph traversal.

### 6. Shallow Graph Exploration on Complex Queries
Queries 1, 5, and 8 all warranted multi-hop traversals but the agent stopped after 0-1 hops. The GATHER->ACT->VERIFY harness should encourage deeper exploration when the query requires it.

---

## Bright Spots

### 1. Query 4: Masterclass in Graph Traversal
The "bad reviews" query showed the agent at its best — 11 graph traversals covering 3 edge types with correct directions. It executed the full `customer->placed->contains->has_review` chain, demonstrating the agent CAN do multi-hop reasoning when the query clearly maps to graph operations.

### 2. Query 3: Correct Multi-Hop Strategy
Despite the poor response, the ingredient query showed correct strategic thinking: look up user -> find most expensive product -> traverse `contains_ingredient`. The 7-tool-call chain was well-structured. The failure was in data availability, not tool selection.

### 3. Consistent `cat` for User Profile
The agent reliably used `cat(/users/charlotte_gong)` to ground its understanding of the user — a correct first step for personalized queries.

### 4. `find` for Semantic Product Search
Query 6 showed effective use of `find` with meaningful semantic queries ("hydrating moisturizer", "gentle cleanser", "lightweight serum") rather than generic searches. The tool selection was appropriate even if constraint handling was poor.

### 5. Correct Edge Type Selection
When the agent DID use `graph_traverse`, it consistently selected the right edge types: `placed` for orders, `contains` for order items, `has_review` for reviews, `contains_ingredient` for ingredients, `also_bought`/`related_to` for recommendations. The graph schema understanding is solid.

---

## Recommendations

1. **Mandate graph grounding**: When user context claims something ("you bought X"), the agent should verify it via graph traversal before building on it.
2. **Add fallback chains**: graph_traverse(empty) -> grep(text search) -> find(semantic) -> surrealql_query(raw).
3. **Budget/constraint tracking**: System prompt should instruct running totals for numerical constraints.
4. **Product ID resolution**: Always `find` or `grep` first to get actual IDs before `graph_traverse`.
5. **Depth encouragement for complex queries**: Detect "summarize", "comprehensive", "complete" keywords and trigger deeper multi-hop traversal.
