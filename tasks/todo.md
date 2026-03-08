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

### P2: Demo Polish
- [ ] Self-improvement logging (learned_pattern + failure_record tables)
- [ ] Analytics dashboard on tool usage patterns
- [ ] Streaming responses (SSE from /chat endpoint)

### P3: Nice to Have
- [ ] Upgrade openai/langchain packages to latest for full gpt-5.4 support
- [ ] Add Gemini 3.1 to AVAILABLE_MODELS once langchain-google-genai supports it
- [ ] Prompt A/B testing framework (compare prompt variants per model)
- [ ] Automated regression testing in CI
