# Slide Brief: AI-Ready Format for PowerPoint Generation

> **Taro.ai** -- LangChain x SurrealDB Hackathon, London, March 6-8 2026

---

> **TL;DR**
>
> - 16 structured slides for a 5-minute presentation covering the SurrealFS story arc: origin, architecture, live demo, results, and reusable pattern.
> - Each slide block contains title, subtitle, visual specification, bullets, speaker notes, and duration -- machine-readable for `python-pptx` or Google Slides API generation.
> - Total duration: 300 seconds (5 minutes). Demo slot is 120 seconds. Non-demo slides average 12 seconds each.
> - Key numbers: 9 tools, 12 edge types, 1,890 products, 95.3% stress test pass rate, 51.1% to 95.3% improvement arc across 4 rounds.

---

## Slide 1: Title

**Subtitle:** SurrealFS -- A Filesystem Metaphor for Agentic Search

**Visual:** Taro.ai logo centered. Team name "Taro.ai" large. Subtitle below. Hackathon branding (LangChain x SurrealDB) in bottom-left corner. Date "London, March 6-8 2026" in bottom-right.

**Bullets:**
- Taro.ai -- LangChain x SurrealDB Hackathon
- SurrealFS: 9 bash commands over a multi-model database
- One SurrealDB instance. Vector + BM25 + Graph + Relational.
- Team: Jordan, Desmond, Charlotte, Shashwat, B

**Speaker Notes:** "We are Taro.ai. Over the past 48 hours, we built SurrealFS -- a filesystem metaphor that gives LLM agents pre-trained intuition for navigating a SurrealDB database. Nine tools named after bash commands, one database backend for everything. Let me tell you how it started."

**Duration:** 15 seconds

---

## Slide 2: The WhatsApp Moment

**Subtitle:** Friday night, 11pm -- the idea that changed everything

**Visual:** Cropped WhatsApp screenshot showing Jordan's 23:10 message ("I think about what the guy said about replicating the filesystem structure that coding agents have in surrealdb"), Jordan's 23:12 follow-up ("We could define a verbose enough tool set for agents to perform agentic search across the db"), and Desmond's 23:13 reply ("thats quite good"). Timestamps visible.

**Bullets:**
- 9pm Friday: venue closing, team scatters to WhatsApp
- 23:10: "What if we replicated the filesystem structure that coding agents have -- but over a database?"
- 23:13: Desmond (SurrealDB): "thats quite good"
- Architecture decided at 23:14 over WhatsApp
- Name: Jordan suggested "a random fruit or vegetable" -- Desmond said "Taro"

**Speaker Notes:** "Friday night, 11pm. Five strangers in a WhatsApp group. Someone says: what if ls, cat, find, grep were the interface to your database? Desmond from SurrealDB replies with two words: 'thats quite good.' Forty-eight hours later, we shipped it."

**Duration:** 20 seconds

---

## Slide 3: The Problem

**Subtitle:** E-commerce search has a three-body problem

**Visual:** Three-column layout. Left column: "Keyword (BM25)" with a red X on "moisturizer for dry skin in winter" returning zero results. Center column: "Vector (HNSW)" with an orange warning on "retinol serum under 30 pounds" returning irrelevant 50-pound products. Right column: "Graph" with a red X on "what do customers who bought this also buy?" with text "Cannot search -- only navigates."

**Bullets:**
- Keyword search (BM25): precise but brittle -- "dry skin in winter" returns nothing
- Vector search (HNSW): captures intent but ignores constraints -- returns 50-pound products for "under 30 pounds"
- Graph traversal: answers relationship queries but cannot search -- needs a known starting node
- Industry answer: pick one, add heuristics, accept the gaps
- SurrealDB answer: all three in one engine -- but the interface is the problem

