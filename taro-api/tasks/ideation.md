# Ideation: Dataset & Schema for THG-Style Agentic Chatbot

## The Vision

Build a **SurrealDB agentic search harness** (inspired by surrealfs) where a LangGraph agent navigates a rich product knowledge graph across **beauty, fitness, and health** — diagnosing user needs, resolving ingredient conflicts, building personalised routines, and evolving memory over conversations.

The key insight: **THG's ecosystem is goal-oriented** — users don't just browse products, they pursue outcomes (build muscle, clear skin, sleep better). This creates natural multi-hop graph paths that showcase SurrealDB's multi-model strengths far beyond what a simple product catalog can.

---

## Current State vs Target

| Metric | Current (MVP) | Target (Demo) |
|--------|--------------|---------------|
| Products | 5 (Myprotein only) | 40-50 (Myprotein + LOOKFANTASTIC + Myvitamins) |
| Entity types | 3 (product, category, documents) | 10+ (+ ingredient, benefit, goal, brand, routine, user_profile, review) |
| Relations | 10 edges, 3 types | 200+ edges, 15+ types |
| Search modalities | 3 (vector, BM25, hybrid) | 3 + graph-augmented RAG |
| Personalisation | None (MemorySaver only) | User profiles, goal tracking, preference learning |
| SurrealDB features used | ~5 | ~15+ |

---

## Schema Topology: The Knowledge Graph

### Entity Nodes

```
product          Products across all brands
ingredient       Active ingredients (creatine, retinol, hyaluronic acid...)
benefit          What ingredients provide (muscle recovery, hydration, anti-aging...)
goal             User-level objectives (build muscle, clear skin, better sleep...)
category         Product taxonomy (3-level hierarchy)
brand            THG brands (Myprotein, LOOKFANTASTIC, Myvitamins, Myvegan)
routine          Named product sequences (Morning Skincare, Post-Workout Stack)
user_profile     Chatbot users with preferences, skin type, fitness level
review           User reviews (enables computed avg ratings)
documents        Unified searchable content (vector + BM25 indexed)
```

### Edge Relations (The Secret Sauce)

```
-- Product Knowledge Graph
contains_ingredient    product → ingredient      { dosage, unit, per_serving }
belongs_to             product → category        { primary: bool }
made_by                product → brand           {}

-- Ingredient Intelligence
provides_benefit       ingredient → benefit      { evidence_level, mechanism }
achieves_goal          benefit → goal            { strength: 1-5 }
compatible_with        ingredient ↔ ingredient   { synergy_type, notes }
conflicts_with         ingredient ↔ ingredient   { severity, reason, workaround }

-- Category Hierarchy
child_of               category → category       {}

-- Routines
includes_product       routine → product         { step_order, time_of_day, dosage_notes }
targets_goal           routine → goal            {}

-- User Context Evolution
has_goal               user → goal               { priority, start_date, status }
follows_routine        user → routine            { adherence_pct, started_at }
purchased              user → product            { date, quantity, rating }
reviewed               user → product            { rating, text, date }
viewed                 user → product            { timestamp }

-- Cross-Domain Magic
pairs_well_with        product ↔ product         { context, reason, domain_bridge: bool }
```

### The Multi-Hop Chains (Demo Killers)

```
Goal → Benefit → Ingredient → Product
"I want to build muscle" → muscle_growth → creatine → Creatine Monohydrate Powder

User → Goal → Benefit → Ingredient → conflicts_with → Ingredient → Product
"What should I avoid?" → clear_skin → exfoliation → glycolic_acid ✗ retinol → Retinol Serum

User → purchased → Product → contains_ingredient → Ingredient → compatible_with → Ingredient → Product
"What goes well with what I already use?"
```

---

## SurrealDB Feature Showcase Map

### Tier 1: Must Demo (Core Differentiators)

