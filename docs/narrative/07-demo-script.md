# 5-Minute Live Demo Script

> Taro.ai — SurrealFS: A filesystem metaphor for agentic search over SurrealDB's multi-model engine.

---

**TL;DR**

- SurrealFS maps 9 bash commands (`ls`, `cat`, `find`, `grep`, `tree`, `graph_traverse`, `surrealql_query`, `web_search`, `explore_schema`) to SurrealDB's vector, BM25, graph, and relational engines through a single database backend.
- A ReAct agent with a GATHER-ACT-VERIFY constraint loop achieves 95.3% accuracy on a 43-query adversarial stress test — up from 51.1% before the filesystem metaphor.
- One SurrealDB instance stores 1,890 products, 2,526 customers, 6,862 orders, 3,247 reviews, 12 graph edge types, and all agent checkpoints. No secondary databases.

---

## Act 1: The Opening (30 seconds)

**Speaker notes:** Start with the WhatsApp screenshot. This grounds the demo in a real moment, not a pitch deck.

> "Friday night, 11pm, WhatsApp group chat. Five strangers at a hackathon. Someone says: what if we replicated the filesystem structure that coding agents have — but over a database? What if `ls`, `cat`, `find`, `grep` were the interface to your entire data layer? That idea became SurrealFS. Let me show you what it does."

**Visual:** WhatsApp screenshot showing Jordan's 23:12 message and Desmond's "thats quite good" reply. Fade to the Taro.ai chat interface.

---

## Act 2: The Problem (30 seconds)

**Speaker notes:** Do not explain search theory. Show it breaking. Three quick queries, three different failures.

> "E-commerce search has a three-body problem. Watch."

| Query | Search mode | What happens |
|-------|------------|--------------|
| "retinol serum under 30 pounds" | Vector only | Returns retinol blog posts and 50-pound products. Understands the concept, ignores the constraints. |
| "moisturizer for dry skin in winter" | Keyword only | Returns nothing. No product description contains those exact words. |
| "What do customers who bought this also buy?" | Either | Neither mode can traverse relationships. You need a graph. |

> "Each mode solves part of the problem. None solves the whole thing. So we put all three — vector, keyword, graph — into one database, and gave the agent a filesystem to navigate them."

**Visual:** Three-panel split showing each query failing in isolation. Brief, no more than 10 seconds per panel.

---

## Act 3: SurrealFS Live (2 minutes)

**Speaker notes:** This is the core of the demo. Four interactions that show the full tool spectrum. Let the tool trace cards do the talking — the audience should see the agent reasoning in real time.

### 3a. Semantic search + product cards (30s)

Type: **"Best moisturizers for sensitive skin under 30 pounds"**

> "Watch the tool trace. The agent calls `find` — that is hybrid vector plus BM25 search with reciprocal rank fusion. It gets candidates from both search modes, merges them, then calls `cat` on each result to verify details before responding. GATHER, ACT, VERIFY — three phases, every time."

**Visual:** Chat response streaming token by token. Tool trace cards appear with live spinners, then show completion durations. Product cards render inline with images, prices, and ratings.

### 3b. Copilot mode + preference actions (30s)

Click the expand button to open copilot mode.

> "Copilot mode — side-by-side browsing and chat. Now watch the product cards. Each one has three actions: Cart, Keep, Remove."

Click **Cart** on one product. Click **Remove** on another.

> "Those actions write graph edges directly into SurrealDB. Cart creates a `wants` edge, Keep creates `interested_in`, Remove creates `rejected`. The agent sees these preferences on the next query. This is not a session variable — it is a persisted graph relationship."

**Visual:** 50/50 split view. The preference buttons animating on click. Briefly show the SurrealDB edge being created (optional, can save for Act 4).

### 3c. Graph traversal (30s)

Type: **"What do customers who bought LANEIGE Water Bank also buy?"**

> "Now the agent calls `graph_traverse`. It walks the `also_bought` edges — derived from co-purchase patterns across 6,862 orders. This is not collaborative filtering running in Python. These are pre-computed graph edges stored natively in SurrealDB, traversed in one query."

**Visual:** Tool trace showing `graph_traverse` with edge type and direction. Results showing related products with co-purchase weights.

### 3d. Multi-tool chain (30s)

Type: **"I have dry skin and I am looking for a routine. What categories do you have, and find me a cleanser, moisturizer, and serum?"**

