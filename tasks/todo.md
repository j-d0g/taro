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

### P2: Demo Polish
- [ ] Self-improvement logging (learned_pattern + failure_record tables)
- [ ] Analytics dashboard on tool usage patterns
- [ ] Streaming responses (SSE from /chat endpoint)

### P3: Nice to Have
- [ ] Upgrade openai/langchain packages to latest for full gpt-5.4 support
- [ ] Add Gemini 3.1 to AVAILABLE_MODELS once langchain-google-genai supports it
- [ ] Prompt A/B testing framework (compare prompt variants per model)
- [ ] Automated regression testing in CI
