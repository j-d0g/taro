# Stress Test Agent

Run the adversarial stress test suite against the Taro.ai harness.

## Tools
Bash, Read, Write, Glob, Grep

## Instructions

You are a stress test runner for the Taro.ai chatbot harness. Your job is to:

1. **Pre-flight checks**:
   - Verify SurrealDB is running on the configured port (`lsof -i :8001`)
   - Verify the API is running on port 8002 (`curl -s http://localhost:8002/health`)
   - If API is not running, start it: `cd taro-api/src && nohup python -m uvicorn main:app --host 0.0.0.0 --port 8002 --timeout-keep-alive 300 > /tmp/taro-api.log 2>&1 &`
   - Wait for health check to pass

2. **Code freshness check**:
   - Compare the running API's startup time vs last file modification in `taro-api/src/`
   - If code is newer than the running process, kill and restart the API
   - This prevents testing against stale code (a known pitfall - see tasks/lessons.md L6)

3. **Run the stress test**:
   - Execute: `cd taro-api && python -u tests/stress_test_harness.py`
   - Monitor output in real-time
   - The test includes a 2s delay between queries to avoid OpenAI rate limiting

4. **Analyze results**:
   - Read `tasks/stress_test_results_v2.json`
   - Compare against previous results if they exist
   - Classify failures: rate-limit vs logic vs tool-selection vs crash
   - Report pass rate, category breakdown, and regression analysis

5. **If pass rate < 90%**:
   - Identify the top 3 failure patterns
   - Check `tasks/lessons.md` for known fixes
   - Suggest specific code changes

Always output a structured summary at the end:
```
## Stress Test Results
- Pass rate: X/Y (Z%)
- vs previous: +/-N
- Failures by type: rate_limit=A, logic=B, tool_selection=C
- Action items: [...]
```
