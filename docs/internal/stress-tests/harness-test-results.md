# Harness Test Scenario

## Query: "I have dry skin and I'm looking for a moisturizer under 30 that other customers loved"

### Expected GATHER Steps

1. **`ls /categories/`** -- See what product categories exist (skincare? beauty? body care?)
   - Expected output: List of category IDs and names
   - Purpose: Identify the right category path to explore

2. **`tree /categories/skincare` (or equivalent)** -- See the category hierarchy and products within
   - Expected output: Tree view showing subcategories and products with prices
   - Purpose: Understand what skincare products are available before searching

3. **`explore_schema("product")`** -- Check what fields products have
   - Expected output: Fields like name, price, description, avg_rating, dietary_tags, etc.
   - Purpose: Know that `price` and `avg_rating` fields exist for filtering

### Expected ACT Steps

4. **`find("moisturizer dry skin hydrating", doc_type="product")`** -- Hybrid semantic + keyword search
   - Expected output: Ranked list with RRF scores, product titles, source_ids
   - Purpose: Find products matching the conceptual need (dry skin + moisturizer)

5. **`surrealql_query("SELECT id, name, price, avg_rating FROM product WHERE price < 30 ORDER BY avg_rating DESC LIMIT 10")`** -- Filter by price constraint
   - Expected output: Products under 30 sorted by customer rating
   - Purpose: Apply the price constraint and find highly-rated products

6. **`graph_traverse("product:hydrating_cream", "also_bought", "out")`** -- See what customers who bought this also purchased
   - Expected output: Co-purchased products (social proof: "other customers loved")
   - Purpose: Leverage purchase graph for social proof recommendations

### Expected VERIFY Steps

7. **`get_record("product:hydrating_cream")`** -- Verify top recommendation
   - Expected output: Full product record with price, description, all fields
   - Verify: Price is actually under 30, description mentions dry skin/moisturizing

8. **`cat /products/hydrating_cream`** -- Double-check with full graph context
   - Expected output: All fields + related products + category
   - Verify: Category is skincare, related products are relevant

9. **`get_record("product:second_pick")`** -- Verify second recommendation
   - Expected output: Full product record
   - Verify: Price and relevance confirmed

### Expected Response

The agent should respond with:
- 2-3 verified product recommendations with accurate prices
- Brief description of why each suits dry skin
- Mention of what other customers also bought (from `also_bought` traversal)
- Products all genuinely under 30 (verified via `get_record`)
- Health disclaimer if applicable

### Harness Verification Checklist

- [x] GATHER phase provides data landscape orientation
- [x] ACT phase uses appropriate tools (hybrid search + price filter + social graph)
- [x] VERIFY phase confirms every recommended product via `get_record` or `cat`
- [x] No product recommended without tool-verified data
- [x] Price constraint verified against actual record, not just search snippet
- [x] Graph traversal adds social proof dimension to recommendations

---

## Test Results: Implementation Verified

- **48/48 tests passing** after adding 5 fs_tools to ALL_TOOLS (13 total)
- **Tool registry**: All 13 tools import correctly with phase annotations
- **System prompt**: Updated with GATHER -> ACT -> VERIFY loop
- **Harness prompt**: Created as specialized variant at `harness.md`
- **Tool descriptions**: Phase annotations added to all fs_tools docstrings
- **No regressions**: All existing tests continue to pass
