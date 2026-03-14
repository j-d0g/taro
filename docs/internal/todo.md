# TODO - Taro.ai Harness

## Completed (this session)

- [x] Restore and consolidate 13 tools -> 9 SurrealFS tools
- [x] Fix KNN `<|N|>` and BM25 `@1@` operators for SurrealDB 3.0
- [x] Rewrite system prompt with GATHER->ACT->VERIFY + worked examples
- [x] Fix graph_traverse with all 9 edge types + validation
- [x] Fix explore_schema SurrealDB 3.0 result format
- [x] Add error handling + rate limit retry in chat endpoint
- [x] Add user context injection (user_id on ChatRequest)
- [x] Add POST /distill memory distillation endpoint
- [x] Complete schema.surql (user/order/review/goal/ingredient + all 9 edges)
- [x] Add embedding LRU cache
- [x] Fix graph_traverse `->*` syntax (SurrealDB 3.0 -> `->?`)
- [x] Fix RecordID str coercion in find/grep
- [x] Verify cross-model: gpt-4o, gpt-4o-mini, gpt-4.1, gpt-5.2, gpt-5.4 all pass
- [x] Add stress-test + restart-api agents, Makefile targets
- [x] Stress test: 95.3% (41/43)
- [x] Add `ls /users/{id}/preferences/` route + handler; preferences in agent context (wants, interested_in, rejected)
- [x] Load persisted conversation history at chat start and prepend summary for multi-turn context
- [x] Fix learned_pattern query for SurrealDB 3.0 (ORDER BY created_at in SELECT)
- [x] Default checkpointer to MemorySaver (SurrealSaver broken on SurrealDB 3.0); remove reasoning_effort for gpt-5.4
- [x] Add docs/internal/testing-guide.md (step-by-step tests, including distill without make)
- [x] Product Swipe Actions: cart badge above chat bubble (same size), drawer with thumbnails + "View product" link; backend injects preference context when thread_id sent

## Backlog

### Next: Multi-Model Harness Optimisation
**Priority**: High
**Goal**: Compare GPT-5.4, Claude 4.6, Gemini 3.1 on the harness and find the best model for the task. Also explore if frontier models can raise the ceiling beyond 95.3%.

Tasks:
- [ ] Top up Anthropic credits (currently depleted) and Gemini API (free tier exhausted)
- [ ] Run full 43-query stress test on each model (gpt-5.4, claude-4.6, gemini-3.1)
- [ ] Compare: tool selection accuracy, latency, cost per query, response quality
- [ ] Identify model-specific prompt tuning opportunities (e.g. Claude may not need "CRITICAL RULE" shouting)
- [ ] Test if gpt-5.4's larger context window enables richer system prompts
- [ ] Test if frontier models can do multi-hop reasoning in fewer tool calls
- [ ] Optimize: create model-specific prompt variants if needed, or find a universal prompt
- [ ] Decide: which model gives best quality/cost/latency tradeoff for demo
- [ ] Update default model in .env and AVAILABLE_MODELS
- [ ] Document findings in tasks/model-comparison.md

### Next: Augment Review Dataset
**Priority**: High
**Goal**: Every product should have 0-5 written reviews and 0-50 star-only ratings. Use parallel Haiku sub-agents to generate realistic, varied review data at scale.

Tasks:
- [ ] Query current review coverage: how many products have 0 reviews vs some
- [ ] Design review generation prompt: persona-varied, realistic tone, product-aware (reads actual product description/category/price before writing)
- [ ] Spawn parallel Haiku agents (cheap + fast) — each agent handles a batch of products
- [ ] For each product: generate 0-5 written reviews (rating + comment + sentiment) and 0-50 star-only ratings (rating only, no text)
- [ ] Distribution should feel natural: popular products get more reviews, niche products fewer
- [ ] Insert via SurrealDB: create review records + RELATE order->has_review->review edges
- [ ] Create matching synthetic orders/users if needed for the graph edges
- [ ] Verify: count reviews per product, check distribution looks realistic
- [ ] Re-run `make smoke` to confirm agent can surface review data in responses