> "This query requires three tool types. `tree` to show the category hierarchy. `find` to search across product types. `cat` to verify each recommendation. The agent chains them because the tools have familiar names — it already knows that `tree` shows structure and `find` searches content. That is the entire insight behind SurrealFS: borrow the LLM's existing priors instead of teaching it a new taxonomy."

**Visual:** Tool trace showing 4-5 tool calls in sequence. The streaming response building a structured routine recommendation.

---

## Act 4: Under the Hood (1 minute)

**Speaker notes:** Switch to SurrealDB Studio. Keep it fast — three views, ten seconds each.

Open SurrealDB Studio at `localhost:8000`.

> "One database. Everything you just saw lives here."

**View 1 — Documents table:** "Vector embeddings — 1,536 dimensions, HNSW indexed, cosine similarity. This is what `find` queries."

**View 2 — Graph edges:** "Twelve edge types. `placed`, `contains`, `has_review`, `belongs_to`, `child_of`, `also_bought`, `supports_goal`, `contains_ingredient`, `related_to`, `wants`, `interested_in`, `rejected`. All native SurrealDB `RELATE` statements."

**View 3 — Product table:** "Structured relational data. The same product exists in both the `documents` table for search and the `product` table for graph edges, linked by `source_id`. One schema, no synchronization layer."

> "No Pinecone. No Elasticsearch. No Neo4j. One SurrealDB instance running all three search modalities plus relational storage plus agent checkpointing."

**Visual:** SurrealDB Studio with each table briefly visible. The graph edge visualization if Studio supports it.

---

## Act 5: The Journey (30 seconds)

**Speaker notes:** This is the credibility slide. Numbers, not adjectives.

> "We started Friday night with 13 overlapping tools and a 51.1% pass rate on adversarial queries. The LLM could not tell `hybrid_search` from `semantic_search` from `keyword_search`. We consolidated to 9 tools using the filesystem metaphor, added the GATHER-ACT-VERIFY constraint loop, and hit 95.3% on a 43-query stress test."

| Metric | Value |
|--------|-------|
| SurrealFS tools | 9 (ls, cat, find, grep, tree, graph\_traverse, surrealql\_query, web\_search, explore\_schema) |
| Graph edge types | 12 |
| Products | 1,890 (431 unique scraped from lookfantastic.com) |
| Customers | 2,526 |
| Orders | 6,862 |
| Reviews | 3,247 |
| API endpoints | 20 (REST + SSE streaming) |
| Unit tests | 91 |
| Stress test (43 adversarial queries) | 95.3% pass rate |
| LLM support | Model-agnostic (OpenAI, Anthropic, Google) |
| SurrealDB 3.0 bugs found and worked around | 5 |

> "We also found and documented five SurrealDB 3.0 compatibility issues — broken KNN operators, changed result formats, silent BM25 failures, RecordID type changes, and missing table auto-creation in the checkpointer. All worked around, all reported."

**Visual:** A single slide or terminal screenshot with the metrics table. Optionally show the stress test output scrolling.

---

## Act 6: Close (30 seconds)

**Speaker notes:** End on the transferable pattern, not the product.

> "SurrealFS is not an e-commerce product. It is a pattern. Any domain with structured data can use the same approach: map bash commands to your data operations, give the LLM tools it already understands, and enforce a constraint loop so it verifies before it answers."

> "A legal research agent with `find` over case law embeddings and `graph_traverse` over citation networks. A medical agent with `grep` over drug interactions and `tree` over diagnostic hierarchies. A DevOps agent with `ls` over infrastructure state and `cat` over service configurations. The filesystem metaphor works because LLMs already know the filesystem."

> "SurrealDB made this possible by putting vector, graph, keyword, and relational data in one engine. We just gave the agent a familiar way to talk to it. Thank you."

**Visual:** The SurrealFS tool table from Act 5, with the bottom line: "One database. Nine tools. The filesystem your agent already knows."

---

## Presenter Checklist

- [ ] SurrealDB running on port 8000 with seeded data (`make seed`)
- [ ] FastAPI running on port 8003 (`make serve`)
- [ ] Frontend running on port 3001
- [ ] SurrealDB Studio open in a browser tab
- [ ] WhatsApp screenshot ready (crop to 23:10-23:14 messages)
- [ ] Copilot mode collapsed at start (so you can expand it live)
- [ ] Test all four demo queries before going on stage
- [ ] Have a backup: if streaming breaks, the frontend falls back to blocking mode automatically
