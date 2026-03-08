"""Per-turn judge: evaluates agent tool selection quality after each turn.

Extracts the last user query, tool calls, and agent response from LangGraph
message history, then asks a cheap model to score the turn. Persists results
to SurrealDB for self-improvement.
"""

import json
import os

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from loguru import logger

from db import get_db

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-5.4")

TOOLS_AVAILABLE = [
    "ls", "cat", "find", "grep", "graph_traverse",
    "surrealql_query", "web_search", "tree", "explore_schema",
]

JUDGE_PROMPT = """\
You are a tool-selection judge for an e-commerce chatbot agent.

The agent has these tools: {tools}

Given the user query, the tools the agent called, and the final response,
evaluate whether the agent picked the right tools.

User query: {query}
Tools called: {tools_called}
Agent response (truncated): {response}

Respond with ONLY valid JSON (no markdown fences):
{{
  "verdict": "success" | "partial" | "failure",
  "pattern_type": "<category: product_search | graph_query | recommendation | general_info | comparison>",
  "query_pattern": "<short abstracted pattern, e.g. 'find products by ingredient'>",
  "best_tool": "<which tool was most appropriate>",
  "insight": "<1-sentence human-readable takeaway>",
  "error": "<description if failure, else null>"
}}
"""


def _extract_turn_data(messages: list) -> dict | None:
    """Walk messages backwards to extract the last complete turn.

    A turn is: HumanMessage -> (AIMessage with tool_calls -> ToolMessages)* -> AIMessage (final).
    Returns dict with query, tools_called, response, or None if not enough data.
    """
    if len(messages) < 2:
        return None

    # Find the final AI response (last AIMessage without tool_calls)
    response_text = None
    tools_called = []
    query = None

    # Walk backwards
    i = len(messages) - 1

    # 1. Find final AI response
    while i >= 0:
        msg = messages[i]
        if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
            response_text = msg.content[:500] if msg.content else ""
            i -= 1
            break
        i -= 1

    if response_text is None:
        return None

    # 2. Collect tool calls (walk past ToolMessages and AIMessages with tool_calls)
    while i >= 0:
        msg = messages[i]
        if isinstance(msg, ToolMessage):
            i -= 1
            continue
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                tools_called.append(tc.get("name", "unknown"))
            i -= 1
            continue
        break  # Hit something else (should be HumanMessage)

    # 3. Find the user query
    while i >= 0:
        msg = messages[i]
        if isinstance(msg, HumanMessage):
            query = msg.content[:300] if isinstance(msg.content, str) else str(msg.content)[:300]
            break
        i -= 1

    if not query:
        return None

    return {
        "query": query,
        "tools_called": tools_called,
        "response": response_text,
    }


async def evaluate_turn(messages: list) -> dict | None:
    """Evaluate the last agent turn. Returns verdict dict or None on error."""
    turn = _extract_turn_data(messages)
    if not turn:
        logger.debug("Judge: not enough turn data to evaluate")
        return None

    try:
        llm = ChatOpenAI(model=JUDGE_MODEL, temperature=0, reasoning_effort="low")
        prompt = JUDGE_PROMPT.format(
            tools=", ".join(TOOLS_AVAILABLE),
            query=turn["query"],
            tools_called=", ".join(turn["tools_called"]) or "(none)",
            response=turn["response"],
        )

        result = await llm.ainvoke([HumanMessage(content=prompt)])
        raw = result.content.strip()

        # Strip markdown fences if the model wraps anyway
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        verdict = json.loads(raw)
        logger.info(f"Judge verdict: {verdict.get('verdict')} — {verdict.get('insight', '')}")

        await persist_verdict(verdict)
        return verdict

    except Exception as e:
        logger.warning(f"Judge evaluation failed: {e}")
        return None


async def persist_verdict(verdict: dict) -> None:
    """Write judge verdict to SurrealDB.

    - success/partial -> upsert learned_pattern (increment success_count if exists)
    - failure -> insert failure_record
    """
    try:
        async with get_db() as db:
            if verdict.get("verdict") in ("success", "partial"):
                # Check for existing pattern with same query_pattern + best_tool
                existing = await db.query(
                    "SELECT * FROM learned_pattern "
                    "WHERE query_pattern = $qp AND best_tool = $bt LIMIT 1",
                    {"qp": verdict.get("query_pattern", ""), "bt": verdict.get("best_tool", "")},
                )

                if existing:
                    record = existing[0]
                    rid = record["id"]
                    new_count = record.get("success_count", 0) + 1
                    await db.query(
                        "UPDATE $rid SET success_count = $count, insight = $insight",
                        {"rid": rid, "count": new_count, "insight": verdict.get("insight", "")},
                    )
                    logger.debug(f"Judge: updated learned_pattern {rid} (count={new_count})")
                else:
                    await db.query(
                        "CREATE learned_pattern SET "
                        "pattern_type = $pt, query_pattern = $qp, best_tool = $bt, "
                        "success_count = 1, insight = $insight, created_at = time::now()",
                        {
                            "pt": verdict.get("pattern_type", "unknown"),
                            "qp": verdict.get("query_pattern", ""),
                            "bt": verdict.get("best_tool", ""),
                            "insight": verdict.get("insight", ""),
                        },
                    )
                    logger.debug("Judge: created new learned_pattern")

            elif verdict.get("verdict") == "failure":
                await db.query(
                    "CREATE failure_record SET "
                    "query = $q, tool_used = $tu, error = $err, created_at = time::now()",
                    {
                        "q": verdict.get("query_pattern", ""),
                        "tu": verdict.get("best_tool", ""),
                        "err": verdict.get("error", "unknown error"),
                    },
                )
                logger.debug("Judge: recorded failure")

    except Exception as e:
        logger.warning(f"Judge: failed to persist verdict: {e}")
