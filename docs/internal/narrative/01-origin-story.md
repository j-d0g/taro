# From WhatsApp to SurrealFS

> The origin story of Taro.ai — how a Friday night WhatsApp thread turned a filesystem metaphor into a multi-model search harness for SurrealDB.

---

**TL;DR**

- A late-night WhatsApp riff on "Claude Code but for databases" led to the SurrealFS idea: `ls`, `cat`, `find`, `grep`, `tree` mapped over SurrealDB's vector, BM25, and graph engines.
- The SurrealDB team's immediate reaction — "that's quite good" — validated the bet: LLMs already know how to use bash. Give them a filesystem over your database and tool selection becomes near-zero-shot.
- 48 hours later: 9 tools, 12 graph edge types, 91 unit tests, 95.3% on a 43-query adversarial stress test. One database backend for everything.

---

## The Friday Night

The LangChain x SurrealDB hackathon kicked off at 6pm on Friday, March 6, 2026 in London. By 9pm the venue was closing. The team — strangers hours earlier — scattered to their homes and opened a WhatsApp group.

At 22:06, Jordan started thinking out loud about stack allocation and strengths. By 22:22, the small talk was over and the architecture conversation had begun:

> "Thinking to avoid scope creep focus on product reccs as core offering"
> — Jordan, 22:22

The initial pitch was straightforward: an e-commerce recommendation agent grounded in SurrealDB's multi-model capabilities. Product search using vector, keyword, and graph. Desmond from SurrealDB asked Jordan to break down the stack into tasks.

Jordan posted a wall of text at 22:40 — a loose architecture covering LangGraph stateful flows, Tavily search for baseline, SurrealDB schema design, evals with LangSmith, self-improvement loops, and a UI. The critical line, buried in the middle:

> "our core prop can be doing multimodal search that utilises different strengths and weaknesses of vector, key store, topological etc. and have our agent route to the most appropriate given a query"
> — Jordan, 22:40

The conversation drifted into self-improvement loops, fine-tuning adapters, and whether you could run real-time SFT on a 30B model during a hackathon (you cannot — "30B needs an H100 or H200 for comfortable training," Desmond noted). They ruled it out. Good context engineering with a memory store would be enough.

Then at 23:10, the real idea surfaced:

> "I think about what the guy said about replicating the filesystem structure that coding agents have in surrealdb"
> — Jordan, 23:10

Two minutes later, the full shape:

> "We could define a verbose enough tool set for agents to perform agentic search across the db. I think this would work well given how expressive and feature rich it is. A harness for surrealdb search similar to claude code's bash set up with grep."
> — Jordan, 23:12

Desmond's response was immediate:

> "thats quite good, treat surreal as a ground truth wealth of knowledge with multiple search tools for different modes or contexts"
> — Desmond SurrealDB, 23:13

And then the refinement:

> "ultimately an agentic workflow calls the surreal search tools each tool possibly interfacing with many different modes of data in the dbs"
> — Desmond SurrealDB, 23:14

That was it. The architecture was decided at 23:14 on a Friday night over WhatsApp. Jordan confirmed — "I think if we could pull it off it'd be a great project" — and Desmond sealed it: "and opensource, surreal will like that."

The team named themselves at 22:21, when Jordan was throwing out puns ("shopif.ai", "e-clawmmerce") and suggested they "just pick a random fruit or vegetable." Desmond replied with one word: "Taro." Jordan appended the suffix: "Taro.ai."

*(Source: `/HACK.md`, WhatsApp group chat log, 06/03/2026 21:03–23:44)*

---

## The Problem

E-commerce product search is deceptively hard. Each search modality solves part of the problem and fails at the rest:

**Keyword search** (BM25) is precise but brittle. Searching "moisturizer" finds moisturizers. But "something for dry skin in winter" returns nothing — there is no product with those exact terms in its description. BM25 matches tokens, not intent.

**Vector search** (HNSW embeddings) captures intent beautifully. "Something for dry skin in winter" lands near moisturizers, serums, and barrier creams. But ask for "retinol serum under 30 pounds" and vector search returns results semantically close to the concept of retinol — including 50-pound products, non-retinol items, and blog posts about retinol side effects. It understands meaning but ignores specifics.

