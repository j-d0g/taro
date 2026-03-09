# Judge Feedback Loop Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a visible judge node to the LangGraph agent that evaluates every turn, writes learned patterns to SurrealDB, and notifies the frontend — creating a closed feedback loop visible in LangSmith Studio.

**Architecture:** Replace `create_react_agent` with a 2-node `StateGraph`: `agent` (existing ReAct subgraph) → `judge` (GPT-4o-mini evaluator). Judge writes to existing `learned_pattern`/`failure_record` tables. Frontend receives `learn` SSE event and shows brain-emoji notification. Agent reads patterns on next query via existing `ls /system/patterns/` route.

**Tech Stack:** LangGraph StateGraph, GPT-4o-mini (judge), SurrealDB, SSE events, existing frontend scaffolding.

---

### Task 1: Create `taro-api/src/judge.py` — Judge Module

**Files:**
- Create: `taro-api/src/judge.py`

**Step 1: Write the judge module**

```python
"""Per-turn judge that evaluates agent tool selection and response quality."""

import json
import os

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from loguru import logger

from db import get_db

# Use a fast, cheap model for judging
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-4o-mini")

JUDGE_PROMPT = """You are a tool-selection judge for an e-commerce search assistant.

Given a user query, the tools the agent called, and the final response, evaluate:
1. Did the agent pick the right tools? (find for search, cat for lookup, graph_traverse for relationships, etc.)
2. Was the response helpful and relevant?
3. Any errors or failures?

Tools available: ls, cat, find (hybrid search), grep (keyword), graph_traverse, surrealql_query, web_search, tree, explore_schema

Respond with ONLY valid JSON:
{
  "verdict": "success" | "partial" | "failure",
  "pattern_type": "<category: product_search | ingredient_query | graph_traversal | schema_explore | web_lookup | general>",
  "query_pattern": "<short description of query type, e.g. 'ingredient-based product search'>",
  "best_tool": "<which tool was most effective>",
  "insight": "<1 sentence human-readable insight for the frontend, e.g. 'Hybrid search effective for ingredient queries'>",
  "error": "<if failure, what went wrong; null otherwise>"
}"""


def _extract_turn_data(messages: list) -> dict:
    """Extract the last user query, tool calls, and response from message history."""
    query = ""
    tool_calls = []
    response = ""

    # Walk backwards to find the last exchange
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content and not response:
            response = msg.content if isinstance(msg.content, str) else str(msg.content)
        elif isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({"name": tc.get("name", "?"), "args": tc.get("args", {})})
        elif isinstance(msg, HumanMessage) and not query:
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            query = content[:500]  # Truncate long context-enriched messages
            break  # Found the user query, stop

    return {"query": query, "tool_calls": tool_calls, "response": response[:500]}


async def evaluate_turn(messages: list) -> dict | None:
    """Run the judge on the latest turn. Returns parsed verdict or None on error."""
    turn = _extract_turn_data(messages)
    if not turn["query"] or not turn["response"]:
        return None

    tool_summary = ", ".join(tc["name"] for tc in turn["tool_calls"]) or "none"

    judge_input = (
        f"User query: {turn['query']}\n"
        f"Tools called: {tool_summary}\n"
        f"Agent response: {turn['response']}"
    )

    try:
        llm = ChatOpenAI(model=JUDGE_MODEL, temperature=0)
        result = await llm.ainvoke([
            HumanMessage(content=JUDGE_PROMPT),
            HumanMessage(content=judge_input),
        ])
        parsed = json.loads(result.content.strip())
        logger.info(f"Judge verdict: {parsed.get('verdict')} — {parsed.get('insight')}")
        return parsed
    except Exception as e:
        logger.warning(f"Judge evaluation failed: {e}")
        return None


async def persist_verdict(verdict: dict) -> None:
    """Write judge verdict to learned_pattern or failure_record in SurrealDB."""
    try:
        async with get_db() as db:
            if verdict.get("verdict") in ("success", "partial"):
                # Upsert: increment success_count if pattern exists, else insert
                existing = await db.query(
                    "SELECT * FROM learned_pattern WHERE query_pattern = $qp AND best_tool = $bt LIMIT 1",
                    {"qp": verdict.get("query_pattern", ""), "bt": verdict.get("best_tool", "")},
                )
                if existing:
                    pid = existing[0].get("id")
                    await db.query(
                        f"UPDATE {pid} SET success_count += 1, insight = $insight",
                        {"insight": verdict.get("insight", "")},
                    )
                else:
                    await db.query(
                        "CREATE learned_pattern SET "
                        "pattern_type = $pt, query_pattern = $qp, best_tool = $bt, "
                        "success_count = 1, insight = $insight",
                        {
                            "pt": verdict.get("pattern_type", "general"),
                            "qp": verdict.get("query_pattern", ""),
                            "bt": verdict.get("best_tool", ""),
                            "insight": verdict.get("insight", ""),
                        },
                    )
            elif verdict.get("verdict") == "failure":
                await db.query(
                    "CREATE failure_record SET query = $q, tool_used = $t, error = $e",
                    {
                        "q": verdict.get("query_pattern", ""),
                        "t": verdict.get("best_tool", ""),
                        "e": verdict.get("error", "unknown"),
                    },
                )
    except Exception as e:
        logger.warning(f"Failed to persist judge verdict: {e}")
```