### Next: Repository Audit & Cleanup
**Priority**: High
**Goal**: Scan entire repo for stale docs, unused code, broken references, legacy patterns. Polish to be clean, current, and consistent. Minimal but sufficient documentation.

Tasks:
- [ ] Scan MEMORY.md, CLAUDE.md, README.md, DEMO.md, CHANGELOG.md — flag anything that references old tool names (hybrid_search, keyword_search, semantic_search, get_record), old tool counts (8/13), wrong ports, stale instructions
- [ ] Scan all code for unused imports, dead code paths, orphaned files (e.g. old tool files that are no longer in ALL_TOOLS)
- [ ] Check test files reference correct tools/endpoints — no tests for removed tools
- [ ] Verify schema.surql matches actual seeded data (field names, types, edge definitions)
- [ ] Check seed.py / mock_data.py are consistent with schema and current tool expectations
- [ ] Audit Makefile targets — do they all work? Correct ports?
- [ ] Check .env.example matches actual required vars
- [ ] Verify frontend JS (api.js, chat.js) points to correct API endpoints and handles current response format
- [ ] Remove or deprecate: hybrid_search.py, semantic_search.py, keyword_search.py, get_record.py if still present but unused
- [ ] Update README with current architecture (9 tools, distill endpoint, harness phases)
- [ ] Raise questions/concerns about anything ambiguous or potentially broken
- [ ] Keep docs minimal — no bloat, no redundancy between files

### BUG: User/Customer Table Mismatch (blocks user context) — FIXED
**Priority**: Critical
**Goal**: Fix the broken user lookup pipeline. The agent can't find users because `ls /users/` and chat context injection query the `user` table, but `seed.py` creates records in the `customer` table. This makes the entire personalization flow non-functional.

**Root cause**: `fs_tools.py:_handle_list_users` queries `SELECT ... FROM user`, `main.py:122` queries `SELECT * FROM user:{user_id}`, but `seed.py:151` creates `CREATE customer:{cid}`. Table name mismatch throughout.

Tasks:
- [x] Decide: unify on `customer` (matches e-commerce domain) or `user` (matches SurrealFS `/users/` metaphor). Recommendation: keep `customer` in DB, alias `/users/` routes to query `customer` table
- [x] Update `fs_tools.py`: all `_handle_list_users`, `_handle_show_user`, `_handle_list_user_orders` to query `customer` table
- [x] Update `main.py` chat context injection (line ~129) to query `customer` not `user`
- [x] Update `main.py` distill endpoint (line ~260) to read/write `customer` context field
- [x] Verify schema.surql defines `customer` with a `context` field for distillation
- [x] Update `explore_schema` output if it references `user` table
- [x] Test: `ls /users/` returns Charlotte Gong and other seeded customers
- [x] Test: chat with `user_id=charlotte_gong` injects her profile into the conversation
- [x] Test: distill endpoint updates `customer:charlotte_gong` context field

### Next: User Context Injection at Chat Start — DONE (profile + history)
**Priority**: High
**Goal**: When a user starts a chat, dynamically inject their profile, purchase history, and review history into the system prompt — so the agent knows who it's talking to from message #1.

Tasks:
- [x] On chat request with `user_id`, query customer record + recent orders + review history
- [x] Traverse graph: `customer->placed->order->contains->product` to get purchase history
- [x] Traverse graph: `customer->placed->order->has_review->review` to get their review history
- [x] Build a structured context block: name, profile_type, experience_level, skin concerns, recent purchases, distilled context
- [x] Inject this as a system message prefix (not user message) so the agent sees it naturally
- [x] Include graph entry points: "To find more about this user, start from `customer:{id}`"
- [x] Test: agent should greet Charlotte by name and reference her purchase history without any tool calls

