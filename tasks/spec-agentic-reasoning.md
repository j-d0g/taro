# Spec: Agentic Reasoning Loop — "Claude Code for SurrealDB"

## Vision

The chatbot should feel like watching Claude Code solve a problem: visible stream-of-thought reasoning, dynamic graph exploration that reacts to what it finds, recursive traversal that goes deeper when promising paths emerge, and search that compounds user history with live web results. Not a single tool call and done — a living reasoning loop.

## 1. Stream-of-Thought Reasoning

### What
Between every tool call, the agent emits a short reasoning step visible to the user — what it found, what it's thinking, what it'll do next. Like Claude Code's thinking traces but for e-commerce search.

### Example
```
User: "I've been getting breakouts lately, what should I change in my routine?"

🔍 Let me check your profile and purchase history first...
[cat /users/emma_chen] → Emma, combination skin, goals: clear skin, anti-aging

💭 She's had combination skin but is now getting breakouts — could be a product
   reaction or seasonal change. Let me check what she's been using recently.
[ls /users/emma_chen/orders/] → 3 recent orders

💭 Her last order had The Ordinary AHA 30% + BHA 2% — that's a strong exfoliant.
   Could be over-exfoliating. Let me check the ingredients and find gentler alternatives.
[graph_traverse product:ordinary_aha_bha → contains_ingredient] → glycolic acid, salicylic acid
[find "gentle exfoliant sensitive breakout-prone skin"] → 4 results

💭 Found some options. Let me also check what worked well for her before — her
   Niacinamide serum had a 5-star review. Products with niacinamide might be safer.
[graph_traverse product:ordinary_niacinamide → related_to] → CeraVe PM, La Roche-Posay

✅ Based on your history, here's what I'd suggest...
```

### Implementation
- Use LangGraph's `StreamEvents` or custom callback handler to emit intermediate reasoning
- The agent's system prompt should instruct it to think out loud between tool calls
- Frontend renders these as thinking bubbles / trace cards with timestamps
- Each reasoning step references what was found and what decision was made

### Metrics
- **Reasoning steps per query**: target 2-5 visible thinking steps for complex queries
- **Reasoning relevance**: each step should reference specific data from the previous tool call
- **User engagement**: visible reasoning should feel like watching an expert think, not filler

---

## 2. Dynamic Graph Traversal Loop

### What
Instead of `graph_traverse(start, edge, depth=1)` as a one-shot, the agent should traverse iteratively — follow an edge, inspect what it finds, decide whether to go deeper or branch to a different edge. The graph becomes a search space the agent navigates intelligently.

### Current Problem
The agent calls `graph_traverse` once, gets results, moves on. It never:
- Follows a chain: product → also_bought → that product's ingredients → compare with user's preferences
- Branches: "this product is also_bought with X, but X has an ingredient the user is allergic to — skip, try Y instead"
- Recurses: "the category has subcategories, let me explore each"

### Design: Graph Navigator Tool
Replace single `graph_traverse` with a smarter pattern. Two options:

**Option A: Multi-hop graph_traverse** (simpler)
Enhance `graph_traverse` to support chained edges:
```python
graph_traverse(
    start_id="user:emma_chen",
    edges=["placed", "contains", "contains_ingredient"],  # chain of edges
    direction="out",
    filter_fn="name CONTAINS 'retinol'"  # optional SurrealQL filter at each hop
)
```

**Option B: Graph reasoning loop** (more impressive)
Add a `graph_reason` tool that takes a *question* and explores the graph to answer it:
```python
graph_reason(
    start_id="user:emma_chen",
    question="What ingredients has this user been exposed to that might cause breakouts?",
    max_hops=4
)
```
Internally this tool uses the LLM to decide which edges to follow at each hop.

**Recommendation**: Option A for reliability, but frame it as Option B in the demo by having the outer agent do the reasoning between calls.

### Metrics
- **Graph depth reached**: target average 2-3 hops per complex query (currently ~1)
- **Branching factor**: agent should explore 2+ paths before converging
- **Data compounds**: final answer should cite data from 3+ different nodes in the graph