**Speaker Notes:** "Each search mode solves part of the problem and fails at the rest. Keyword search is precise but brittle. Vector search captures intent but ignores specifics. Graph traversal answers relationship questions but cannot search. The standard answer is to run three separate databases and build a fragile orchestration layer. SurrealDB puts all three in one engine. Our challenge was the interface."

**Duration:** 20 seconds

---

## Slide 4: The Bet

**Subtitle:** What if ls, cat, find, grep were your database interface?

**Visual:** Split layout. Left side: "Before" -- a cluttered list of 13 tools with novel names (`hybrid_search`, `semantic_search`, `keyword_search`, `get_record`, `list_records`, `browse_hierarchy`...) with a red "44% tool selection" badge. Right side: "After" -- a clean list of 9 tools with bash names (`ls`, `cat`, `find`, `grep`, `tree`, `graph_traverse`, `explore_schema`, `surrealql_query`, `web_search`) with a green "100% tool selection" badge.

**Bullets:**
- LLMs already know bash commands from billions of tokens of training data
- Name your database tools after commands the model understands -- zero-shot selection
- 13 tools with novel names: 44% tool selection accuracy
- 9 tools with bash names: 100% tool selection accuracy
- Same model, same queries, same database operations -- only the names changed

**Speaker Notes:** "The bet was simple: name your database tools after bash commands. LLMs have seen millions of examples of find, grep, cat in their training data. They already know when to use each one. We tested this directly -- 44% accuracy with novel tool names, 100% with bash names. No model change, no prompt change. Pure context engineering."

**Duration:** 15 seconds

---

## Slide 5: System Architecture

**Subtitle:** FastAPI + LangGraph + SurrealDB -- the full stack

**Visual:** Architecture diagram (from 02-architecture.md). Top: "Browser / API Client" with an arrow down to "FastAPI (20 endpoints, SSE streaming)." Below that: "LangGraph StateGraph" containing "ReAct SubGraph (create_react_agent)" and "Judge Node (evaluate_turn)." Nine tool boxes fanning out below: ls, cat, find, grep, tree, graph_traverse, explore_schema, surrealql_query, web_search. All arrows converge into a single "SurrealDB" box at the bottom labeled "7 roles."

**Bullets:**
- FastAPI: 20 endpoints with SSE streaming for real-time token + tool trace
- LangGraph: ReAct agent with create_react_agent + post-agent Judge node
- 9 SurrealFS tools: all async, all routed to one SurrealDB instance
- Model-agnostic: OpenAI, Anthropic, Google via get_llm() registry
- Judge is observational only -- scores tool selection, never blocks responses

**Speaker Notes:** "The stack is FastAPI on top for 20 REST endpoints with server-sent event streaming. LangGraph in the middle running a ReAct agent with 9 tools bound. A judge node runs after the agent to score tool selection quality. Everything hits one SurrealDB instance at the bottom -- no secondary databases."

**Duration:** 15 seconds

---

## Slide 6: SurrealFS Tools

**Subtitle:** 9 tools, 3 phases, 1 filesystem metaphor

**Visual:** Table with columns: Tool, Bash Analog, Phase, Database Operation. Rows for all 9 tools. Phase column color-coded: GATHER tools in blue, ACT tools in orange, GATHER/VERIFY tools in green.

| Tool | Bash Analog | Phase | DB Operation |
|------|-------------|-------|--------------|
| `ls` | `ls /path` | GATHER | SELECT on routed table (13 path patterns) |
| `cat` | `cat /path` | GATHER/VERIFY | Same routes, verbose=True for full fields |
| `tree` | `tree /path` | GATHER | Recursive SELECT with edge expansion |
| `explore_schema` | `SHOW TABLES` | GATHER | INFO FOR DB / INFO FOR TABLE |
| `find` | `find . -name` | ACT | Hybrid RRF: cosine vector + BM25 keyword |
| `grep` | `grep term` | ACT | BM25 keyword with CONTAINS fallback |
| `graph_traverse` | symlink following | ACT | Walk RELATE edges (5 named patterns) |
| `surrealql_query` | `sql` client | ACT | Raw read-only SurrealQL |
| `web_search` | `curl` | ACT | Tavily API (domain-scoped, cached) |