**Step 2: Verify module imports work**

Run: `cd /Users/jtran/Code/taro/taro-api && python -c "import src.judge; print('OK')"`
Expected: OK (no import errors)

---

### Task 2: Modify `graph.py` — Custom StateGraph with Judge Node

**Files:**
- Modify: `taro-api/src/graph.py`

**Step 1: Replace `create_react_agent` wrapper with custom StateGraph**

The key change: wrap the existing ReAct agent as a subgraph node, add judge as a second node.

```python
"""LangGraph agent with SurrealDB checkpointer and per-turn judge."""

import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import create_react_agent
from loguru import logger

from db import get_db_config
from judge import evaluate_turn, persist_verdict
from prompts.system import load_prompt
from tools import ALL_TOOLS

from langgraph_checkpoint_surrealdb import SurrealSaver

# Optional provider imports
try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
DEFAULT_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))


def get_llm(provider: str = DEFAULT_PROVIDER, model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE):
    """Return the appropriate LangChain chat model for the given provider."""
    provider = provider.lower()
    if provider == "openai":
        return ChatOpenAI(model=model, temperature=temperature)
    if provider == "anthropic":
        if ChatAnthropic is None:
            raise ImportError("Install langchain-anthropic: pip install langchain-anthropic")
        return ChatAnthropic(model=model, temperature=temperature)
    if provider == "google":
        if ChatGoogleGenerativeAI is None:
            raise ImportError("Install langchain-google-genai: pip install langchain-google-genai")
        return ChatGoogleGenerativeAI(model=model, temperature=temperature)
    raise ValueError(f"Unsupported LLM provider: {provider}. Use 'openai', 'anthropic', or 'google'.")


# ── Judge node ────────────────────────────────────────────

async def judge_node(state: MessagesState) -> dict:
    """Evaluate the latest turn and persist patterns to SurrealDB.

    Visible as a distinct node in LangSmith traces.
    """
    messages = state.get("messages", [])
    verdict = await evaluate_turn(messages)
    if verdict:
        await persist_verdict(verdict)
    # Don't modify messages — judge is observational only
    return {"messages": []}


# ── Graph builder ─────────────────────────────────────────

def build_graph(model_provider: str = None, model_name: str = None, temperature: float = None, prompt: str = None, use_checkpointer: bool = True):
    """Build agent → judge graph with optional checkpointer."""
    llm = get_llm(
        provider=model_provider or DEFAULT_PROVIDER,
        model=model_name or DEFAULT_MODEL,
        temperature=temperature if temperature is not None else DEFAULT_TEMPERATURE,
    )

    if use_checkpointer:
        try:
            db_config = get_db_config()
            checkpointer = SurrealSaver(
                url=db_config["url"],
                namespace=db_config["namespace"],
                database=db_config["database"],
                user=db_config["user"],
                password=db_config["password"],
            )
            logger.info("Using SurrealSaver for persistent checkpoints")
        except Exception as e:
            logger.warning(f"SurrealSaver failed, falling back to MemorySaver: {e}")
            checkpointer = MemorySaver()
    else:
        checkpointer = None

    # Inner ReAct agent (becomes a subgraph node)
    react_agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=prompt or load_prompt(),
    )

    # Outer graph: agent → judge
    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", react_agent)
    workflow.add_node("judge", judge_node)
    workflow.add_edge(START, "agent")
    workflow.add_edge("agent", "judge")
    workflow.add_edge("judge", END)

    agent = workflow.compile(checkpointer=checkpointer)
    logger.info(f"Built agent→judge graph with {len(ALL_TOOLS)} tools (checkpointer={'enabled' if use_checkpointer else 'platform-managed'})")
    return agent


_is_studio = os.getenv("LANGGRAPH_STORE_URI") is not None or "langgraph_api" in sys.modules
graph = build_graph(use_checkpointer=not _is_studio)
```