---

## 3. Rich User Context — The Paper Trail

### What
Every user should have a rich, evolving context that makes recommendations genuinely personal. Not just "goals: muscle building" but a full history.

### Schema Additions
```surql
-- Extend user record with rich context fields
DEFINE FIELD tried_products ON user TYPE option<array<object>>;
-- Each: { product_id, liked: bool, reason: "too greasy", date }

DEFINE FIELD ingredient_reactions ON user TYPE option<array<object>>;
-- Each: { ingredient: "retinol", reaction: "irritation", severity: "mild" }

DEFINE FIELD preferences ON user TYPE option<object>;
-- { price_range: [10, 40], brands_liked: [...], brands_avoided: [...],
--   textures: ["lightweight", "gel"], scents: ["unscented"],
--   concerns: ["acne", "dark spots"], routine_complexity: "minimal" }

DEFINE FIELD chat_history_summary ON user TYPE option<array<string>>;
-- Distilled summaries from past conversations (append-only)

DEFINE FIELD repeat_purchases ON user TYPE option<array<object>>;
-- Each: { product_id, count, last_date, avg_interval_days }
```

### Graph Edges to Add
```surql
-- user -tried-> product (with outcome metadata)
DEFINE TABLE tried SCHEMAFULL TYPE RELATION IN user OUT product;
DEFINE FIELD liked ON tried TYPE bool;
DEFINE FIELD reason ON tried TYPE option<string>;
DEFINE FIELD date ON tried TYPE option<datetime>;

-- user -allergic_to-> ingredient
DEFINE TABLE allergic_to SCHEMAFULL TYPE RELATION IN user OUT ingredient;
DEFINE FIELD severity ON allergic_to TYPE option<string>;
DEFINE FIELD reaction ON allergic_to TYPE option<string>;
```

### Mock Data Requirements
For 5-10 demo users, each should have:
- 5-15 tried products (mix of liked and disliked with reasons)
- 2-3 ingredient sensitivities (e.g. "retinol causes redness", "fragrance triggers headaches")
- Detailed preferences object
- 3-5 repeat purchases with dates
- 2-3 distilled chat summaries
- Realistic order history spanning 6+ months

### Metrics
- **Personalization depth**: agent should reference 3+ user-specific data points per response
- **Negative filtering**: agent should actively avoid products with ingredients the user reacted to
- **History awareness**: agent should notice patterns (repeat purchases, brand loyalty, seasonal changes)

---

## 4. Graph Schema Navigation Guide

### Problem
The agent doesn't know the full graph structure upfront. It has to discover it, wasting tool calls. Claude Code has CLAUDE.md. We need the equivalent for the graph.

### Design: Auto-Injected Graph Map

**Option A: System prompt injection** (simplest)
Inject a concise graph map into the system prompt:
```markdown
## GRAPH MAP (auto-loaded)
user:emma_chen
  →placed→ order:* →contains→ product:*
  →tried→ product:* (liked, reason)
  →allergic_to→ ingredient:* (severity)

product:*
  →belongs_to→ category:*
  →contains_ingredient→ ingredient:*
  →also_bought→ product:* (weight)
  →related_to→ product:* (reason)
  →supports_goal→ goal:*

category:*
  →child_of→ category:* (vertical→subcategory)
```

**Option B: Schema node in SurrealDB** (more dynamic)
Store a `graph_map` record that the agent loads as its first GATHER step:
```surql
CREATE graph_map:main SET
  description = "Navigation guide for the Taro data graph",
  nodes = { ... },
  edges = { ... },
  traversal_patterns = [
    "To find what a user has tried: user→tried→product",
    "To check allergies before recommending: user→allergic_to→ingredient, then product→contains_ingredient→ingredient",
    "To find co-purchases: product→also_bought→product (follow weight for strength)",
    ...
  ]
```

**Option C: Both** (recommended)
- Inject a compact graph map in the system prompt (always available, no tool call needed)
- Store detailed traversal patterns in SurrealDB for the agent to consult when stuck
- The `explore_schema` tool should also return the graph map