### Next: Fix or Replace Graph Traversal Tool
**Priority**: High
**Goal**: The `graph_traverse` tool is currently confusing and low-value in practice. The agent uses it but the results don't meaningfully help answer user queries. Either make it genuinely useful (e.g., "customers who bought X also bought Y", ingredient safety chains, category drill-down) or remove it and let `surrealql_query` handle graph queries directly.

Tasks:
- [ ] Audit current graph_traverse usage in stress test logs — when does the agent call it, and does it actually help the response?
- [ ] Identify the 3-4 graph traversal patterns that would genuinely improve recommendations: `also_bought`, `contains_ingredient->related_to`, `supports_goal`
- [ ] Option A: Rewrite graph_traverse to focus on these high-value patterns with clear, useful output formatting
- [ ] Option B: Remove graph_traverse entirely, add graph query examples to `surrealql_query` docstring
- [ ] If keeping: make output human-readable ("Customers who bought [X] also bought: [Y], [Z]") not raw record dumps
- [ ] If keeping: add to the system prompt's GATHER phase as an explicit recommendation step
- [ ] Update frontend: hide raw graph traversal debug output, show only the natural language result
- [ ] Re-run smoke test to verify no regression

### Next: Evaluation Suite (DeepEval + LangSmith)
**Priority**: High
**Goal**: Add structured evaluation beyond the current stress test. The stress test checks pass/fail but doesn't measure quality dimensions like faithfulness, relevance, hallucination, or tool efficiency. Reference: `THG/chatbot` repo has a working DeepEval implementation.

Tasks:
- [ ] Review DeepEval implementation in `THG/chatbot` repo — extract patterns for metrics, test cases, dataset format
- [ ] Decide architecture: DeepEval for offline eval (faithfulness, hallucination, answer relevance) + LangSmith for runtime tracing. They complement, not compete
- [ ] Create `taro-api/tests/eval_suite.py` with DeepEval test cases derived from the 43 stress test queries
- [ ] Add metrics: faithfulness (did it use tool results?), answer relevance (did it answer the question?), hallucination (did it invent products?), tool selection accuracy
- [ ] Connect to LangSmith: ensure all chat traces are tagged with eval run IDs for correlation
- [ ] Add `make eval` target that runs the evaluation suite and outputs a summary report
- [ ] Compare eval scores across models (ties into multi-model optimisation task)
- [ ] Store eval results in `tasks/eval-results.md` for tracking over time

### Next: Observability & Self-Improvement Pipeline
**Priority**: Medium
**Goal**: Leverage LangSmith telemetry to create a feedback loop where the agent learns from past conversations. Batch-analyse chat logs to identify failure patterns, extract learned preferences, and feed them back into the system prompt or user context.

Tasks:
- [ ] Set up LangSmith dataset from production chat traces — export conversations with tool calls + outcomes
- [ ] Build a batch analysis script: pull recent traces, classify by outcome (success/partial/fail), extract failure patterns
- [ ] Create a `learned_patterns` table in SurrealDB: pattern, frequency, fix, source_trace_id
- [ ] Build a self-improvement sub-agent: reads recent failures from LangSmith, proposes prompt/tool improvements, writes to `learned_patterns`
- [ ] Option: give the main agent read access to `learned_patterns` via `ls /system/patterns/` route in fs_tools
- [ ] Option: spawn a review sub-agent post-conversation that scores the interaction and logs insights
- [ ] Add `failure_record` table: query, expected_behavior, actual_behavior, root_cause, resolution
- [ ] Feed high-frequency patterns back into system prompt updates (manual review gate)
- [ ] Add Makefile target: `make analyse` — runs batch analysis on last N traces

### Next: Multi-Agent Architecture Review
**Priority**: Medium
**Goal**: Evaluate whether our single `create_react_agent` with 9 tools is the right architecture, or if we should decompose into specialised sub-agents (e.g., search agent, recommendation agent, profile agent) for better context efficiency and separation of concerns. Currently one agent carries all tools and all context.