**Bullets:**
- GATHER tools: orient in the data graph before searching
- ACT tools: execute informed queries with the right modality
- VERIFY: `cat` does double duty -- GATHER for exploration, VERIFY for confirmation
- `find` uses client-side RRF fusion (two queries, merged by reciprocal rank)
- `ls` and `cat` share the same 13-pattern path router -- one boolean toggles verbosity

**Speaker Notes:** "Nine tools in three phases. GATHER tools orient the agent in the data graph. ACT tools execute the actual search. VERIFY means re-reading records with cat before recommending them. The agent cannot answer until it has evidence. The filesystem metaphor makes the right tool obvious without fine-tuning."

**Duration:** 15 seconds

---

## Slide 7: The Harness

**Subtitle:** GATHER -> ACT -> VERIFY -- constrain outputs, not process

**Visual:** Horizontal flow diagram with three large boxes connected by arrows. Box 1 (blue): "GATHER -- Orient" with icons for ls, cat, tree, explore_schema. Box 2 (orange): "ACT -- Execute" with icons for find, grep, graph_traverse, surrealql_query, web_search. Box 3 (green): "VERIFY -- Confirm" with icon for cat. A curved arrow from VERIFY back to GATHER labeled "iterate if needed." Below the flow: a quote: "You MUST use tools. NEVER answer from your own knowledge."

**Bullets:**
- GATHER: understand data landscape before searching (ls, tree, explore_schema)
- ACT: targeted queries with context -- semantic, keyword, graph, or raw SQL
- VERIFY: cat every product before recommending it -- catches hallucinations
- Inspired by Codex and Claude Code research on agent harness design
- System prompt + worked examples + stress tests enforce the loop

**Speaker Notes:** "The harness is a constraint loop: GATHER, ACT, VERIFY. The agent must orient itself in the data before searching, and must verify its recommendations before responding. This is not three separate prompts -- it is an architectural constraint encoded in the system prompt, the tool docstrings, and the stress tests. Constrain outputs, not process."

**Duration:** 15 seconds

---

## Slide 8: LIVE DEMO

**Subtitle:** SurrealFS in action -- 4 interactions, 2 minutes

**Visual:** Placeholder slide with large centered text: "LIVE DEMO". Below: four bullet points previewing the demo queries. Background: a subtle screenshot of the Taro.ai chat interface.

**Bullets:**
- Semantic search: "Best moisturizers for sensitive skin under 30 pounds"
- Copilot mode + preference actions: Cart / Keep / Remove writing graph edges
- Graph traversal: "What do customers who bought LANEIGE Water Bank also buy?"
- Multi-tool chain: "Find me a skincare routine" (tree + find + cat)

**Speaker Notes:** [Live demo -- refer to 07-demo-script.md Acts 2-4 for full script. Key points: let the tool trace cards do the talking, show copilot mode side-by-side, demonstrate graph traversal with also_bought edges, end with a multi-tool chain showing GATHER-ACT-VERIFY in action.]

**Duration:** 120 seconds

---

## Slide 9: Graph Schema

**Subtitle:** 12 edge types -- commerce, taxonomy, domain knowledge, live preferences

**Visual:** Network graph visualization. Central cluster of nodes: product (orange), customer (blue), order (gray), category (green), review (yellow), goal (purple), ingredient (pink). Edges drawn between them with labels. Four groupings highlighted: Commerce (placed, contains, has_review), Taxonomy (belongs_to, child_of), Domain Knowledge (also_bought, supports_goal, contains_ingredient, related_to), Live Preferences (wants, interested_in, rejected).

