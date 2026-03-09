.PHONY: install serve studio seed surrealdb health test verify eval eval-basic smoke stress restart test-chat test-distill traces frontend help

# Show all available commands
help:
	@echo ""
	@echo "  Taro.ai Makefile"
	@echo "  ════════════════════════════════════════════"
	@echo ""
	@echo "  Setup"
	@echo "    make install        Install Python dependencies"
	@echo "    make surrealdb      Start SurrealDB (in-memory)"
	@echo "    make seed           Seed DB with sample data"
	@echo ""
	@echo "  Run"
	@echo "    make serve          Start FastAPI server (foreground)"
	@echo "    make restart        Restart API in background"
	@echo "    make frontend       Start frontend on :3001"
	@echo "    make studio         Start LangGraph Studio"
	@echo ""
	@echo "  Test"
	@echo "    make verify         Unit tests (89 tests, ~1s)"
	@echo "    make smoke          Quick smoke test (3 queries, ~1min)"
	@echo "    make stress         Full stress test (43 queries, ~20min)"
	@echo "    make eval-basic     Eval suite, basic assertions (10 queries, ~5min)"
	@echo "    make eval           Eval suite, DeepEval LLM-as-judge"
	@echo ""
	@echo "  Tools"
	@echo "    make health         API health check"
	@echo "    make test-chat      Quick chat test"
	@echo "    make test-distill   Test memory distillation flow"
	@echo "    make traces         Analyse LangSmith traces"
	@echo "    make conversations  List persisted conversations"
	@echo ""

# Install dependencies
install:
	pip install -r requirements.txt

# Run all tests
test:
	cd src && python -m pytest ../tests/ -v

# Verify everything (syntax + imports + tests) -- used by Stop hook
verify: test
	@echo "All checks passed."

# Start FastAPI server
serve:
	cd src && python main.py

# Start LangGraph Studio
studio:
	langgraph dev --port 2024

# Seed SurrealDB with sample data
seed:
	python schema/seed.py

# Start SurrealDB (in-memory)
surrealdb:
	surreal start --user root --pass root memory

# Health check
health:
	curl -s http://localhost:8002/health | python -m json.tool

# Test chat
test-chat:
	curl -s -X POST http://localhost:8002/chat \
		-H 'Content-Type: application/json' \
		-d '{"message":"recommend a protein powder"}' | python -m json.tool

# Restart the API server (kill old, start fresh, verify health)
restart:
	@echo "Restarting API..."
	@lsof -i :8002 -t 2>/dev/null | xargs kill -9 2>/dev/null || true
	@sleep 2
	@cd src && nohup python -m uvicorn main:app --host 0.0.0.0 --port 8002 --timeout-keep-alive 300 > /tmp/taro-api.log 2>&1 &
	@sleep 5
	@curl -sf http://localhost:8002/health > /dev/null && echo "API healthy on :8002" || (echo "FAILED - check /tmp/taro-api.log"; cat /tmp/taro-api.log | tail -10; exit 1)

# Run DeepEval evaluation suite (10 test cases, ~5 min)
eval:
	@echo "=== Evaluation Suite (DeepEval) ==="
	@curl -sf http://localhost:8002/health > /dev/null || (echo "API not running. Run: make restart"; exit 1)
	@python -c "import deepeval" 2>/dev/null || (echo "deepeval not installed. Run: pip install deepeval"; exit 1)
	@export $$(grep OPENAI_API_KEY config/.env | xargs) && deepeval test run tests/eval_suite.py -v

# Run eval suite without DeepEval (basic assertions only)
eval-basic:
	@echo "=== Evaluation Suite (basic mode) ==="
	@curl -sf http://localhost:8002/health > /dev/null || (echo "API not running. Run: make restart"; exit 1)
	python -u tests/eval_suite.py

# Run adversarial stress test (restarts API first to ensure fresh code)
stress: restart
	@echo "Running stress test (43 queries, ~20 min)..."
	python -u tests/stress_test_harness.py

# Quick smoke test: 3 representative queries
smoke:
	@echo "=== Smoke test ==="
	@curl -sf http://localhost:8002/health > /dev/null || (echo "API not running. Run: make restart"; exit 1)
	@echo "1. Product search (find)..."
	@curl -s --max-time 120 -X POST http://localhost:8002/chat -H 'Content-Type: application/json' \
		-d '{"message":"recommend a protein powder"}' | python -c "import sys,json;d=json.load(sys.stdin);t=[c['name'] for c in d.get('tool_calls',[])];print(f'  Tools: {t}');print(f'  Pass: {\"find\" in t}')"
	@echo "2. Graph traversal..."
	@curl -s --max-time 120 -X POST http://localhost:8002/chat -H 'Content-Type: application/json' \
		-d '{"message":"What categories exist?"}' | python -c "import sys,json;d=json.load(sys.stdin);t=[c['name'] for c in d.get('tool_calls',[])];print(f'  Tools: {t}');print(f'  Pass: {len(t) > 0}')"
	@echo "3. Schema awareness..."
	@curl -s --max-time 120 -X POST http://localhost:8002/chat -H 'Content-Type: application/json' \
		-d '{"message":"What tables exist in the database?"}' | python -c "import sys,json;d=json.load(sys.stdin);t=[c['name'] for c in d.get('tool_calls',[])];print(f'  Tools: {t}');print(f'  Pass: {\"explore_schema\" in t or \"ls\" in t}')"
	@echo "=== Done ==="

# Test memory distillation
test-distill:
	@echo "1. Chat with user context..."
	@curl -s --max-time 120 -X POST http://localhost:8002/chat -H 'Content-Type: application/json' \
		-d '{"message":"I want vegan protein for muscle building","user_id":"diego_carvalho","thread_id":"make-test-distill"}' \
		| python -c "import sys,json;d=json.load(sys.stdin);print(f'Reply: {d[\"reply\"][:150]}')"
	@echo "2. Distilling..."
	@curl -s --max-time 120 -X POST http://localhost:8002/distill -H 'Content-Type: application/json' \
		-d '{"thread_id":"make-test-distill","user_id":"diego_carvalho"}' \
		| python -c "import sys,json;d=json.load(sys.stdin);print(f'Context: {d[\"context\"][:200]}');print(f'Updated: {d[\"updated\"]}')"

# Analyse LangSmith traces
traces:
	python scripts/analyse_traces.py

# Start frontend dev server
frontend:
	@lsof -i :3001 -t 2>/dev/null | xargs kill -9 2>/dev/null || true
	@sleep 1
	@cd ../taro-web && python -m http.server 3001 > /tmp/taro-web.log 2>&1 &
	@sleep 1
	@echo "Frontend running on http://localhost:3001"

# List persisted conversations
conversations:
	@curl -sf http://localhost:8002/conversations 2>/dev/null \
		| python -c "import sys,json;cs=json.loads(sys.stdin.buffer.read());print(f'{len(cs)} conversations:');[print(f'  {c[\"thread_id\"]:40s}  msgs={c[\"message_count\"]}  user={c.get(\"user_id\") or \"anon\"}') for c in cs]" \
		|| echo "API not running. Run: make restart"
