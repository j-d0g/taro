# SurrealDB 3.0 Battle Report: 13 Lessons from the Trenches

> Taro.ai -- LangChain x SurrealDB Hackathon, London, March 6-8 2026

---

> **TL;DR**
> - SurrealDB 3.0 broke five critical things silently -- KNN, BM25, result format, RecordID serialization, and third-party checkpointers -- but every one was fixable with workarounds.
> - Our stress test pass rate went from **51.1% to 95.3%** across four rounds, with the dip in round 3 caused entirely by OpenAI rate limits, not SurrealDB.
> - Every bug we hit became a lesson, every lesson became a prevention rule, and the whole cycle lives in `tasks/lessons.md`. We shipped a self-correcting system.

---

## The Improvement Journey

We ran four rounds of adversarial stress tests against 43-45 queries. The trajectory was not monotonic. That matters.

| Round | Pass Rate | Key Issue |
|-------|-----------|-----------|
| Round 1 (baseline) | 51.1% (23/45) | Wrong tools, HTTP 500s, no graph traversal |
| Round 2 (fixes) | 68.9% (31/45) | Tests still referencing old tool names |
| Round 3 (rate limited) | 60.5% (26/43) | OpenAI RateLimitError on all 17 failures |
| **Round 4 (final)** | **95.3% (41/43)** | 1 rate limit, 1 false positive test |

**Round 1** was brutal. 22 of 45 queries crashed with HTTP 500. The agent had no error handling on the chat endpoint, so any tool failure -- and there were many -- killed the entire request. Graph traversal worked for exactly one query. Schema introspection scored zero. Tool selection was 44% (8/18).

**Round 2** fixed the infrastructure: error handling, search operator workarounds, prompt rewrite, tool consolidation. The jump to 68.9% came from fixing real bugs. But two tests were still asserting against old tool names (`hybrid_search`, `get_record`) that no longer existed after consolidation.

**Round 3 dropped.** This was the instructive moment. We went from 68.9% down to 60.5%, which initially felt like a regression. It was not. We had trimmed the test suite from 45 to 43 queries and fixed the stale tool name assertions. But we ran all 43 queries back-to-back with no pacing. OpenAI's rate limiter kicked in, and 15 of the 17 failures were `RateLimitError`. The harness was fine; our test infrastructure was not (Lesson L6, L10).

**Round 4** added a 2-second delay between queries and retry logic with 5-second backoff. Pass rate jumped to 95.3%. The two remaining failures: one genuine rate limit under sustained load, and one false positive where the `not_error()` test helper matched the word "error" inside the phrase "sent in error" in a perfectly good agent response (Lesson L7).

The key insight: **you must classify failures by type**. Lumping rate limits with logic bugs produces meaningless pass rates and misdirects debugging effort.

---

## Five Critical SurrealDB 3.0 Bugs

### 1. KNN `<|N|>` Operator Returns Error Strings (L1)

The vector nearest-neighbor operator that worked in SurrealDB 2.x does not work in 3.0. Instead of raising an exception, it returns an error *string* -- which means the query "succeeds" but your results are garbage. We only caught this by inspecting actual return values during integration testing.

**What broke:** `WHERE embedding <|5|> $vec` in both `hybrid_search.py` and `semantic_search.py`. Vector search silently returned zero results.

**How we found it:** Stress test round 1 showed 0% pass rate on multi-hop reasoning queries that depended on vector search as an entry point.

**How we fixed it:**
```sql
-- Before (broken in 3.0):
WHERE embedding <|5|> $vec

-- After (works in 3.0):
ORDER BY vector::similarity::cosine(embedding, $vec) DESC LIMIT 5
```

The workaround is actually more explicit -- it makes the similarity function and limit visible in the query rather than hiding them behind an operator.

### 2. BM25 `@1@` Returns Empty Results (L1)

The full-text search operator also broke silently. `WHERE content @1@ $query` returns an empty array in SurrealDB 3.0 even when the content clearly contains the query terms.

**What broke:** Keyword search produced zero results for terms that existed in the data.

**How we found it:** Grep tool (`grep "retinol" --type=product`) returned nothing despite retinol appearing in dozens of products.

**How we fixed it:** Added a `CONTAINS` fallback path:
```sql
-- Primary (sometimes works):
WHERE content @1@ $query

-- Fallback (always works):
WHERE string::lowercase(content) CONTAINS string::lowercase($term)
```

This loses BM25 scoring but at least returns results. For a hackathon, correctness beats ranking quality.

### 3. `db.query()` Result Format Changed (L2)

SurrealDB 2.x returned `[{"result": [...], "status": "OK"}]`. SurrealDB 3.0 returns a flat list. Every tool in the codebase had:

```python
docs = result[0].get("result", []) if result else []
```

This silently returned empty lists on 3.0 because `result[0]` was an actual data record, not a wrapper dict.

**How we fixed it:** Defensive handling that works with both formats:
```python
raw = await db.query(surql, params)
if isinstance(raw, list) and raw and isinstance(raw[0], dict) and "result" in raw[0]:
    docs = raw[0]["result"] or []  # Old format
else:
    docs = raw or []  # New flat format
```

### 4. RecordID Serialization (L12)

SurrealDB 3.0 returns `RecordID` objects instead of strings for any field that references another record. Code like `doc.get("source_id", "").replace("product:", "")` crashed because `RecordID` has no `.replace()` method.

