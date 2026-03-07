.PHONY: install serve studio seed surrealdb health test verify

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
	curl -s http://localhost:8000/health | python -m json.tool

# Test chat
test-chat:
	curl -s -X POST http://localhost:8000/chat \
		-H 'Content-Type: application/json' \
		-d '{"message":"recommend a protein powder"}' | python -m json.tool
