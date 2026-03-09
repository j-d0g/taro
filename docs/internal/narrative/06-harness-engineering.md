# Harness Engineering: Constrain Outputs, Not Process

> Taro.ai -- LangChain x SurrealDB Hackathon, London, March 6-8 2026

---

> **TL;DR**
> - A harness is the environment, constraints, and feedback signals that surround an AI agent -- it determines what the agent can achieve more than the model itself does.
> - The SurrealFS pattern (filesystem metaphor over any data source) gives LLMs zero-shot tool selection by borrowing concepts from their training data instead of teaching new ones.
> - GATHER -> ACT -> VERIFY is not three prompts. It is a constraint loop: the agent cannot answer until it has evidence, and the harness makes evidence-gathering the path of least resistance.

---

## What is Harness Engineering?

The term comes from two independent sources arriving at the same conclusion in early 2026.

**OpenAI** described it in the context of Codex: harness engineering is the shift from writing code to "designing environments, specifying intent, and providing structured feedback." The agent operates within a constrained sandbox with rich verification methods. The human's job is not to tell the agent what to do step by step -- it is to build the environment where doing the right thing is easier than doing the wrong thing.

**Anthropic** articulated it through Claude Code's architecture: gather context, take action, verify work, repeat. The harness provides tools, context management, and an execution environment. Settings are scoped from organization-wide policies down to personal preferences. The key insight is the same: the agent's ceiling is set by the quality of its harness, not the quality of its model.

Martin Fowler synthesized both into a framework: harness engineering is about **architectural constraints** (enforced dependency sequences), **entropy management** (periodic agents that detect inconsistencies), and **feedback loops** (verifiable evidence at every step).

What all three agree on: **constrain outputs, not process.** Define what "done" looks like. Do not prescribe the steps to get there. The model is better at finding paths than you are at specifying them -- but only if you tell it where the walls are.

---

## The SurrealFS Pattern

SurrealFS is a reusable pattern for exposing any data source to an LLM agent through a filesystem metaphor. The idea is simple: instead of inventing tool names that describe what the tool does (`hybrid_search`, `get_record`, `browse_hierarchy`), name them after bash commands the model already knows.

| SurrealFS Tool | Bash Analog | Database Operation |
|----------------|-------------|-------------------|
| `ls` | `ls /path` | List tables or records |
| `cat` | `cat /path` | Read a full record |
| `find` | `find . -name "pattern"` | Hybrid vector + BM25 search (RRF fusion) |
| `grep` | `grep "term" /path` | Keyword search (CONTAINS fallback) |
| `tree` | `tree /path` | Hierarchical view of categories/goals |
| `explore_schema` | `file`, `stat` | Database introspection (INFO FOR DB/TABLE) |
| `graph_traverse` | `ln -s`, symlink following | Walk graph edges between records |
| `surrealql_query` | `sql` client | Raw read-only queries |
| `web_search` | `curl` | External web search (Tavily) |

The pattern works because of how LLMs select tools. Given a user query like "what moisturizers do you have?", the model needs to decide which tool to call. With a tool named `hybrid_search`, it must read the tool description, parse the semantics, and hope its understanding matches the implementer's intent. With a tool named `find`, it already knows: `find` locates things that match a pattern. The decision is near-instant because it draws on billions of tokens of prior context.

We measured this directly. With 13 tools using novel names: **44% tool selection accuracy.** With 9 tools using bash names: **100% tool selection accuracy.** Same model, same queries, same underlying database operations. The only change was the surface-level naming.

This is not a SurrealDB-specific trick. The SurrealFS pattern applies to any data source with records, search, and relationships. The filesystem metaphor is universal because every LLM has been trained on filesystem interactions.

---

## GATHER -> ACT -> VERIFY

The three-phase constraint loop is the structural core of the harness. It is encoded in the system prompt, reinforced by worked examples, and validated by the stress test suite.

**GATHER: Orient before you search.** Before executing any query, the agent must understand the data landscape. What tables exist? What fields does a product have? What categories are in the hierarchy? The GATHER tools (`ls`, `cat`, `tree`, `explore_schema`) are low-cost, high-information operations that prevent blind searches.

Without GATHER, the agent guesses. It searches for "moisturizer" without knowing that the database organizes products by subcategory. It recommends products without checking if they exist. It claims a category has items without verifying the schema supports that relationship.

**ACT: Execute informed queries.** With context from GATHER, the agent makes targeted queries. `find "retinol serum for sensitive skin"` for conceptual search. `grep "CeraVe" --type=product` for exact matches. `graph_traverse product:abc -also_bought->` for relationship discovery. `surrealql_query "SELECT count() FROM product WHERE price < 30 GROUP ALL"` for aggregations.

The critical insight here is that ACT is not "search." It is "search with context." The agent that GATHERed first knows which edge types exist, which fields are queryable, and which tables contain the data. Its searches are precise because it built a mental model of the data before querying it.