**Step 2: Run tests to verify graph builds correctly**

Run: `cd /Users/jtran/Code/taro/taro-api && make verify`
Expected: All existing tests pass (graph API unchanged — still has `.ainvoke()`, `.astream_events()`, `.aget_state()`)

---

### Task 3: Update Schema — Add `insight` field to `learned_pattern`

**Files:**
- Modify: `taro-api/schema/schema.surql:193-199`

**Step 1: Add insight field**

After `DEFINE FIELD success_count ON learned_pattern TYPE int DEFAULT 0;` add:
```sql
DEFINE FIELD insight ON learned_pattern TYPE option<string>;
```

**Step 2: Apply schema change**

Run: `cd /Users/jtran/Code/taro/taro-api && surreal import --conn http://localhost:8000 --user root --pass root --ns taro --db taro schema/schema.surql`

Or if that fails, manually:
```bash
cd /Users/jtran/Code/taro/taro-api && python -c "
import asyncio
from surrealdb import Surreal
async def run():
    db = Surreal('ws://localhost:8001/rpc')
    await db.signin({'user': 'root', 'pass': 'root'})
    await db.use('taro', 'taro')
    await db.query('DEFINE FIELD insight ON learned_pattern TYPE option<string>;')
    print('Done')
asyncio.run(run())
"
```

---

### Task 4: Update `_handle_list_patterns` to Show Insights

**Files:**
- Modify: `taro-api/src/tools/fs_tools.py:474-487`

**Step 1: Update the pattern display to include insights**

```python
async def _handle_list_patterns(db, verbose=False):
    """List learned tool-selection patterns and recent failures."""
    patterns = await db.query("SELECT * FROM learned_pattern ORDER BY success_count DESC LIMIT 20")
    failures = await db.query("SELECT * FROM failure_record ORDER BY created_at DESC LIMIT 10")
    patterns = patterns or []
    failures = failures or []

    lines = [f"Learned patterns ({len(patterns)}):"]
    for p in patterns:
        insight = p.get('insight', '')
        insight_str = f" — {insight}" if insight else ""
        lines.append(f"  [{p.get('pattern_type', '?')}] {p.get('query_pattern', '?')} -> {p.get('best_tool', '?')} (x{p.get('success_count', 0)}){insight_str}")
    lines.append(f"\nRecent failures ({len(failures)}):")
    for f in failures:
        lines.append(f"  {f.get('tool_used', '?')}: {f.get('error', '?')[:80]}")
    return "\n".join(lines)
```

---

### Task 5: Wire SSE Handler — Emit `learn` Event

**Files:**
- Modify: `taro-api/src/main.py:308-404`

**Step 1: Capture judge verdict from event stream and emit learn SSE**

In the `event_generator()` inside `chat_stream`, add detection of the judge node's completion and emit a `learn` event. The simplest approach: after the event loop, read the state for any verdict, OR intercept `on_chain_end` for the judge node.

Preferred approach — intercept judge events inline during streaming:

Add this inside the event loop (after the existing `elif` blocks):
```python
                # Catch judge node output
                elif kind == "on_chain_end":
                    metadata = event.get("metadata", {})
                    if metadata.get("langgraph_node") == "judge":
                        output = data.get("output", {})
                        msgs = output.get("messages", [])
                        # Judge doesn't add messages, but we can check
                        # if verdict was persisted by reading from events
                        pass  # Verdict already persisted in judge_node
```