| Feature | Where | Demo Query |
|---------|-------|------------|
| **HNSW Vector Search** | `documents.embedding` | "something for post-workout recovery" |
| **BM25 Full-Text** | `documents.content/title` | "Impact Whey Isolate chocolate" |
| **Hybrid RRF** | Combined vector + BM25 | General product search |
| **Graph Traversal** | 15+ edge types | Goal → Benefit → Ingredient → Product (3 hops) |
| **Recursive Depth** | Category hierarchy | `category:protein.{1..3}<-child_of<-category` |
| **Shortest Path** | Product-to-product | "How is Impact Whey related to Retinol Serum?" |

### Tier 2: Should Demo (Powerful Differentiators)

| Feature | Where | Demo Query |
|---------|-------|------------|
| **Computed Fields (VALUE)** | `product.avg_rating`, `updated_at` | Auto-recomputed on review |
| **ASSERT Validation** | `review.rating ASSERT $value >= 1 AND $value <= 5` | Data integrity |
| **DEFINE EVENT** | On `purchased` → auto-learn preferences | "Based on your purchases, try creatine" |
| **Pre-Computed Views** | `popular_products AS SELECT...GROUP BY` | Real-time leaderboard |
| **Record Links** | `product.brand TYPE record<brand>` | No JOINs needed |
| **Changefeeds** | `CHANGEFEED 7d` on product, user_profile | Audit trail |

### Tier 3: Nice-to-Have

| Feature | Where | Demo Query |
|---------|-------|------------|
| **Live Queries** | Cart recommendations | Real-time WebSocket updates |
| **Access Controls** | User can only see own profile | Row-level security |
| **Geometry** | Store locations | "Nearest store with stock" |
| **Duration type** | Supplement timing | "Take creatine 30min post-workout" |

---

## Dataset: THG Ecosystem

### Domain A: Myprotein (Sports Nutrition) — 25 products

**Categories**: Protein (Whey, Isolate, Casein, Vegan, Clear), Creatine, Pre-Workout, Amino Acids, Vitamins, Snacks

**Sample Products**:
- Impact Whey Protein (£18.99) — 5 flavours, 21g protein
- Impact Whey Isolate (£24.99) — 4 flavours, 23g protein, <1g fat
- Clear Whey Isolate (£24.99) — juice-like, refreshing
- Creatine Monohydrate (£9.99) — clinically proven, 3g/serving
- THE Pre-Workout (£29.99) — 175mg caffeine, citrulline, beta-alanine
- Essential BCAA 2:1:1 (£14.99) — leucine, isoleucine, valine
- Layered Protein Bar (£2.99) — 20g protein, 6 layers
- Alpha Men Multivitamin (£8.99) — A-Z vitamins, zinc, magnesium
- Vegan Protein Blend (£19.99) — pea + fava bean
- Collagen Peptides (£16.99) — Type I & III, skin + joints

### Domain B: LOOKFANTASTIC (Beauty & Skincare) — 15 products

**Categories**: Cleansers, Serums, Moisturizers, SPF, Masks, Hair Care

**Sample Products**:
- The Ordinary Retinol 0.5% (£5.80) — anti-aging, PM only
- The Ordinary Niacinamide 10% + Zinc 1% (£5.90) — pore control
- The Ordinary Hyaluronic Acid 2% + B5 (£6.80) — hydration
- CeraVe Hydrating Cleanser (£11.50) — ceramides, gentle
- La Roche-Posay Anthelios SPF50 (£17.50) — UVA/UVB protection
- Paula's Choice 2% BHA Liquid Exfoliant (£29.00) — salicylic acid
- COSRX Snail Mucin Essence (£21.00) — repair, hydration
- Olaplex No.3 Hair Perfector (£28.00) — bond repair
- The Ordinary AHA 30% + BHA 2% Peeling Solution (£6.80) — exfoliation
- Drunk Elephant Protini Polypeptide Cream (£62.00) — peptides, amino acids