Tasks:
- [ ] Audit current token usage per chat request via LangSmith — how much context is the single agent consuming?
- [ ] Identify tool clusters that could be separate agents: (1) search/browse: ls, cat, find, grep, tree (2) recommend: graph_traverse, surrealql_query (3) external: web_search
- [ ] Research LangGraph multi-agent patterns: supervisor, hierarchical, swarm — which fits our use case?
- [ ] Prototype: split into a router agent + specialist sub-agents, compare quality and latency
- [ ] Evaluate tradeoffs: simpler single agent vs faster/cheaper multi-agent with context isolation
- [ ] Decision point: if single agent works well enough for demo, don't over-engineer. Document the finding either way
- [ ] If adopting multi-agent: update system prompts, tool assignments, and chat endpoint to route appropriately

### Next: Streaming + Visible Intermediate Reasoning — DONE
**Priority**: High
**Goal**: Make the agent feel *alive*. Stream responses via SSE so the user sees thinking steps, tool calls, and results in real-time — like watching Claude Code solve a problem. Implemented via `/chat/stream` + SSE in the frontend; `/chat` is kept for backwards compatibility.

**What the user should see** (per the spec):
```
🔍 Let me check your profile and purchase history...
[cat /users/emma_chen] → Emma, combination skin, goals: clear skin
💭 She's been getting breakouts — let me check her recent orders for possible causes...
[ls /users/emma_chen/orders/] → 3 recent orders
💭 Her last order had AHA/BHA — that's strong. Cross-referencing with her sensitivities...
✅ Based on your history, here's what I'd suggest...
```

Tasks:
- [x] Add SSE streaming endpoint: `POST /chat/stream` returning `text/event-stream` with structured event types
- [x] Define SSE event types: `thinking` (reasoning bubbles), `tool_start` / `tool_end` (tool name + args + timing), `token` (response text tokens), `done` / `error` (final state)
- [x] Implement LangGraph `astream_events()` handling to emit intermediate steps between tool calls
- [x] Add stream-of-thought instructions to system prompt: agent emits short reasoning summaries between tool calls (no full chain-of-thought)
- [x] Frontend: render SSE events as a live trace — thinking bubbles for `thinking`, collapsible cards for tool events, streaming text for `token`
- [x] Frontend: tool call cards show tool name + args in a compact format, with result details collapsible
- [x] Frontend: hide or collapse the old static debug badges in favor of the live reasoning/tool trace
- [x] Keep the existing blocking `POST /chat` endpoint for backwards compatibility and stress testing
- [x] Test: visible reasoning stream renders in real-time for a multi-tool-call query
- [x] Target: 2-5 visible thinking steps per complex query, each referencing specific data from the previous tool call

### BUG: Chat Product Card Modal Shows Empty/Boilerplate Data — FIXED
**Priority**: High
**Goal**: Clicking a product card rendered inside a chat response opens the detail modal but shows no title, price, rating, etc. — just the boilerplate loading state or empty fields. Products in the main grid modal work fine.

**Likely root cause**: The product `id` extracted from chat tool results may not match the format expected by `GET /products/{id}`. The extraction pipeline is:
1. `main.py:184-186` — parses tool message JSON, calls `_str_id()` to strip `product:` prefix
2. `chat.js:62` — renders card with `onclick="openProductDetail('${p.id}')"`
3. `api.js:40` — calls `GET /products/${productId}`
4. `main.py:346` — queries `SELECT * FROM product:\`${product_id}\``

**Possible failure points**:
- Tool results from `find`/`grep` may return `source_id` (a `documents` table ID) not `product` table ID — the `id` field maps to the wrong table
- `_str_id()` may produce an ID that doesn't match any `product` record (e.g., if the tool returned a document hash, not a product key)
- The API returns `{"error": "Product not found"}` which `fetchProductDetail` treats as valid data (no error check on response body)

