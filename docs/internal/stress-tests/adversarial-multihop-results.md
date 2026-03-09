# Adversarial Multi-Hop Graph Traversal Test Results

**Date**: 2026-03-08
**Tester**: multihop-tester agent
**API Endpoint**: POST http://localhost:8002/chat
**User**: charlotte_gong
**Model**: claude-sonnet-4-20250514 (Anthropic) -- switched from OpenAI gpt-4o due to persistent rate limits
**Notes**: Query 1 used default OpenAI model before rate limits hit. All subsequent queries used Anthropic Claude Sonnet.

---

## Individual Query Results

### Query 1: "What ingredients are shared between LANEIGE Water Bank and Clinique Moisture Surge?"
**Expected tools**: grep/find to locate both products, then graph_traverse contains_ingredient on each, compare
**Actual tools**: cat (x3), grep (x2), cat (x2) -- 6 total calls
**Graph traverse used?**: NO (0)
**Response quality**: Found the LANEIGE products but could not locate Clinique Moisture Surge. No ingredient comparison was performed. The agent did not attempt graph_traverse contains_ingredient at all.
**Verdict**: WRONG
**Why**: Agent never attempted graph_traverse with contains_ingredient edge type; fell back to text search and gave up when one product wasn't found by exact slug.

---

### Query 2: "What goals do my past purchases support?"
**Expected tools**: graph_traverse placed (customer->order->product), then graph_traverse supports_goal on products
**Actual tools**: cat (user), graph_traverse supports_goal (x3), ls, surrealql_query, explore_schema, tree, surrealql_query, cat -- 10 total calls
**Graph traverse used?**: YES (3 -- all supports_goal on specific products)
**Response quality**: Excellent. Retrieved user profile, attempted graph traversal on multiple products for goals, explored schema when edges returned empty, and synthesized a meaningful answer from product descriptions. Acknowledged that goal mappings weren't fully populated.
**Verdict**: CORRECT
**Why**: Agent properly used graph_traverse supports_goal on individual products, explored schema to understand the goal table, and gave a well-reasoned answer even when edges were sparse.

---

### Query 3: "Find products that customers who bought what I bought also purchased"
**Expected tools**: graph_traverse placed, then graph_traverse also_bought on those products
**Actual tools**: cat (user), graph_traverse also_bought (x2), graph_traverse related_to (x1), find, cat -- 6 total calls
**Graph traverse used?**: YES (3 -- 2x also_bought, 1x related_to)
**Response quality**: Good. Used also_bought edges correctly to find co-purchased products. Identified that the user already owns most popular items. Found one new suggestion (gel version of existing moisturizer).
**Verdict**: CORRECT
**Why**: Agent correctly used also_bought graph traversal on the user's purchased products and synthesized recommendations.

---

### Query 4: "What category has the most products I've bought from?"
**Expected tools**: cat user or graph_traverse placed, then graph_traverse belongs_to on products
**Actual tools**: cat (user), cat (x4 products) -- 5 total calls
**Graph traverse used?**: NO (0)
**Response quality**: Answer is correct (Premium subcategory) but derived entirely from reading product records directly rather than using graph traversal. Did not use belongs_to edges at all.
**Verdict**: SUBOPTIMAL
**Why**: Correct answer but bypassed graph_traverse belongs_to entirely; manually read each product and counted categories from their fields instead of traversing the graph.

---

### Query 5: "Show me products related to things in my order history, but in a different category"
**Expected tools**: graph_traverse placed->contains, then related_to or also_bought, filter by category
**Actual tools**: cat (user), graph_traverse related_to (x2), cat (x2), find (x3), cat (x2) -- 10 total calls
**Graph traverse used?**: YES (2 -- both related_to)
**Response quality**: Good. Used related_to edges to find connections, then supplemented with find queries for brand-specific searches in different categories. Recommended Clinique serum and INKEY List serum as cross-category options.
**Verdict**: CORRECT
**Why**: Agent correctly used graph_traverse related_to and then filtered/searched for products in different categories.

---

### Query 6: "What are the top-rated products that share ingredients with my purchases?"
**Expected tools**: graph_traverse placed->contains->contains_ingredient, then reverse traverse or find
**Actual tools**: cat (user), cat (x3 products), find (x2), cat (x2) -- 8 total calls
**Graph traverse used?**: NO (0)
**Response quality**: Decent recommendations based on known ingredient types (hyaluronic acid, ceramides) from product descriptions, but no actual graph traversal for ingredients. Used find queries with ingredient keywords instead.
**Verdict**: SUBOPTIMAL
**Why**: Agent never used graph_traverse contains_ingredient; instead inferred ingredients from product descriptions and used find with ingredient keywords. The answer is reasonable but doesn't prove actual ingredient graph traversal.

---