Actually simpler — after the event loop completes (line 379, after the `async for` block), read back the latest learned pattern:

```python
            # Check if judge captured a new pattern
            try:
                async with get_db() as db:
                    latest = await db.query(
                        "SELECT insight, pattern_type, verdict FROM learned_pattern "
                        "ORDER BY created_at DESC LIMIT 1"
                    )
                    if latest and latest[0].get("insight"):
                        yield _sse("learn", {
                            "insight": latest[0]["insight"],
                            "type": latest[0].get("pattern_type", "success"),
                        })
            except Exception as learn_err:
                logger.debug(f"Learn event check failed: {learn_err}")
```

Place this between the event loop and the `done` event yield.

**IMPORTANT**: Also collect the response text during streaming so the judge has it. Add `response_tokens = []` at the top of `event_generator()`, and in the `on_chat_model_stream` handler, append: `response_tokens.append(content)`.

---

### Task 6: Frontend — Handle `learn` SSE Event in Streaming

**Files:**
- Modify: `taro-web/js/chat.js:350-372`

**Step 1: Add `learn` case to the streaming event handler and a method to the streaming message object**

In `createStreamingMessage()` return object, add a `showLearn(insight)` method:

```javascript
    showLearn(insight) {
      const learnDiv = document.createElement('div');
      learnDiv.className = 'self-improve';
      learnDiv.innerHTML = '&#129504; ' + escapeHtml(insight);
      msgDiv.appendChild(learnDiv);
      container.scrollTop = container.scrollHeight;
      // Update counter
      learnedCount++;
      document.getElementById('learnedCount').textContent = learnedCount;
    },
```

In `sendMessage()` streaming event handler (the `switch` block), add:
```javascript
          case 'learn':
            stream.showLearn(data.insight || 'Pattern captured');
            break;
```

---

### Task 7: Test End-to-End

**Step 1: Run unit tests**

Run: `cd /Users/jtran/Code/taro/taro-api && make verify`
Expected: All tests pass

**Step 2: Manual smoke test**

1. Restart API: `cd /Users/jtran/Code/taro/taro-api && make restart`
2. Open frontend at `http://localhost:3001`
3. Send: "recommend a hydrating moisturizer"
4. Verify: Response streams normally, brain emoji notification appears below the response
5. Check LangSmith: Two nodes visible — `agent` → `judge`
6. Check DB: `SELECT * FROM learned_pattern` should have 1+ rows
7. Send second query: "what about for oily skin?"
8. Verify: Agent can read patterns via `ls /system/patterns/`

**Step 3: Commit**

```bash
git add taro-api/src/judge.py taro-api/src/graph.py taro-api/src/main.py taro-api/src/tools/fs_tools.py taro-api/schema/schema.surql taro-web/js/chat.js
git commit -m "feat: add judge feedback loop — visible agent→judge graph in LangSmith

Per-turn GPT-4o-mini judge evaluates tool selection and response quality,
writes learned patterns to SurrealDB, emits SSE learn events to frontend.
Agent reads accumulated patterns via ls /system/patterns/ on next query."
```

---

## Architecture Diagram

```
User Query
    │
    ▼
┌─────────────┐     SSE: tool_start, tool_end, token
│   agent      │────────────────────────────────────────► Frontend
│  (ReAct)     │
└──────┬───────┘
       │
       ▼
┌─────────────┐     SSE: learn {insight: "..."}
│   judge      │────────────────────────────────────────► Frontend
│ (GPT-4o-mini)│
└──────┬───────┘
       │
       ▼
┌─────────────────────────┐
│  SurrealDB              │
│  learned_pattern table  │◄──── Agent reads on next query
│  failure_record table   │      via ls /system/patterns/
└─────────────────────────┘
```

## What Already Exists (no changes needed)
- `learned_pattern` + `failure_record` tables in schema (just add `insight` field)
- `_handle_list_patterns()` in fs_tools.py reads from these tables
- `ls /system/patterns/` route dispatches to the handler
- Frontend `.self-improve` CSS class styled with purple brain emoji
- `learnedCount` counter in chat stats bar
- `addMessage()` accepts `learnMsg` parameter
- LangSmith tracing enabled in .env