**Graph traversal** answers relationship questions that neither search mode can touch. "What do customers who bought this moisturizer also buy?" "Does this serum contain any ingredients I am allergic to?" "Show me everything in the haircare category tree." But graphs do not search — they navigate. You need to already know your starting node.

The standard industry answer is to pick one modality, add heuristic fallbacks, and accept the gaps. Or run multiple specialized databases (Pinecone for vectors, Elasticsearch for keywords, Neo4j for graphs) and build a fragile orchestration layer between them.

SurrealDB offered a different proposition: all three modalities in a single database engine. HNSW vector indexes, BM25 full-text search, and native graph relations (`RELATE` statements with typed edges) — all queryable through one query language. One connection, one schema, one source of truth.

The problem was not the database. The problem was the interface. How do you give an LLM agent coherent access to all three modalities without drowning it in 13 overlapping tools?

*(Source: `/tasks/spec-agentic-reasoning.md`, Section 5: Compound Search Strategy; `/taro-api/tasks/lessons.md`, L3–L4)*

---

## The Bet

The bet was simple and counterintuitive: name your database tools after bash commands.

`ls` to list tables and records. `cat` to read a full record. `find` for hybrid semantic+keyword search with RRF fusion. `grep` for exact keyword matching. `tree` for hierarchical category views. `graph_traverse` for walking edges. `explore_schema` for introspection. `surrealql_query` for raw queries. `web_search` for external fallback.

The insight — which became Lesson L4 in the project log — was that LLMs already have deep priors on when to use these commands. Every coding agent in their training data uses `grep` for keyword search and `find` for broader discovery. You do not need to teach the model a new tool taxonomy. You borrow one it already knows.

This is not a metaphor for the sake of cleverness. It is a context engineering decision. The filesystem metaphor reduced tool selection confusion from a real problem (13 tools with overlapping semantics, 51.1% accuracy on adversarial queries) to a near-solved one (9 tools with distinct roles, 95.3% accuracy) without changing the underlying search algorithms at all.

On top of the tools, the team layered a constraint loop: GATHER, then ACT, then VERIFY. The agent must orient itself (`ls`, `tree`, `explore_schema`) before searching (`find`, `grep`, `graph_traverse`), and must verify its recommendations (`cat` on each product) before responding. This three-phase harness, combined with worked examples in the system prompt, eliminated the most common agent failure mode: answering from its own parametric knowledge instead of the database.

*(Source: `/tasks/harness-engineering.md`; `/tasks/lessons.md`, L4–L5)*

---

## The Team

Jordan proposed the architecture, built the agent core, and drove the SurrealFS design from Friday night through Sunday morning. The connection to SurrealDB came through Desmond, who was embedded with the team and validated the filesystem idea on the spot — then helped debug the five SurrealDB 3.0 compatibility issues that surfaced during the build (broken KNN operators, changed result formats, missing table auto-creation, RecordID objects instead of strings, and BM25 returning empty results silently).

Charlotte brought e-commerce domain knowledge, data modeling, and prompt engineering. Shashwat contributed RAG testing experience from production agent systems. B handled presentation and API integration work.

The name stuck from minute one. Desmond said "Taro." Jordan said "Taro.ai." Nobody suggested anything else. At 23:44 on Friday night, Jordan posted the priority list and went to sleep:

> "1. basic prod reccs agent that utilises surrealdb modes
> 2. closed self-improvement loop
> 3. a clean UI
> 4. surrealdb agentic search (would be higher but depends on feasibility)
> 5. expanding uses to customer service, etc."
> — Jordan, 23:44

By Sunday morning, items 1 through 4 were shipped. The "depends on feasibility" caveat on SurrealFS turned out to be unfounded. The filesystem metaphor was not just feasible — it was the core differentiator.

*(Source: `/HACK.md`; `/docs/COMPLETED.md`; `/CHANGELOG.md`)*

---

*Next: [02-architecture.md] — How 9 bash commands map to vector, BM25, and graph queries inside a single SurrealDB instance.*