### Query 7: "Walk me through the full graph connections from my profile"
**Expected tools**: Multiple graph_traverse calls exploring different edge types from customer node
**Actual tools**: cat (user), graph_traverse also_bought (x1), cat (product), graph_traverse supports_goal (x1), ls, tree, graph_traverse contains_ingredient (x1) -- 7 total calls
**Graph traverse used?**: YES (3 -- also_bought, supports_goal, contains_ingredient)
**Response quality**: Excellent and comprehensive. Mapped out the full graph structure: profile node, 15 orders via placed edges, 8 unique products, co-purchase network (40+ also_bought connections), category connections. Noted missing goal and ingredient edges. This was the most graph-aware response.
**Verdict**: CORRECT
**Why**: Agent systematically explored multiple edge types (also_bought, supports_goal, contains_ingredient) and synthesized a complete graph map with honest reporting of missing edges.

---

### Query 8: "Compare the ingredient profiles of the top 3 moisturizers"
**Expected tools**: find moisturizers, then graph_traverse contains_ingredient on each
**Actual tools**: find (x2), cat (x3), surrealql_query (x1), grep (x1) -- 7 total calls
**Graph traverse used?**: NO (0)
**Response quality**: Good comparison of 3 moisturizers with ingredient details, but ingredients were extracted from product descriptions rather than graph traversal. Used surrealql_query to search by name and find to discover products.
**Verdict**: SUBOPTIMAL
**Why**: Agent never used graph_traverse contains_ingredient; relied entirely on product description text for ingredient information. Correct answer but wrong method.

---

## Summary Table

| # | Query | Graph Traverse? | Count | Verdict | Key Issue |
|---|-------|----------------|-------|---------|-----------|
| 1 | Shared ingredients between 2 products | NO | 0 | WRONG | Never attempted contains_ingredient traversal |
| 2 | Goals from past purchases | YES | 3 | CORRECT | Proper supports_goal traversal + schema exploration |
| 3 | Also-bought collaborative filtering | YES | 3 | CORRECT | Good also_bought + related_to usage |
| 4 | Category with most purchases | NO | 0 | SUBOPTIMAL | Read products directly, skipped belongs_to |
| 5 | Cross-category related products | YES | 2 | CORRECT | Used related_to edges effectively |
| 6 | Top-rated + shared ingredients | NO | 0 | SUBOPTIMAL | Used find with keywords instead of graph |
| 7 | Full graph connections from profile | YES | 3 | CORRECT | Most thorough graph exploration |
| 8 | Ingredient comparison of moisturizers | NO | 0 | SUBOPTIMAL | Ingredients from descriptions, not graph |

## Aggregate Statistics

- **Total queries**: 8
- **CORRECT**: 4 (50%)
- **SUBOPTIMAL**: 3 (37.5%)
- **WRONG**: 1 (12.5%)
- **Queries using graph_traverse**: 4/8 (50%)
- **Total graph_traverse calls**: 11 across all queries
- **Total tool calls**: ~59 across all queries

## Key Findings

### 1. contains_ingredient Edge is Systematically Ignored
The most critical finding: across 4 queries that explicitly or implicitly required ingredient traversal (Q1, Q6, Q7, Q8), the agent only attempted `contains_ingredient` in Q7 (the explicit "walk me through graph connections" query). In all other cases, it relied on text-based search or product description parsing. This suggests the agent doesn't naturally reach for ingredient graph traversal unless explicitly prompted about "graph connections."

### 2. belongs_to Edge Underutilized
Q4 asked about categories but the agent read product records directly instead of using `belongs_to` edges. The category information is available in both places, but graph traversal would be the canonical approach for a graph-powered system.

### 3. also_bought and related_to Work Well
When queries explicitly imply collaborative filtering (Q3, Q5), the agent reliably uses `also_bought` and `related_to` edges. These seem to be the best-understood graph operations.

### 4. supports_goal Works When Prompted
Q2 successfully triggered `supports_goal` traversal. The agent correctly explored the goal schema and reported on missing edges.

### 5. Fallback to find/grep is Too Aggressive
The agent quickly falls back to `find` (semantic search) and `grep` (keyword search) when graph traversal could provide more precise answers. This is especially problematic for ingredient queries where the graph should be the authoritative source.

### 6. Model Behavior Note
These results are for Anthropic Claude Sonnet 4, not OpenAI GPT-4o. The graph traversal patterns may differ between models. Q1 (the only GPT-4o query) was also the worst performer, but that's a sample of 1 and may be coincidence.

## Recommendations

1. **Boost contains_ingredient in tool descriptions**: Add explicit examples showing when to use ingredient traversal (e.g., "To compare ingredients between products, use graph_traverse with contains_ingredient edge").
2. **Add ingredient-aware system prompt examples**: Include worked examples in the system prompt showing multi-hop ingredient comparison workflows.
3. **Consider auto-chaining**: When a query mentions "ingredients" or "ingredient profiles," the system could hint the agent toward contains_ingredient traversal.
4. **belongs_to should be first-class**: Category queries should route through the graph, not through reading product fields.
5. **Test with OpenAI model**: Run the same suite when rate limits clear to compare model behavior.