**VERIFY: Ground-truth before responding.** The agent must `cat` the actual records it plans to recommend. This catches hallucinations, stale data, and misinterpreted search results. If the agent found a product via vector search and is about to recommend it, VERIFY forces it to read the full record and confirm the price, availability, and description match what it is about to tell the user.

The constraint is structural, not aspirational. The system prompt says: "You MUST use tools. NEVER answer from your own knowledge." The worked examples all show a GATHER-ACT-VERIFY chain. The stress tests explicitly check for tool usage in every response. An agent that skips verification fails the test.

---

## The Feedback Spectrum

Harness signals are not binary. They range across three dimensions: hard to soft, fast to slow, automated to human.

### Hard Signals (automated, deterministic)

These fire immediately and unambiguously. In Taro:

- **Tool errors**: SurrealDB returns an error string instead of results. The agent sees this in the tool output and can retry or try a different approach.
- **Empty results**: A `find` query returns no matches. The agent must broaden its search, try `grep`, or use `graph_traverse` from a different entry point.
- **Type errors**: RecordID objects instead of strings, missing fields, wrong data shapes. These crash the tool call and produce a visible error.
- **Test failures**: `make verify` runs 91 unit tests. Any regression is caught before commit.

### Soft Signals (heuristic, probabilistic)

These require interpretation:

- **Search scores**: RRF fusion produces a ranked list. Low scores signal poor matches -- the agent should not recommend the top result if its score is 0.12.
- **Tool-call efficiency**: An agent making 12 tool calls for a simple question is over-exploring. The harness does not penalize this directly, but it wastes tokens and latency.
- **Graph traversal depth**: Following 5 edges to answer "what category is this product in?" suggests the agent is lost. One `graph_traverse` with `belongs_to` suffices.

### Async Signals (delayed, human-mediated)

These close the loop over hours or sessions:

- **User preferences**: Cart / Keep / Remove actions on product cards create `wants`, `interested_in`, and `rejected` graph edges. These are not real-time feedback on the current query, but they train future recommendations.
- **Memory distillation**: `POST /distill` runs an LLM over the conversation to extract preferences and context, stored in the user's profile for future sessions. The feedback from conversation 1 improves conversation 5.
- **Conversation abandonment**: If the user stops mid-conversation, something went wrong. This is the strongest negative signal and the hardest to capture.

The design heuristic: **layer feedback by latency.** Hard signals fire in milliseconds. Soft signals are evaluated per-response. Async signals accumulate over sessions. A harness that only uses hard signals cannot learn from user behavior. A harness that only uses async signals cannot prevent hallucinations in real time.

---

## Context Engineering > Prompt Engineering

Prompt engineering optimizes the text you send to the model. Context engineering optimizes the world the model operates in. The distinction matters.

A prompt engineer might write: "When the user asks about related products, use the graph_traverse tool with the also_bought edge type." This works for that specific case but does not generalize. Every new edge type requires a new prompt clause. Every new query pattern requires a new instruction.

A context engineer asks: "What would make the model choose the right tool without being told?" The answer, in our case, was to name the tools after concepts the model already understands. `find` instead of `hybrid_search`. `cat` instead of `get_record`. `grep` instead of `keyword_search`.

The 44% to 100% tool selection improvement required zero additional prompt text about tool selection. We removed instructions. The model needed less guidance because the tools were self-documenting through their names.

This generalizes beyond naming. Context engineering includes:

- **Data architecture**: Structuring records so that `cat /products/abc` returns everything the agent needs in one call, including graph edge counts that hint at further exploration.
- **Tool output format**: Including `source_id` in every search result so the agent can bridge from documents to products without a separate lookup step.
- **Schema design**: Making graph edges discoverable through `explore_schema` so the agent knows what relationships exist before trying to traverse them.
- **Error messages**: Returning "Edge type 'purchased' does not exist. Valid types: placed, contains, has_review, belongs_to, child_of, also_bought, supports_goal, contains_ingredient, related_to" instead of a generic 400 error.

Every one of these is a context decision, not a prompt decision. They shape the environment so that the right action is the obvious action.

---

## The Self-Improvement Flywheel

Every bug we hit during the hackathon followed a five-step cycle:

1. **Detect**: Stress test fails, or we observe bad behavior in the chat
2. **Diagnose**: Classify as SurrealDB issue, prompt issue, tool issue, or test issue
3. **Fix**: Implement the minimal correct solution
4. **Extract**: Write a lesson with Problem / Solution / Prevention sections
5. **Persist**: Add to `tasks/lessons.md` with a numbered identifier (L1 through L13)

The 13 lessons are not documentation. They are executable knowledge. The project's CLAUDE.md instructs every agent session to "review lessons at session start" and "search lessons first before starting work." A new session that encounters a RecordID serialization issue does not need to rediscover that `str()` wrapping is required -- it reads L12 and applies the known fix.