### Metrics
- **First-tool accuracy**: agent should pick the right starting point without needing `ls /` first
- **Edge selection accuracy**: agent should pick the right edge type on first try >80% of the time

---

## 5. Compound Search Strategy

### What
The final recommendation shouldn't rely on a single `find` call. It should compound:
1. **User history**: what they've bought, tried, liked/disliked
2. **Graph context**: related products, ingredient compatibility, goal alignment
3. **Hybrid search**: vector + keyword search for candidates
4. **Web search**: fill gaps with live product data from Tavily (lookfantastic.com, myprotein.com)
5. **Filtering**: remove anything with ingredients the user reacted to

### Search Pipeline (per complex query)
```
1. Load user context (cat /users/{id})
2. Check constraints (allergies, dislikes, budget)
3. Hybrid search for candidates (find)
4. For top candidates: check ingredient compatibility (graph_traverse → contains_ingredient)
5. Filter out incompatible products
6. Check what similar users bought (also_bought edges)
7. If <3 good candidates from SurrealDB: web_search to fill gaps
8. Rank by: relevance × user_fit × ingredient_safety × social_proof
9. Verify top picks (cat on each)
10. Present with reasoning trail
```

### Web Search Enhancement
Currently `web_search` is a last resort. It should be a first-class signal:
- Domain-scope to lookfantastic.com, myprotein.com, theordinary.com
- When SurrealDB has the product but no reviews: search for reviews online
- When user asks about trends/new products: always include web results
- Combine SurrealDB product data + web prices/availability for complete answer

### Metrics
- **Search sources per query**: target 2-3 different data sources for complex queries
- **Negative filtering rate**: should exclude products with known user incompatibilities
- **Web augmentation rate**: web_search used in 20-30% of queries (not 0%, not 100%)

---

## 6. Self-Improvement Loop

### What
After every conversation, the system should get smarter:
1. **Distill user context** (already built: POST /distill)
2. **Log successful patterns** → `learned_pattern` table
3. **Log failures** → `failure_record` table
4. **Update user tried_products** when they mention products they've used

### Auto-Distillation Enhancement
Current distill is called manually. Should be automatic:
- After every conversation of 3+ turns, auto-distill
- Extract: new preferences discovered, products discussed, ingredients mentioned
- Update user record: append to chat_history_summary, update preferences, add tried_products
- Store which tool chains worked well for this query type

### Metrics
- **Context growth**: user context should grow by 1-2 sentences per meaningful conversation
- **Pattern coverage**: learned_pattern should have entries for top 20 query types after 50 conversations
- **Recommendation improvement**: same query should give better results after user history accumulates

---

## 7. Richer Mock Data

### Current Gaps
- No FAQs about skincare routines, ingredient interactions, product usage tips
- No company/brand documents (ingredient philosophy, sourcing, certifications)
- No fashion/beauty blog content (seasonal recommendations, trend analysis)
- User profiles are shallow (goals + skin_type, no tried products or ingredient reactions)

### Data to Generate
1. **30-50 FAQs** covering: skincare routines, ingredient combos (what to mix/avoid), product usage timing, common concerns (acne, aging, sensitivity), supplement stacking
2. **10-15 brand/ingredient deep-dives** as documents: "The science of hyaluronic acid", "Why vitamin C and niacinamide work together", "Retinol: beginner's guide"
3. **5-10 demo users with rich histories**:
   - tried_products with likes/dislikes and reasons
   - ingredient_reactions (allergies, sensitivities)
   - detailed preferences (price range, texture, scent, complexity)
   - 6+ months of orders showing patterns (repeat purchases, brand exploration)
   - 3-5 distilled chat summaries from "previous conversations"
4. **Product enrichment**: add key_ingredients, usage_instructions, best_for tags to existing products

### Generation Strategy
- Use Haiku agents for bulk generation (cheap + fast)
- Each agent gets product context + user persona to generate realistic data
- Validate: no contradictions, prices match, ingredients are real

---

## 8. Implementation Phases

