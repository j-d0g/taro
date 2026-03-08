# Results: The Numbers Behind 95.3%

> Taro.ai -- LangChain x SurrealDB Hackathon, London, March 6-8 2026

---

> **TL;DR**
> - 95.3% pass rate on 43 adversarial stress test queries, with 100% tool selection accuracy across all 18 selection tests.
> - The single biggest improvement came from renaming tools to bash commands -- tool selection jumped from 44% to 100% with zero logic changes.
> - Two remaining failures: one OpenAI rate limit under sustained load, one test assertion that was too broad. Neither was a harness defect.

---

## Headline Metrics

| Metric | Value |
|--------|-------|
| Stress test pass rate | **95.3%** (41/43 queries) |
| Tool selection accuracy | **100%** (18/18 queries) |
| Unit tests passing | **91** |
| API endpoints | **20** |
| SurrealFS tools | **9** |
| Graph edge types | **12** |
| Products in database | **1,890** (431 unique, scraped from lookfantastic.com) |
| Customers | **2,526** synthetic profiles |
| Orders | **6,862** with line items |
| Reviews | **3,247** with sentiment |
| Product verticals | **3** (Skincare, Haircare, Body & Fragrance) |
| Subcategories | **9** |
| SSE streaming | Real-time tokens + live tool trace cards |
| Conversation persistence | SurrealDB `checkpoint` + `write` tables via SurrealSaver v2.0.0 |

---

## Stress Test Breakdown by Category

The 43 queries were distributed across 8 categories designed to probe different failure modes. Round 4 results:

| Category | Score | Pass Rate | Notes |
|----------|-------|-----------|-------|
| Tool Selection | 18/18 | **100%** | Agent picks the right tool every time |
| Multi-Hop Reasoning | 3/4 | 75% | 1 failure was OpenAI rate limit |
| Edge Cases | 5/6 | 83% | 1 false positive (test too strict) |
| Adversarial | 3/3 | **100%** | Prompt injection and data extraction blocked |
| Graph Reasoning | 5/5 | **100%** | All 5 traversal patterns work correctly |
| Schema Awareness | 3/3 | **100%** | `explore_schema` works after SurrealDB 3.0 fix |
| Personalization | 1/1 | **100%** | Multi-turn conversation with context retention |
| Failure Recovery | 3/3 | **100%** | Graceful handling of non-existent entities |

Five categories achieved perfect scores. The two imperfect categories were both caused by infrastructure issues, not agent logic.

### The Improvement Arc

Comparing category scores across rounds shows where the work went:

| Category | Round 1 | Round 4 | Delta |
|----------|---------|---------|-------|
| Tool Selection | 44% (8/18) | **100%** (18/18) | +56pp |
| Multi-Hop Reasoning | 0% (0/4) | 75% (3/4) | +75pp |
| Graph Reasoning | 20% (1/5) | **100%** (5/5) | +80pp |
| Schema Awareness | 0% (0/3) | **100%** (3/3) | +100pp |
| Edge Cases | 83% (5/6) | 83% (5/6) | -- |
| Adversarial | 100% (5/5) | **100%** (3/3) | -- |
| Failure Recovery | 100% (3/3) | **100%** (3/3) | -- |

The biggest gains came from fixing SurrealDB 3.0 compatibility (schema awareness: +100pp, graph reasoning: +80pp) and tool consolidation (tool selection: +56pp). Edge cases and adversarial handling were strong from round 1 -- the ReAct agent's built-in safety was already sufficient.

---

## Tool Selection Analysis

This is the result we are most proud of.

**Round 1: 44% tool selection accuracy.** The agent had 13 tools with overlapping semantics. Given a query like "recommend a moisturizer," it had to choose between `find`, `hybrid_search`, and `semantic_search` -- three tools that all do essentially the same thing. It chose wrong more than half the time, or failed to choose at all.

