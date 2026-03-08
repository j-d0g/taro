# Restart API Agent

Kill and restart the Taro.ai FastAPI server from the current source code.

## Tools
Bash

## Instructions

You restart the Taro.ai API server. Steps:

1. Kill any existing process on port 8002:
   ```
   lsof -i :8002 -t 2>/dev/null | xargs kill -9 2>/dev/null
   ```

2. Wait for port to be free:
   ```
   sleep 2
   lsof -i :8002 -t 2>/dev/null || echo "port free"
   ```

3. Start the API from the correct directory:
   ```
   cd taro-api/src && nohup python -m uvicorn main:app --host 0.0.0.0 --port 8002 --timeout-keep-alive 300 > /tmp/taro-api.log 2>&1 &
   ```

4. Wait and verify:
   ```
   sleep 5 && curl -s http://localhost:8002/health
   ```

5. If health check fails, read `/tmp/taro-api.log` for errors and report them.

Always confirm success with the health check response and PID.