**Bullets:**
- Commerce (3): placed, contains, has_review -- transactional backbone
- Taxonomy (2): belongs_to, child_of -- 3 verticals, 9 subcategories
- Domain Knowledge (4): also_bought, supports_goal, contains_ingredient, related_to
- Live Preferences (3): wants, interested_in, rejected -- created during conversation
- All defined as TYPE RELATION tables with typed IN/OUT constraints

**Speaker Notes:** "Twelve edge types organized into four categories. Commerce edges encode transactions. Taxonomy edges encode the category hierarchy. Domain knowledge edges encode product relationships, ingredients, and beauty goals. And the live preference edges -- wants, interested_in, rejected -- are created during conversation as the user interacts with product cards. The graph evolves while the user is chatting."

**Duration:** 15 seconds

---

## Slide 10: One Database, Seven Roles

**Subtitle:** SurrealDB as vector store, keyword index, graph DB, and more

**Visual:** A single SurrealDB cylinder icon in the center with seven labeled arrows radiating outward to role boxes: (1) Vector Store (HNSW 1536d, cosine), (2) Keyword Index (BM25, snowball stemming), (3) Graph Database (12 edge types, RELATE), (4) Relational Store (7 SCHEMAFULL tables), (5) Checkpoint Backend (SurrealSaver v2.0.0), (6) Conversation Memory (thread persistence), (7) Web Cache (Tavily results, 24h TTL).

**Bullets:**
- Vector Store: HNSW index, 1536d OpenAI embeddings, cosine similarity
- Keyword Index: BM25 with snowball stemming + CONTAINS fallback
- Graph Database: 12 edge types as native RELATE statements
- Relational Store: 7 SCHEMAFULL tables (product, customer, order, review, category, goal, ingredient)
- Also: checkpoint backend, conversation memory, web cache -- one connection string

**Speaker Notes:** "One SurrealDB instance serves seven roles. Vector store for semantic search. Keyword index for BM25. Graph database for relationship traversal. Relational store for structured data. Plus it stores our agent checkpoints, conversation history, and web search cache. No Pinecone, no Elasticsearch, no Neo4j, no Redis. One database, one schema file, one connection string."

**Duration:** 15 seconds

---

## Slide 11: The Improvement Arc

**Subtitle:** 51.1% -> 95.3% across four adversarial stress test rounds

**Visual:** Line chart with X-axis "Round 1, Round 2, Round 3, Round 4" and Y-axis "Pass Rate (%)". Data points: 51.1%, 68.9%, 60.5%, 95.3%. Round 3 dip annotated with "OpenAI rate limits -- not a regression." A callout box at the Round 4 point: "41/43 queries passing." Below the chart: a small table showing the key fix per round.

| Round | Pass Rate | Key Fix |
|-------|-----------|---------|
| 1 (baseline) | 51.1% (23/45) | -- |
| 2 (fixes) | 68.9% (31/45) | Error handling, search workarounds, tool consolidation |
| 3 (rate limited) | 60.5% (26/43) | Trimmed suite to 43, but no pacing -- OpenAI rate limits |
| 4 (final) | 95.3% (41/43) | 2s delay between queries, retry with 5s backoff |

**Bullets:**
- Round 1: 13 tools, no error handling, 44% tool selection -- brutal
- Round 2: tool consolidation 13 -> 9, SurrealDB 3.0 workarounds applied
- Round 3: dip to 60.5% was 15/17 failures from OpenAI rate limits, not logic bugs
- Round 4: 95.3% -- remaining 2 failures: 1 rate limit, 1 false positive test assertion
- Key insight: classify failures by type -- rate limits are not harness defects

**Speaker Notes:** "We ran four rounds of adversarial stress testing. Started at 51.1% -- brutal. Fixed the real bugs, consolidated tools, hit 68.9%. Then round 3 dropped to 60.5%, which scared us -- until we classified the failures and found that 15 of 17 were OpenAI rate limits. Added pacing, hit 95.3%. The lesson: classify failures by type before panicking."

**Duration:** 15 seconds

---