Tasks:
- [x] Reproduce: send a chat query that returns product recommendations, click a product card, inspect browser console for the API response
- [x] Check: ensure `p.id` in the chat product card matches actual `product` IDs in SurrealDB (via `collect_product_ids_from_messages` + `fetch_products`)
- [x] Fix: normalise IDs from tool results and map them to `product` table IDs (using `str_id`) before sending to the frontend
- [x] Fix: `fetchProductDetail` checks for `data.error` and falls back to mock data or closes the modal gracefully instead of leaving boilerplate
- [x] Test: click product cards in chat — modal shows full product details matching what the agent recommended

### Next: Product Swipe Actions (Cart / Keep / Remove)
**Priority**: High
**Goal**: Add Tinder-style swipe actions to recommended product cards in chat. Each product card gets three actions: "Add to Cart" (love it), "Keep for Later" (neutral/interested), or "Remove" (not for me). These signals feed back into the conversation in real-time (so the agent refines its next recommendations) AND persist to the user's profile in SurrealDB (so future sessions learn from past preferences).

**UX vision**: Product cards in chat get a subtle action bar (swipe on mobile, buttons on desktop):
- **Cart** (green bag icon) — "I want this" → adds to a visible shopping cart sidebar/drawer
- **Keep** (bookmark icon) — "Interesting, save it" → stays visible, dimmed/bookmarked
- **Remove** (X icon) — "Not for me" → card fades out / collapses with a brief "Got it, noted" animation

**Data flow**:
1. User swipes/clicks → frontend sends `POST /preferences` with `{user_id, product_id, action: "cart"|"keep"|"remove", reason?: string}`
2. Backend persists to SurrealDB:
   - `cart`: `RELATE customer:{id}->wants->product:{id}` (new edge type)
   - `keep`: `RELATE customer:{id}->interested_in->product:{id}` (new edge type)
   - `remove`: `RELATE customer:{id}->rejected->product:{id} SET reason = $reason` (new edge type)
3. Within the current chat session: inject a system message like "User rejected [product X] — avoid similar products. User added [product Y] to cart — they like this direction." This steers the agent's next recommendations without a new user message.
4. On future sessions: load user's `wants`, `interested_in`, `rejected` edges during context injection so the agent knows their preferences from message #1.

Tasks:
- [x] Design action bar component for chat product cards — compact, accessible, works on desktop buttons
- [x] Add three new graph edge types to schema: `wants` (customer->product), `interested_in` (customer->product), `rejected` (customer->product with optional `reason` field)
- [x] Create `POST /preferences` endpoint: accepts `{user_id, product_id, action, reason?}`, creates/removes appropriate graph edges
- [x] Frontend: on "Cart" action → add to a shopping cart component (floating badge with count, expandable drawer showing carted items; drawer shows thumbnails, name, price, "View product" link; badge positioned above chat bubble, same size)
- [x] Frontend: on "Keep" action → visually bookmark the card (subtle highlight/icon change), keep visible in chat
- [x] Frontend: on "Remove" action → fade out card with micro-animation, optionally prompt "What didn't you like?" for the `reason` field
- [x] Backend: after preference action, inject a context message into the current thread so the agent adapts immediately (e.g., append to conversation as a system message)
- [x] Update user context injection (chat start) to load `wants`, `interested_in`, `rejected` edges and present as "User's preferences: likes [X, Y], not interested in [Z]"
- [x] Update `graph_traverse` or agent tools: agent should be able to query `customer->rejected->product` to avoid recommending disliked items
- [x] Add `ls /users/{id}/preferences/` route to fs_tools showing cart, saved, and rejected products
- [ ] Test: reject a product → next recommendation from agent avoids similar items
- [ ] Test: add to cart → cart persists across page refresh (via API, not just localStorage)