### Domain C: Cross-Domain / Myvitamins — 10 products

**Sample Products**:
- Omega-3 Fish Oil (£7.99) — skin + brain + joints
- Vitamin D3 (£4.99) — immunity + mood
- Collagen Powder (£16.99) — skin elasticity + joint health (BRIDGE product)
- Biotin (£5.99) — hair + nail growth
- Magnesium Citrate (£6.99) — sleep + muscle recovery (BRIDGE product)
- Ashwagandha KSM-66 (£9.99) — stress + cortisol
- Turmeric & Black Pepper (£7.99) — inflammation + recovery

### Key Ingredients to Model (25-30)

**Fitness**: Whey Protein, Creatine Monohydrate, Caffeine, Beta-Alanine, L-Citrulline, BCAAs (Leucine, Isoleucine, Valine), L-Glutamine, Electrolytes

**Beauty**: Retinol, Hyaluronic Acid, Niacinamide, Vitamin C (L-Ascorbic Acid), Glycolic Acid (AHA), Salicylic Acid (BHA), Ceramides, Peptides, Squalane, Snail Mucin

**Bridge**: Collagen, Omega-3, Vitamin D3, Zinc, Magnesium, Biotin

### Ingredient Compatibility Graph (HIGH DEMO VALUE)

**Compatible Pairs** (synergy):
- Retinol + Hyaluronic Acid → "HA buffers retinol dryness"
- Retinol + Niacinamide → "Niacinamide reduces retinol irritation"
- Vitamin C + Vitamin E → "Antioxidant synergy (+ Ferulic Acid = CE Ferulic)"
- Creatine + Whey Protein → "Both post-workout, complementary mechanisms"
- Caffeine + L-Citrulline → "Energy + pump synergy"
- Collagen + Vitamin C → "Vitamin C required for collagen synthesis"

**Conflict Pairs** (avoid):
- Retinol + AHA (Glycolic Acid) → severity: HIGH, "Over-exfoliation, barrier damage"
- Retinol + Vitamin C → severity: MEDIUM, "pH incompatibility, use AM/PM split"
- Vitamin C + BHA (Salicylic Acid) → severity: MEDIUM, "Oxidation risk"
- AHA + BHA → severity: HIGH, "Double exfoliation, irritation"
- ZMA + Calcium → severity: MEDIUM, "Calcium blocks zinc absorption"
- Iron + Calcium → severity: HIGH, "Competitive absorption"
- Caffeine + Creatine (high dose) → severity: LOW, "May reduce absorption slightly"

### Goals (8-10)

1. **Build Muscle** — protein, creatine, BCAAs
2. **Lose Weight** — protein (satiety), CLA, green tea extract
3. **Clear Skin** — niacinamide, BHA, retinol, hydration
4. **Anti-Aging** — retinol, vitamin C, collagen, peptides
5. **Better Sleep** — magnesium, ZMA, ashwagandha
6. **More Energy** — pre-workout, caffeine, vitamin D, B vitamins
7. **Hair Growth** — biotin, collagen, omega-3
8. **Post-Workout Recovery** — whey protein, creatine, magnesium, BCAAs
9. **Healthy Skin (Inside Out)** — omega-3 + collagen (supplements) + HA + SPF (topical)
10. **Competition Prep** — whey isolate + creatine + pre-workout + multivitamin

### Pre-Built Routines (5-8)

1. **Morning Skincare** — Cleanser → Vitamin C Serum → Moisturizer → SPF
2. **Evening Skincare** — Cleanser → BHA → Retinol → Moisturizer
3. **Post-Workout Stack** — Whey Protein → Creatine → BCAAs (within 30min)
4. **Beginner Supplement Stack** — Whey Protein + Multivitamin + Creatine
5. **Sleep & Recovery** — Magnesium (evening) → ZMA (before bed) → Night Cream
6. **Skin Health Inside Out** — Collagen + Omega-3 (AM) → HA Serum + SPF (topical AM) → Retinol (PM)
7. **Competition Prep** — Whey Isolate + Creatine + Pre-Workout + Multivitamin + Electrolytes