## Slide 12: SurrealDB 3.0 Bugs

**Subtitle:** 5 critical bugs found, all worked around, all reported

**Visual:** Table with two columns: "Bug" and "Workaround". Five rows, each with a short bug description and the fix. Red/yellow severity indicators on the left.

| # | Bug | Workaround |
|---|-----|-----------|
| 1 | KNN `<\|N\|>` returns error strings | `ORDER BY vector::similarity::cosine() DESC LIMIT N` |
| 2 | BM25 `@1@` returns empty results | `CONTAINS` fallback with case-insensitive matching |
| 3 | `db.query()` result format changed | `isinstance` checks for both flat list and wrapped format |
| 4 | RecordID objects instead of strings | Wrap all RecordID access in `str()` |
| 5 | SurrealSaver tables not auto-created | Pre-create `checkpoint` + `write` SCHEMALESS tables in schema |

**Bullets:**
- All 5 bugs are silent failures -- code runs, returns wrong/empty results
- KNN and BM25 bugs broke both vector and keyword search simultaneously
- RecordID bug only found by testing with a weaker model (gpt-4o-mini)
- Cost: ~8 hours of debugging across two days
- Savings: ~12 hours of infrastructure setup avoided by using one database

**Speaker Notes:** "We found five critical SurrealDB 3.0 compatibility issues. All were silent failures -- the code ran without errors but returned wrong or empty results. The KNN operator is broken, BM25 returns empty, the result format changed, RecordIDs are objects not strings, and the checkpointer tables are not auto-created. All fixable with workarounds, and we have documented every one."

**Duration:** 15 seconds

---

## Slide 13: Lessons Learned

**Subtitle:** 13 lessons from the trenches -- three that changed everything

**Visual:** Three large callout boxes arranged horizontally, each with a lesson number, title, and one-line summary. Background: a faded screenshot of the `tasks/lessons.md` file.

| Lesson | Insight |
|--------|---------|
| L4: Filesystem metaphor | Bash names = zero-shot tool selection. 44% -> 100% with no logic changes. |
| L6: Rate limits masquerade | Classify failures by type. 15/17 "failures" in round 3 were rate limits. |
| L11: Weaker models are better fuzzers | gpt-4o-mini found 2 bugs that gpt-4o avoided by being "polite." |

**Bullets:**
- L4: Borrow concepts the model already knows -- do not invent new ones
- L6: Infrastructure failures are not harness failures -- classify before debugging
- L11: Test with at least two model tiers -- weaker models hit more code paths
- Every bug followed: Detect -> Diagnose -> Fix -> Extract lesson -> Persist -> Prevent
- 13 lessons in `tasks/lessons.md` -- read at session start, searched before new work

**Speaker Notes:** "We captured 13 lessons during the hackathon. Three changed everything. L4: naming tools after bash commands gave us zero-shot selection. L6: classifying failures by type prevented us from chasing phantom regressions. L11: testing with a weaker model found bugs the stronger model politely avoided. Every bug became a lesson, every lesson became a prevention rule."

**Duration:** 15 seconds

---

## Slide 14: Results Dashboard

**Subtitle:** The numbers behind 48 hours of building

**Visual:** Dashboard layout with large metric cards arranged in a grid. Each card has a large number and a label beneath it. Key metrics highlighted with color accents.

| Metric | Value |
|--------|-------|
| Stress test pass rate | **95.3%** (41/43 queries) |
| Tool selection accuracy | **100%** (18/18 queries) |
| Unit tests passing | **91** |
| API endpoints | **20** |
| SurrealFS tools | **9** |
| Graph edge types | **12** |
| Products in database | **1,890** (431 unique scraped) |
| Customers | **2,526** |
| Orders | **6,862** |
| Reviews | **3,247** |
| SurrealDB roles | **7** |
| SurrealDB 3.0 bugs found | **5** |