### Next: Conversation Persistence & History (PARTIAL)
**Priority**: High
**Goal**: Persist conversation history in SurrealDB so we have multi-turn continuity, can resume threads across reloads, and feed rich histories into distillation and analytics.

**Current state**:
- `graph.py`: still uses `MemorySaver` for LangGraph checkpointer (lost on restart)
- `conversation` table is defined in `schema.surql` and populated via `_save_conversation` in `routes/chat.py`
- Frontend persists `threadId` in `localStorage` and provides a "New Chat" button to start fresh threads

**Needs research** — best approach TBD. Options to investigate:
1. **Fix `langgraph-checkpoint-surrealdb`** for SurrealDB 3.0 — native LangGraph checkpointing persisted to SurrealDB. Cleanest if feasible.
2. **Custom SurrealDB checkpointer** — implement the `BaseCheckpointSaver` interface ourselves against SurrealDB 3.0. More work but full control.
3. **Hybrid: LangSmith tracing + SurrealDB storage** — LangSmith already captures full traces. Pull conversation logs from LangSmith API, persist summaries to SurrealDB. Less real-time but leverages existing infra.
4. **Simple per-turn persistence** — after each chat turn, write the message + response to a `conversation` table in SurrealDB. No checkpointer needed, just append-only log. Simplest but doesn't give LangGraph native history.

Tasks:
- [ ] Research: check if `langgraph-checkpoint-surrealdb` has a SurrealDB 3.0 compatible release or open PR
- [ ] Research: evaluate LangGraph's `BaseCheckpointSaver` interface — how much work to implement a custom SurrealDB 3.0 saver?
- [ ] Research: can LangSmith traces be pulled via API to reconstruct conversation history? What's the latency?
- [ ] Decide architecture: native checkpointer vs append-only conversation table vs LangSmith hybrid
- [x] Schema: design `conversation` table — thread_id, user_id, messages (array of {role, content, tool_calls, timestamp}), created_at, updated_at
- [x] Frontend: persist `thread_id` in localStorage so refreshing the page resumes the conversation
- [x] Frontend: add "New Chat" button that generates a fresh thread_id
- [ ] Frontend: add conversation history sidebar — list past threads by date/first message, click to resume
- [x] Backend: on chat request, load conversation history from SurrealDB if thread_id exists
- [x] Backend: after each turn, persist the new messages to SurrealDB
- [ ] Wire distill endpoint to read from persisted history (not just in-memory checkpointer)
- [ ] Test: restart server, send a message with a previous thread_id — agent should have full context
- [ ] Test: conversation history survives server restarts and page refreshes

### P2: Expandable Chat — Copilot Mode — DONE
**Priority**: P2
**Goal**: Add a toggle to expand the chat panel from the current compact sidebar into a full half-page copilot view. Implemented via `copilotMode` toggle, expanded chat layout, and persisted preference.

Tasks:
- [x] Add an expand/collapse toggle button to the chat header (icon: expand arrows)
- [x] Expanded mode: chat takes a larger portion of the page width, product grid shrinks to share space
- [x] Collapsed mode: returns to current floating chat bubble layout
- [x] Persist preference in localStorage so it remembers across page loads
- [x] Responsive: on mobile, expanded mode goes full-screen with a back button to return to the grid
- [x] Ensure product cards, tool trace cards, and swipe actions render well in the wider layout
- [x] Smooth CSS transition between modes (not a jarring jump)

### P2: Demo Polish
- [ ] Self-improvement logging (learned_pattern + failure_record tables)
- [ ] Analytics dashboard on tool usage patterns

### P3: Nice to Have
- [ ] Upgrade openai/langchain packages to latest for full gpt-5.4 support
- [ ] Add Gemini 3.1 to AVAILABLE_MODELS once langchain-google-genai supports it
- [ ] Prompt A/B testing framework (compare prompt variants per model)
- [ ] Automated regression testing in CI