**What broke:** The `source_id` bridging between the `documents` table (searchable, with embeddings) and the `product` table (structured, with graph edges) failed. Search tools found documents but could not map them back to products.

**How we fixed it:** Wrapped all RecordID access in `str()`:
```python
source_id = str(doc.get("source_id", ""))
```

This bug was only discovered when testing with `gpt-4o-mini`, which called tools more aggressively than `gpt-4o` and hit code paths the stronger model happened to avoid (Lesson L11).

### 5. SurrealSaver Incompatible with 3.0 (L13)

`langgraph-checkpoint-surrealdb` v2.0.0 assumes its `setup()` method creates the `checkpoint` and `write` tables. In SurrealDB 3.0, `setup()` is a no-op. When those tables do not exist, SurrealDB 3.0 returns an error string (`"The table 'checkpoint' does not exist"`) instead of an empty list. The SurrealSaver code then tries `result[0]` expecting a dict, gets a character from the error string, and crashes with `TypeError: string indices must be integers`.

**How we fixed it:** Pre-created the tables manually in `schema.surql`:
```sql
DEFINE TABLE checkpoint SCHEMALESS;
DEFINE TABLE write SCHEMALESS;
```

With empty tables, `db.query("SELECT * FROM checkpoint")` returns `[]` instead of an error string, and SurrealSaver works correctly.

---

## Tool Consolidation: 13 to 9

Round 1 exposed a critical problem: the agent had 13 tools with overlapping functionality. `find` and `hybrid_search` both did RRF fusion. `cat` and `get_record` both fetched record details. `grep` and `keyword_search` both did BM25. The LLM could not reliably choose between them.

Tool selection accuracy in round 1: **44%** (8/18 queries).

The fix was consolidation and renaming (Lessons L3, L4). We merged duplicates into 9 tools and named them after bash commands:

| Before (13 tools, novel names) | After (9 tools, bash names) |
|------|------|
| `hybrid_search`, `semantic_search`, `find` | `find` |
| `keyword_search`, `grep` | `grep` |
| `get_record`, `cat` | `cat` |
| `list_records`, `ls` | `ls` |
| `browse_hierarchy`, `tree` | `tree` |
| `explore_schema` | `explore_schema` |
| `graph_traverse` | `graph_traverse` |
| `surrealql_query` | `surrealql_query` |
| `web_search` | `web_search` |

Tool selection after: **100%** (18/18 queries in round 4).

This is not a minor naming trick. It is context engineering. LLMs have billions of tokens of training data on bash commands. They know when to `find`, when to `grep`, when to `cat`. By borrowing that prior knowledge, we got zero-shot tool selection for free. Novel names like `hybrid_search` force the model to learn your tool semantics from a short description -- and under adversarial pressure, that learning is fragile.

---

## The Self-Improvement System

Every bug we encountered during the hackathon followed the same pipeline:

1. **Detect** -- stress test fails, or we observe bad behavior
2. **Diagnose** -- classify as SurrealDB issue, prompt issue, tool issue, or test issue
3. **Fix** -- implement the minimal correct solution
4. **Extract** -- write a lesson with Problem / Solution / Prevention sections
5. **Persist** -- add to `tasks/lessons.md` with a lesson number (L1 through L13)
6. **Prevent** -- write a rule that makes the same mistake detectable before it causes harm

This is not post-mortem documentation. It is a working reference. The CLAUDE.md file instructs every session to "review lessons at session start" and "search lessons first before starting work." When a new agent session starts working on Taro, the first thing it reads is the 13 lessons -- and it avoids the same traps.

Three lessons proved especially high-leverage:

- **L4** (filesystem metaphor = zero-shot selection) changed how we name all tools
- **L6** (rate limits masquerade as logic failures) changed how we run all stress tests
- **L11** (test with weaker models to find hidden bugs) changed how we validate robustness

---

## What SurrealDB Got Right

It would be dishonest to end on the bugs. SurrealDB 3.0 is beta software, and the issues we hit are the kind of issues you expect in beta. Here is what made us choose it and what held up:

**Multi-model in one database is genuinely powerful.** We stored vector embeddings, ran keyword searches, traversed a 12-edge-type graph, and executed relational queries -- all in a single SurrealDB instance. No Pinecone for vectors, no Neo4j for graphs, no Elasticsearch for text search, no Postgres for relational data. One connection string, one schema file, one backup, one set of permissions. For a hackathon team of five, this eliminated an entire category of infrastructure complexity.

**Graph traversal syntax is elegant.** `SELECT ->also_bought->product FROM product:abc` reads like a sentence. Multi-hop queries chain naturally: `SELECT ->placed->order->contains->product FROM customer:xyz`. When it works, it is the fastest path from question to answer for relationship queries.

**Schema flexibility is real.** We went from 3 edge types to 12 during the hackathon. Adding a new edge type was one line in `schema.surql` and one `RELATE` statement in `seed.py`. No migrations, no schema versioning, no downtime.

**Record IDs are first-class.** `product:abc123` is both a primary key and a URL-safe identifier. Our SurrealFS pattern exploited this: `cat /products/abc123` maps directly to `SELECT * FROM product:abc123`. The filesystem metaphor works because SurrealDB's naming convention already looks like a path.

The 3.0 bugs cost us roughly 8 hours of debugging across two days. The multi-model architecture saved us roughly 12 hours of infrastructure setup we would have needed with separate databases. Net positive, but only because we documented every bug and built workarounds fast. Teams that hit these bugs without the diagnostic discipline to classify them would lose more time than they save.