**Bullets:**
- 95.3% on 43 adversarial queries -- up from 51.1% baseline
- 100% tool selection accuracy -- zero additional prompt text required
- 1,890 products across 3 verticals, 9 subcategories
- One database, seven roles, zero secondary infrastructure
- SSE streaming with real-time tool trace cards

**Speaker Notes:** "Here are the final numbers. 95.3% on adversarial stress tests. 100% tool selection accuracy. 91 unit tests. 20 API endpoints. 1,890 products, 2,526 customers, 6,862 orders, 3,247 reviews -- all in a single SurrealDB instance serving seven roles. No secondary databases."

**Duration:** 10 seconds

---

## Slide 15: The Reusable Pattern

**Subtitle:** SurrealFS beyond e-commerce -- healthcare, legal, code, knowledge

**Visual:** Four quadrant layout. Each quadrant has a domain icon, a domain name, and 2-3 example tool mappings. Top-left: Healthcare (find over clinical notes, graph_traverse over prescriptions). Top-right: Legal (find over case law, graph_traverse over citations). Bottom-left: Code (ls over modules, grep over TODO items). Bottom-right: Knowledge Management (find over meeting notes, graph_traverse over decision chains). Center: "SurrealFS Pattern" with three requirements listed: Records with IDs, Searchable content, Relationships between records.

**Bullets:**
- The pattern needs three things: addressable records, searchable content, relationships
- Healthcare: `find "recurring headache with aura"` + `graph_traverse -prescribed->`
- Legal: `find "breach of fiduciary duty"` + `graph_traverse -cites->`
- Code: `ls src/` + `grep "TODO"` + `graph_traverse -calls->`
- SurrealDB is not required -- works over Postgres+pgvector, MongoDB, Neo4j

**Speaker Notes:** "SurrealFS is not an e-commerce product. It is a pattern. Any domain with addressable records, searchable content, and relationships between records can use the same approach. Healthcare, legal, code navigation, knowledge management. The filesystem metaphor works because LLMs already know the filesystem. SurrealDB makes it easy by putting everything in one engine, but the pattern works over any backend."

**Duration:** 15 seconds

---

## Slide 16: Q&A

**Subtitle:** Questions, contact, and next steps

**Visual:** Clean slide with "Q&A" in large text. Team contact information below. A small SurrealFS tool table in the bottom corner as a visual anchor. Optional: QR code linking to the GitHub repository.

**Bullets:**
- Team: Jordan (architecture + agent), Desmond (SurrealDB + debugging), Charlotte (data + prompts), Shashwat (RAG testing), B (presentation + API)
- Open source: SurrealFS pattern is MIT-licensed and reusable
- Built with: LangChain, LangGraph, SurrealDB 3.0, FastAPI, OpenAI
- Key takeaway: borrow the LLM's priors -- do not invent a new tool taxonomy

**Speaker Notes:** "Thank you. We are Taro.ai. The SurrealFS pattern is open source and reusable across any data domain. Happy to take questions -- especially about the SurrealDB 3.0 bugs, the tool consolidation journey, or how to apply this pattern to your own data."

**Duration:** 10 seconds

---

## Timing Summary

| Slide | Title | Duration |
|-------|-------|----------|
| 1 | Title | 15s |
| 2 | The WhatsApp Moment | 20s |
| 3 | The Problem | 20s |
| 4 | The Bet | 15s |
| 5 | System Architecture | 15s |
| 6 | SurrealFS Tools | 15s |
| 7 | The Harness | 15s |
| 8 | LIVE DEMO | 120s |
| 9 | Graph Schema | 15s |
| 10 | One Database, Seven Roles | 15s |
| 11 | The Improvement Arc | 15s |
| 12 | SurrealDB 3.0 Bugs | 15s |
| 13 | Lessons Learned | 15s |
| 14 | Results Dashboard | 10s |
| 15 | The Reusable Pattern | 15s |
| 16 | Q&A | 10s |
| **Total** | | **305s (~5 min)** |
