# Adversarial Edge-Type Coverage Test Results

**Date**: 2026-03-08
**API**: POST http://localhost:8002/chat
**User**: charlotte_gong
**Pacing**: 8-15s between queries (60s on rate-limit retries)

---

## Per-Query Results

### Query 1: "Show me all my orders and when I placed them" -- Edge: placed
**Expected tools**: graph_traverse with edge_type=placed (customer->order), or cat on user path
**Actual tools**: `cat /users/charlotte_gong`
**Graph traverse used?**: NO
**Correct edge type?**: N/A -- graph_traverse was not invoked
**Response quality**: Returned all 5 orders with IDs, products, prices, and status. Complete and accurate.
**Verdict**: SUBOPTIMAL -- `cat` on the user profile was sufficient to get order data embedded in the user doc, but it bypassed the `placed` graph edge entirely. The agent took a shortcut via the denormalized user view.

---

### Query 2: "What products were in my most recent order?" -- Edge: contains
**Expected tools**: graph_traverse with edge_type=contains (order->product), or cat on order path
**Actual tools**: `cat /users/charlotte_gong/orders/`
**Graph traverse used?**: NO
**Correct edge type?**: N/A -- graph_traverse was not invoked
**Response quality**: Correctly identified the most recent order and its product (Clinique Moisture Surge gift set, GBP 50). Accurate.
**Verdict**: SUBOPTIMAL -- Used `cat` on orders path instead of graph_traverse with `contains` edge. The filesystem abstraction provided the data without needing graph traversal.

---

### Query 3: "What reviews have I left on my purchases?" -- Edge: has_review
**Expected tools**: graph_traverse with edge_type=has_review (order->review)
**Actual tools**: `cat /users/charlotte_gong`
**Graph traverse used?**: NO
**Correct edge type?**: N/A -- graph_traverse was not invoked
**Response quality**: Returned 2 reviews with product names and review text. Accurate and complete.
**Verdict**: SUBOPTIMAL -- Reviews were accessible via the user profile cat, bypassing the `has_review` graph edge. The agent never needed to traverse the graph.

---

### Query 4: "What category does The Ordinary Niacinamide belong to?" -- Edge: belongs_to
**Expected tools**: graph_traverse with edge_type=belongs_to (product->category)
**Actual tools**: `grep "The Ordinary Niacinamide" /products`, `ls /categories/`, `grep "The Ordinary Niacinamide" /categories`, `find "The Ordinary Niacinamide" doc_type=product`, `cat /products/f2af004352a06a99dca765596240cbc3`
**Graph traverse used?**: NO
**Correct edge type?**: N/A -- graph_traverse was not invoked
**Response quality**: Correctly identified "Serums & Treatments" under Skincare. Accurate.
**Verdict**: SUBOPTIMAL -- Used 5 tool calls (grep, ls, grep, find, cat) when a single `graph_traverse` with `belongs_to` would have sufficed. The category was likely embedded in the product document, but the agent used a scattergun approach.

---

### Query 5: "What are the subcategories under Skincare?" -- Edge: child_of
**Expected tools**: graph_traverse with edge_type=child_of (category->category)
**Actual tools**: `tree /categories/skincare`
**Graph traverse used?**: NO
**Correct edge type?**: N/A -- graph_traverse was not invoked
**Response quality**: Correctly listed 3 subcategories (Premium, Cleansers & Moisturisers, Serums & Treatments). Accurate.
**Verdict**: SUBOPTIMAL -- `tree` on the categories path was a reasonable approach for hierarchy, but it bypassed the `child_of` graph edge. The filesystem metaphor provided the answer without graph traversal.

---

### Query 6: "What do people who bought LANEIGE Water Bank usually also get?" -- Edge: also_bought
**Expected tools**: graph_traverse with edge_type=also_bought (product->product)
**Actual tools**: `graph_traverse start_id=product:laneige_water_bank_gel_cleanser edge_type=also_bought direction=out`
**Graph traverse used?**: YES -- edge_type: also_bought
**Correct edge type?**: YES
**Response quality**: No co-purchase data found (empty result). The graph edge exists but had no data for this product. The response was honest about the empty result.
**Verdict**: CORRECT -- The agent correctly identified this as a graph traversal query and used the right edge type. Empty result is a data issue, not a tool selection issue.

---

### Query 7: "Which products support the hydration or clear skin goal?" -- Edge: supports_goal
**Expected tools**: graph_traverse with edge_type=supports_goal (product->goal), traversed in reverse
**Actual tools**: `tree /goals/hydration`, `tree /goals/clear_skin`
**Graph traverse used?**: NO
**Correct edge type?**: N/A -- graph_traverse was not invoked
**Response quality**: Reported no products found under those goals. Unclear if this is a data issue or if the tree path couldn't find the goal nodes.
**Verdict**: SUBOPTIMAL -- Used `tree` on goal paths instead of `graph_traverse` with `supports_goal`. The filesystem approach may have missed data that a graph traversal would have found. Should have tried `graph_traverse` with `supports_goal` edge from the goal node.

---