### User Personas for Demo (4)

1. **Alex** (Gym Bro) — goal: build muscle, budget-conscious, no restrictions, intermediate
2. **Priya** (Skincare Enthusiast) — goal: clear skin + anti-aging, combination skin, uses retinol already
3. **Sam** (Wellness Seeker) — goals: better sleep + energy, vegan, cross-domain buyer
4. **Jordan** (Competition Prep) — goal: stage-ready, advanced, needs full routine planning

---

## Memory & Personalisation: Context Evolution

### How It Works

```
Conversation 1: "I want to build muscle"
  → Agent creates: RELATE user:alex -> has_goal -> goal:build_muscle
  → Agent recommends: Whey Protein, Creatine (via 3-hop graph traversal)

Conversation 2: "I'm also getting into skincare"
  → Agent creates: RELATE user:alex -> has_goal -> goal:clear_skin
  → Agent checks conflicts: Creatine doesn't conflict with any skincare ingredients ✓
  → Agent recommends: CeraVe Cleanser + Niacinamide Serum
  → Agent suggests BRIDGE: "Collagen Peptides help both muscle recovery AND skin elasticity"

Conversation 3: "What should my daily routine look like?"
  → Agent traverses ALL goals + existing purchases
  → Builds personalised routine avoiding conflicts
  → Returns ordered, timed schedule with cross-domain products
```

### SurrealDB Features Enabling This

1. **Graph Relations** — User → Goal → Benefit → Ingredient → Product chain
2. **Conflict Detection** — `conflicts_with` edges prevent bad recommendations
3. **Events** — Auto-learn preferences on purchase/view
4. **Computed Views** — `user_goal_summary` auto-updates
5. **Changefeeds** — Track preference evolution over time
6. **Conversation as Graph** — Messages linked to products/ingredients they mention

---

## Harness Architecture (Inspired by surrealfs)

### Pattern: Tool Factory with File-Based Docs

Like surrealfs's `build_toolset()` + `tool_docs/` pattern:

```
src/tools/
  __init__.py          # build_toolset() factory
  hybrid_search.py     # Tool implementation
  ...
src/tool_docs/
  hybrid_search.md     # Swappable tool description
  graph_traverse.md    # Swappable tool description
  conflict_check.md    # NEW: ingredient conflict checker
  routine_builder.md   # NEW: personalised routine builder
  user_memory.md       # NEW: read/write user preferences
```

### New Tools to Add

| Tool | Purpose | SurrealDB Feature |
|------|---------|-------------------|
| `conflict_check` | Check ingredient compatibility | Graph traversal (conflicts_with edges) |
| `routine_builder` | Build personalised product routines | Multi-hop traversal + user profile |
| `goal_navigator` | Traverse goal → benefit → ingredient → product | Recursive graph (3+ hops) |
| `user_memory` | Read/write user profile, goals, preferences | CRUD + events |
| `collaborative_filter` | "Users who bought X also bought Y" | Graph pattern matching |
| `product_compare` | Side-by-side comparison (ingredients, benefits) | Multi-record fetch + diff |

---

## Decisions

1. **Domain**: THG ecosystem (Myprotein + LOOKFANTASTIC + Myvitamins) — goal-oriented, natural graph relationships, cross-domain bridges
2. **Scale**: ~50 products, ~30 ingredients, ~15 benefits, ~10 goals, 200+ relations
3. **Key differentiator**: Ingredient compatibility/conflict graph — this is the "wow" moment
4. **Personalisation**: User profiles + goal tracking + preference events stored in SurrealDB
5. **Harness pattern**: Adapt surrealfs tool factory + file-based docs approach
6. **New tools**: conflict_check, routine_builder, goal_navigator, user_memory, collaborative_filter, product_compare