### Phase 1: Graph Map + Prompt (1-2 hours)
- [ ] Add graph map to system prompt (Option C from section 4)
- [ ] Store traversal patterns in SurrealDB as `graph_map:main`
- [ ] Update `explore_schema` to return graph map when called with no args
- [ ] Add stream-of-thought instructions to system prompt
- **Verify**: agent picks correct starting node and edge on first try >80%

### Phase 2: Rich User Data (2-3 hours, parallelizable)
- [ ] Add schema extensions (tried, allergic_to, preferences, repeat_purchases)
- [ ] Generate rich mock data for 5-10 demo users via Haiku agents
- [ ] Generate 30-50 FAQs + 10-15 ingredient/brand documents
- [ ] Seed all new data into SurrealDB
- **Verify**: `cat /users/emma_chen` returns rich profile with tried products, allergies, preferences

### Phase 3: Dynamic Graph Reasoning (2-3 hours)
- [ ] Implement multi-hop graph_traverse (chained edges)
- [ ] Update system prompt with compound search strategy
- [ ] Add ingredient compatibility checking to recommendation flow
- [ ] Add negative filtering (exclude products with user's allergen ingredients)
- **Verify**: stress test shows agent traversing 2-3 hops and citing 3+ graph nodes

### Phase 4: Streaming + Visible Reasoning (1-2 hours)
- [ ] Add SSE streaming to /chat endpoint
- [ ] Emit reasoning steps between tool calls via callback handler
- [ ] Frontend renders thinking bubbles with tool trace cards
- **Verify**: demo shows visible reasoning stream in real-time

### Phase 5: Web-Augmented Search (1 hour)
- [ ] Enhance web_search to be a first-class signal (not just fallback)
- [ ] Add domain-scoped search for lookfantastic.com
- [ ] Combine SurrealDB product data with web review/price data
- **Verify**: queries about trends/new products include web results naturally

### Phase 6: Auto Self-Improvement (1 hour)
- [ ] Wire up learned_pattern + failure_record logging
- [ ] Auto-distill after 3+ turn conversations
- [ ] Update tried_products when user mentions products they've used
- **Verify**: user context grows after conversation, subsequent queries are more personalized

---

## 9. Demo Script (The "Wow" Moment)

### Setup
- Pre-seeded user: Emma Chen, combination skin, 6 months of order history
- She's tried 12 products, has 2 ingredient sensitivities (retinol irritation, fragrance headaches)
- Recent breakout pattern in her last 3 orders

### Demo Flow
1. **"Hi, I've been breaking out lately. Help?"**
   - Agent loads Emma's profile, sees her history
   - Traverses: orders → products → ingredients → cross-references with her known sensitivities
   - Discovers: her recent AHA/BHA purchase + retinol sensitivity = likely cause
   - Recommends: gentler alternatives, specifically products she hasn't tried with compatible ingredients
   - Checks web for latest reviews on the alternatives

2. **"What about something with niacinamide? I loved The Ordinary one"**
   - Agent sees she rated Niacinamide 5 stars in tried_products
   - Traverses: niacinamide → contains_ingredient → other products with niacinamide
   - Filters out anything with retinol or fragrance (her sensitivities)
   - Finds 3 options, checks also_bought for social proof
   - Distills: "Emma prefers niacinamide-based products, avoid retinol"

3. **"Actually, can you find me something from a brand I haven't tried?"**
   - Agent checks her order history for all brands she's used
   - Excludes those brands from search
   - Searches for niacinamide products from new brands
   - Web search fills gaps if SurrealDB doesn't have enough options
   - Reasoning visible: "You've used The Ordinary, CeraVe, and La Roche-Posay. Let me find niacinamide products from other brands..."

### What Makes It Impressive
- The agent *thinks through* the graph, not just queries it
- It *remembers* what the user has tried and what worked/didn't
- It *avoids* known problem ingredients automatically
- It *combines* internal data with live web results
- It *learns* from the conversation and updates the user's profile
- All of this is *visible* — the audience watches the reasoning unfold in real-time