### Query 8: "What ingredients are in Clinique Moisture Surge?" -- Edge: contains_ingredient
**Expected tools**: graph_traverse with edge_type=contains_ingredient (product->ingredient)
**Actual tools**: `grep "Clinique Moisture Surge" /products`, `find "Clinique Moisture Surge" doc_type=product`, `cat /products/14555ba663de8689feacf1d0819cc3b3`
**Graph traverse used?**: NO
**Correct edge type?**: N/A -- graph_traverse was not invoked
**Response quality**: Found a Clinique Moisture Surge product and mentioned "5% lactic acid" from the product description. Did NOT traverse the `contains_ingredient` graph edge to get a structured ingredient list.
**Verdict**: SUBOPTIMAL -- The agent found ingredient info embedded in the product doc text but did not use `graph_traverse` with `contains_ingredient` to get structured ingredient data. A graph traversal could provide richer ingredient details.

---

### Query 9: "What products are related to The INKEY List Ceramide Moisturizer?" -- Edge: related_to
**Expected tools**: graph_traverse with edge_type=related_to (product->product)
**Actual tools**: `grep "The INKEY List Ceramide Moisturizer" /products`, `find "The INKEY List Ceramide Moisturizer" doc_type=product`, `cat /products/73326828aa5efe1ba096223de496f596`
**Graph traverse used?**: NO
**Correct edge type?**: N/A -- graph_traverse was not invoked
**Response quality**: Found the product and described it, but did NOT return any related products. The response offered to "explore more products in the same category" instead of traversing the `related_to` edge.
**Verdict**: WRONG -- The query explicitly asked for related products, which maps directly to the `related_to` graph edge. The agent failed to use `graph_traverse` and instead just described the product itself. This is a missed tool selection.

---

## Coverage Matrix

| Edge Type | Query | graph_traverse Used? | Correct Edge? | Verdict |
|-----------|-------|---------------------|---------------|---------|
| placed | Q1: "Show me all my orders..." | NO | N/A | SUBOPTIMAL |
| contains | Q2: "What products were in my most recent order?" | NO | N/A | SUBOPTIMAL |
| has_review | Q3: "What reviews have I left..." | NO | N/A | SUBOPTIMAL |
| belongs_to | Q4: "What category does The Ordinary..." | NO | N/A | SUBOPTIMAL |
| child_of | Q5: "What are the subcategories under Skincare?" | NO | N/A | SUBOPTIMAL |
| also_bought | Q6: "What do people who bought LANEIGE..." | YES | YES | CORRECT |
| supports_goal | Q7: "Which products support hydration..." | NO | N/A | SUBOPTIMAL |
| contains_ingredient | Q8: "What ingredients are in Clinique..." | NO | N/A | SUBOPTIMAL |
| related_to | Q9: "What products are related to..." | NO | N/A | WRONG |

---

## Summary Statistics

- **Total queries**: 9
- **graph_traverse used**: 1/9 (11.1%)
- **Correct edge type when used**: 1/1 (100%)
- **CORRECT verdicts**: 1 (also_bought)
- **SUBOPTIMAL verdicts**: 7 (placed, contains, has_review, belongs_to, child_of, supports_goal, contains_ingredient)
- **WRONG verdicts**: 1 (related_to)
- **Rate limit errors**: 3 (queries 6, 8 x2) -- retried successfully after delays

---

## Key Findings

### 1. The agent strongly prefers filesystem tools over graph_traverse
Only 1 of 9 queries triggered `graph_traverse`. The agent defaults to `cat`, `grep`, `find`, `ls`, and `tree` -- the filesystem metaphor is so intuitive that the agent reaches for it even when graph traversal would be more appropriate.

### 2. Denormalized data in user/product docs makes graph traversal unnecessary for many queries
Queries 1-3 (placed, contains, has_review) were all answerable from the user profile document alone. The `cat /users/charlotte_gong` path returns orders, products, and reviews inline, so the agent never needs to traverse graph edges.

### 3. Category hierarchy is served by `tree`, not graph_traverse
Query 5 (child_of) was naturally handled by `tree /categories/skincare`, which is the filesystem equivalent of traversing `child_of` edges. This is actually a reasonable tool choice.

### 4. The agent only uses graph_traverse when the query implies a relationship not available in document text
Query 6 (also_bought) was the only one that triggered graph_traverse, likely because "what do people also buy" has no answer in the product document itself -- it requires traversing a co-purchase graph edge.

### 5. Query 9 (related_to) is a clear failure
The agent should have used `graph_traverse` with `related_to` but instead just described the product. This is the worst result -- the user explicitly asked for related products and got none.

### 6. Multi-tool scatter pattern on Q4
Query 4 used 5 tool calls (grep, ls, grep, find, cat) when a single graph_traverse would have been cleaner. This suggests the agent lacks confidence in graph_traverse and falls back to brute-force search.

---

## Recommendations

1. **Boost graph_traverse in system prompt**: Add explicit guidance like "For relationship queries (who bought what, what's related to, what ingredients), prefer graph_traverse over cat/grep"
2. **Add graph_traverse examples to prompt**: Include worked examples for each edge type so the LLM sees the pattern
3. **Reduce denormalization**: If orders/reviews are always available via `cat /users/`, the agent will never use placed/has_review edges. Consider making the user doc lighter and requiring graph traversal for details.
4. **Add edge type hints to tool description**: The graph_traverse docstring should list all 9 edge types with example queries that map to each
5. **Test with "find related products" phrasing**: The `related_to` failure suggests the agent doesn't map "related products" to the graph edge