Three meta-patterns emerged:

**Silent failures are the most expensive bugs.** L1 (KNN returns error strings), L2 (result format changed), L12 (RecordID objects) all shared a property: the code did not crash. It returned empty or wrong results. These bugs survived multiple rounds of manual testing because the absence of results looks like "no matches" rather than "broken query." The prevention rule: always test that known data produces non-empty results.

**Test infrastructure bugs masquerade as logic bugs.** L6 (rate limits), L7 (`not_error()` too broad), L10 (no pacing) all made the harness look broken when the harness was fine. The prevention rule: classify every failure by error type before investigating the harness.

**Weaker models are better fuzzers.** L11 discovered two real bugs that `gpt-4o` avoided by being "polite" about tool calling. `gpt-4o-mini` called tools more aggressively, hit more code paths, and exposed the RecordID crash and a graph traversal syntax error. The prevention rule: validate with at least two model tiers.

---

## 5 Design Heuristics

These are the practical takeaways from building an agentic search harness over 48 hours.

**1. Constrain outputs, not process.** Tell the agent it must cite source records. Do not tell it which tool to call first. The model is better at finding paths than you are at specifying them. The GATHER-ACT-VERIFY loop constrains what "done" looks like (evidence-backed answer) without constraining how the agent gets there.

**2. Borrow concepts, do not invent them.** Name tools after things the model already knows. Use filesystem metaphors. Use HTTP verbs. Use SQL keywords. Every novel concept you introduce is a concept the model must learn from a 50-word description. Every borrowed concept comes with billions of tokens of prior understanding.

**3. Make failure loud and specific.** A custom error message that says "Edge type 'purchased' does not exist. Valid types: placed, contains, has_review..." is worth more than a stack trace. The model can act on specific feedback. It cannot act on `TypeError: string indices must be integers`.

**4. Layer feedback by latency.** Hard signals (tool errors) fire in milliseconds. Soft signals (empty results, low scores) fire per-response. Async signals (user preferences, memory distillation) fire per-session. A robust harness covers all three timescales.

**5. Watch for signal absence.** The most dangerous state is when the harness is silent but the answer is wrong. KNN returning error strings instead of exceptions. BM25 returning empty arrays instead of errors. Result format changes that produce empty lists instead of crashes. Actively probe for gaps: test that known data produces non-empty, correct results.

---

## Beyond E-Commerce

The SurrealFS pattern and the GATHER-ACT-VERIFY loop are not specific to product search. They apply wherever an agent needs to navigate structured data with relationships.

**Healthcare records.** `ls /patients/abc123` lists encounters. `cat /encounters/xyz` reads the full clinical note. `find "recurring headache with visual aura"` searches across notes with semantic similarity. `graph_traverse encounter:xyz -prescribed->` finds medications. `grep "metformin" --type=medication` finds all patients on a specific drug. The GATHER phase prevents the agent from recommending a drug without checking the patient's allergy list. The VERIFY phase forces it to confirm dosage against the actual prescription record.

**Legal document review.** `ls /cases/2024` lists filings. `cat /filings/motion-123` reads the full text. `find "breach of fiduciary duty"` searches across all documents. `graph_traverse filing:motion-123 -cites->` finds precedents. `tree /statutes/commercial-code` shows the statutory hierarchy. The constraint loop prevents the agent from citing a case without verifying it exists and is relevant.

**Code navigation.** This is where the pattern started -- OpenAI's Codex uses a filesystem harness natively. `ls src/` lists modules. `cat src/main.py` reads a file. `find "database connection pool"` searches semantically across the codebase. `graph_traverse function:handle_request -calls->` traces the call graph. `grep "TODO" --type=py` finds technical debt. The metaphor is literal because code already lives in a filesystem.

**Knowledge management.** `ls /teams/engineering` lists team members and documents. `cat /docs/architecture-decision-003` reads an ADR. `find "why did we choose Kafka over RabbitMQ"` searches across meeting notes, Slack exports, and decision logs. `graph_traverse decision:003 -supersedes->` traces how architectural decisions evolved.

In each case, the same three things make the pattern work:

1. **Records with IDs** -- addressable entities that `cat` can read
2. **Searchable content** -- text or embeddings that `find` and `grep` can query
3. **Relationships between records** -- edges that `graph_traverse` can walk

SurrealDB happens to provide all three in a single database. But the SurrealFS pattern does not require SurrealDB. You can build it over Postgres + pgvector, over MongoDB + Atlas Search, over Neo4j + full-text indexes. The pattern is the interface, not the backend. The filesystem metaphor works because it maps to how LLMs already think about navigating information, regardless of where that information is stored.

The harness is the product. The model is replaceable. The data source is replaceable. What remains constant is the constraint loop, the feedback spectrum, and the principle that borrowed concepts outperform invented ones.