**Round 4: 100% tool selection accuracy.** We consolidated to 9 tools and renamed them after bash commands: `ls`, `cat`, `find`, `grep`, `tree`, `explore_schema`, `graph_traverse`, `surrealql_query`, `web_search`.

No model change. No prompt change (beyond listing the new tool names). No additional few-shot examples for tool selection. The improvement came entirely from:

1. **Eliminating duplicates** -- one tool per function, no ambiguity
2. **Using familiar names** -- LLMs have strong priors on bash commands from training data

This is context engineering in its purest form: instead of teaching the model new concepts, borrow concepts it already knows. The model does not need to learn what `find` does -- it has seen millions of examples. It does need to learn what `hybrid_search` does, and a 50-word tool description is not enough context to do it reliably under adversarial pressure.

---

## Remaining Failures

Two queries failed in round 4. We investigated both.

### Failure 1: OpenAI Rate Limit (Multi-Hop Reasoning)

One of the four multi-hop reasoning queries -- which require chaining 3-5 tool calls -- hit OpenAI's `RateLimitError` on the third tool call. Our retry logic (5-second backoff, 1 retry) caught most rate limits but not this one. This is an infrastructure constraint, not a harness defect. The 2-second delay between stress test queries mitigated most rate limiting, but sustained multi-tool chains within a single query still make multiple LLM calls in rapid succession.

**Mitigation applied:** Rate limit retry with exponential backoff. Under normal (non-stress-test) usage, rate limits are not observed.

### Failure 2: `not_error()` False Positive (Edge Cases)

The gibberish input test (`"asdfghjkl qwerty"`) expected the agent to respond gracefully and the response to not contain the word "error." The agent responded perfectly: it explained it could not find products matching that query and asked the user to clarify. But its response included the phrase "if that was sent in error" -- which triggered the `not_error()` assertion.

**Fix applied:** Changed `not_error()` from checking `"error" not in reply.lower()` to checking for specific system error phrases: `"i encountered an error"`, `"error processing your request"`, `"RateLimitError"`. With this fix, the effective pass rate is 97.7% (42/43), with the single remaining failure being a rate limit.

---

## Test Infrastructure

We built three tiers of testing, each serving a different purpose:

### `make verify` -- Unit Tests (91 tests, ~10 seconds)

Runs `pytest` against the full test suite. No external API calls. No running SurrealDB instance required. Tests cover:

- All 20 REST endpoints (request/response validation)
- SSE streaming event format
- Preference CRUD operations
- Tool safety (SQL injection prevention, write blocking)
- RRF fusion algorithm correctness
- Import sanity checks

This runs on every code change via the Stop hook. If unit tests fail, the commit does not happen.

### `make smoke` -- Quick Integration (3 queries, ~1 minute)

Three representative queries against the live API with a real SurrealDB backend:
- A product search (tests vector + BM25 pipeline)
- A graph traversal (tests edge walking)
- An adversarial input (tests safety)

This is the "did I break anything obvious" check. Fast enough to run after every significant change.

### `make stress` -- Adversarial Suite (43 queries, ~20 minutes)

The full adversarial battery. Restarts the API first (`make restart`), then runs 43 queries with 2-second pacing. Categories cover tool selection, multi-hop reasoning, edge cases, adversarial attacks, graph reasoning, schema awareness, personalization, and failure recovery.

Each failure is classified by error type (rate limit vs. logic vs. tool selection vs. test defect) to prevent infrastructure issues from masking real bugs.

---

## What the Numbers Mean

The 95.3% number is not the point. The point is the diagnostic infrastructure around it.

When round 3 dropped to 60.5%, we did not panic and rewrite the prompt. We classified failures and found that 15 of 17 were rate limits. When the gibberish test failed, we did not weaken the test -- we made the assertion more precise. When tool selection was at 44%, we did not add more few-shot examples -- we changed the tool names.

Each fix targeted the root cause, not the symptom. That is why the trajectory went up and stayed up.
