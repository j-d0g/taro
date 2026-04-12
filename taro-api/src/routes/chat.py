"""Chat endpoints: POST /chat, POST /chat/stream."""

import json
import os
import time

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from loguru import logger

import db
from agent import get_agent, build_message_content
from helpers import (
    collect_product_ids_from_messages,
    collect_product_ids_from_text,
    fetch_products,
    sse,
)
from models import ChatRequest, ChatResponse


router = APIRouter()

# LangGraph default is 25; override only if needed (prefer prompt/tool fixes over raising this).
_AGENT_RECURSION_LIMIT = int(os.getenv("AGENT_RECURSION_LIMIT", "25"))


def _agent_config(thread_id: str) -> dict:
    return {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": _AGENT_RECURSION_LIMIT,
    }


async def _load_conversation(conn, thread_id: str) -> list[dict]:
    """Load conversation messages from SurrealDB."""
    result = await conn.query(
        "SELECT messages FROM conversation WHERE thread_id = $tid",
        {"tid": thread_id},
    )
    if result and isinstance(result[0], dict):
        return result[0].get("messages", [])
    return []


async def _save_conversation(conn, thread_id: str, user_id: str | None, user_msg: str, assistant_msg: str, tool_calls: list[dict]):
    """Append messages to conversation in SurrealDB."""
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    new_messages = [
        {"role": "user", "content": user_msg, "timestamp": now},
        {"role": "assistant", "content": assistant_msg, "tool_calls": tool_calls, "timestamp": now},
    ]

    # Upsert: create or append
    existing = await conn.query(
        "SELECT id, messages FROM conversation WHERE thread_id = $tid",
        {"tid": thread_id},
    )

    if existing and isinstance(existing[0], dict) and "id" in existing[0]:
        # Append to existing
        old_messages = existing[0].get("messages", [])
        all_messages = old_messages + new_messages
        conv_id = str(existing[0]["id"])
        await conn.query(
            f"UPDATE {conv_id} SET messages = $msgs, updated_at = time::now()",
            {"msgs": all_messages},
        )
    else:
        # Create new
        await conn.query(
            "CREATE conversation SET thread_id = $tid, user_id = $uid, "
            "messages = $msgs, created_at = time::now(), updated_at = time::now()",
            {"tid": thread_id, "uid": user_id, "msgs": new_messages},
        )


async def append_preference_context(conn, thread_id: str, user_id: str | None, product_id: str, product_name: str | None, action: str, reason: str | None) -> None:
    """Append a single preference-update message to the conversation so the agent sees it on next turn."""
    import datetime
    name = product_name or product_id
    if action == "cart":
        content = f"[Preference: User added {name} to cart — they like this direction.]"
    elif action == "keep":
        content = f"[Preference: User saved {name} for later — interested.]"
    else:
        part = f"[Preference: User removed {name} from recommendations — avoid similar."
        if reason:
            part += f" Reason: {reason[:100]}."
        part += "]"
        content = part
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    new_msg = {"role": "user", "content": content, "timestamp": now}
    existing = await conn.query(
        "SELECT id, messages FROM conversation WHERE thread_id = $tid",
        {"tid": thread_id},
    )
    if existing and isinstance(existing[0], dict) and "id" in existing[0]:
        old_messages = existing[0].get("messages", [])
        all_messages = old_messages + [new_msg]
        conv_id = str(existing[0]["id"])
        await conn.query(
            f"UPDATE {conv_id} SET messages = $msgs, updated_at = time::now()",
            {"msgs": all_messages},
        )
    else:
        await conn.query(
            "CREATE conversation SET thread_id = $tid, user_id = $uid, "
            "messages = $msgs, created_at = time::now(), updated_at = time::now()",
            {"tid": thread_id, "uid": user_id, "msgs": [new_msg]},
        )


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat (slow: full agent run)",
    description=(
        "Runs the LangGraph ReAct agent (LLM + SurrealDB tools). "
        "Expect **30s–several minutes** per request; Swagger stays on “Loading” until the full reply is ready. "
        "Watch the API terminal for progress. If it never finishes, check OPENAI_API_KEY, SurrealDB, and network."
    ),
)
async def chat(request: ChatRequest):
    """Send a message to the chatbot."""
    logger.info(f"Chat request: thread={request.thread_id}, message='{request.message[:80]}'")

    try:
        agent = get_agent(request.model_provider, request.model_name, request.prompt_id)

        config = _agent_config(request.thread_id)

        # Load persisted history for this thread (if any) and prepend as a short summary.
        history_prefix = ""
        try:
            async with db.get_db() as conn:
                past = await _load_conversation(conn, request.thread_id)
            if past:
                # Build a compact textual summary of the last few turns
                lines = []
                for m in past[-10:]:
                    role = m.get("role", "")
                    content = str(m.get("content", ""))[:200]
                    if content:
                        lines.append(f"{role}: {content}")
                if lines:
                    history_prefix = "Previous conversation:\n" + "\n".join(lines) + "\n\n"
        except Exception as hist_err:
            logger.warning(f"Failed to load persisted conversation for thread {request.thread_id}: {hist_err}")

        message_content = await build_message_content(request.message, request.user_id)
        full_content = history_prefix + message_content
        input_msg = {"messages": [HumanMessage(content=full_content)]}

        result = await agent.ainvoke(input_msg, config=config)

        # Extract final response
        messages = result.get("messages", [])
        reply = messages[-1].content if messages else "I couldn't generate a response."

        # Extract tool calls from message history
        tool_calls = []
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls.append({"name": tc.get("name", ""), "args": tc.get("args", {})})

        # Observability: log when find/grep returns citeable policy chunks
        for msg in messages:
            name = getattr(msg, "name", "") or ""
            if name in ("find", "grep"):
                text = str(getattr(msg, "content", ""))
                if "source_key:" in text:
                    logger.info(f"retrieval_citation: tool={name} (policy/help chunk in output)")

        # Extract product data from tool calls and tool outputs
        product_ids = collect_product_ids_from_messages(messages)
        products = await fetch_products(product_ids)

        # Persist conversation
        try:
            async with db.get_db() as conn:
                await _save_conversation(
                    conn, request.thread_id, request.user_id,
                    request.message, reply, tool_calls,
                )
        except Exception as save_err:
            logger.warning(f"Failed to save conversation: {save_err}")

        return ChatResponse(reply=reply, thread_id=request.thread_id, tool_calls=tool_calls, products=products)
    except Exception as e:
        import traceback
        error_type = type(e).__name__
        logger.error(f"Chat error ({error_type}): {e}\n{traceback.format_exc()}")

        # Retry once on rate limit errors
        if "RateLimit" in error_type or "rate_limit" in str(e).lower():
            import asyncio
            logger.info("Rate limited, retrying after 5s backoff...")
            await asyncio.sleep(5)
            try:
                result = await agent.ainvoke(input_msg, config=config)
                messages = result.get("messages", [])
                reply = messages[-1].content if messages else "I couldn't generate a response."
                tool_calls = []
                for msg in messages:
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            tool_calls.append({"name": tc.get("name", ""), "args": tc.get("args", {})})
                return ChatResponse(reply=reply, thread_id=request.thread_id, tool_calls=tool_calls)
            except Exception as retry_err:
                logger.error(f"Retry also failed: {retry_err}")

        return ChatResponse(
            reply=f"I encountered an error processing your request: {error_type}. Please try again.",
            thread_id=request.thread_id,
            tool_calls=[],
        )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream agent response via Server-Sent Events.

    Emits events: thinking, tool_start, tool_end, token, done.
    """
    logger.info(f"Stream request: thread={request.thread_id}, message='{request.message[:80]}'")

    agent = get_agent(request.model_provider, request.model_name, request.prompt_id)
    config = _agent_config(request.thread_id)

    # Load persisted history for this thread (if any) and prepend as a short summary.
    history_prefix = ""
    try:
        async with db.get_db() as conn:
            past = await _load_conversation(conn, request.thread_id)
        if past:
            lines = []
            for m in past[-10:]:
                role = m.get("role", "")
                content = str(m.get("content", ""))[:200]
                if content:
                    lines.append(f"{role}: {content}")
            if lines:
                history_prefix = "Previous conversation:\n" + "\n".join(lines) + "\n\n"
    except Exception as hist_err:
        logger.warning(f"Failed to load persisted conversation for stream thread {request.thread_id}: {hist_err}")

    message_content = await build_message_content(request.message, request.user_id)
    full_content = history_prefix + message_content
    input_msg = {"messages": [HumanMessage(content=full_content)]}

    async def event_generator():
        tool_calls = []
        seen_product_ids: set[str] = set()
        collected_product_ids: list[str] = []
        active_tools = {}  # run_id -> start_time

        learn_insight = None  # Captured from judge node
        import datetime as _dt
        turn_start = _dt.datetime.now(_dt.timezone.utc).isoformat()

        try:
            async for event in agent.astream_events(input_msg, config=config, version="v2"):
                kind = event.get("event", "")
                name = event.get("name", "")
                run_id = event.get("run_id", "")
                data = event.get("data", {})
                metadata = event.get("metadata", {})

                # Skip events from the judge node (its LLM call is internal)
                if metadata.get("langgraph_node") == "judge":
                    continue

                if kind == "on_tool_start":
                    tool_input = data.get("input", {})
                    active_tools[run_id] = time.time()
                    tool_calls.append({"name": name, "args": tool_input})
                    yield sse("tool_start", {
                        "id": run_id,
                        "name": name,
                        "args": tool_input,
                    })

                    # Extract from cat /products/{id} args
                    if name == "cat":
                        path = tool_input.get("path", "")
                        if path.startswith("/products/"):
                            pid = path.replace("/products/", "").strip("/")
                            if pid and pid not in seen_product_ids:
                                seen_product_ids.add(pid)
                                collected_product_ids.append(pid)

                elif kind == "on_tool_end":
                    start = active_tools.pop(run_id, None)
                    duration_ms = int((time.time() - start) * 1000) if start else 0
                    yield sse("tool_end", {
                        "id": run_id,
                        "name": name,
                        "duration_ms": duration_ms,
                    })
                    # Extract product IDs from tool output text
                    output = data.get("output", "")
                    if isinstance(output, str):
                        new_ids = collect_product_ids_from_text(output, seen_product_ids)
                        collected_product_ids.extend(new_ids)

                elif kind == "on_chat_model_end":
                    # Extract reasoning summaries from models that support it
                    message = data.get("output")
                    if message:
                        # GPT-5.x: reasoning in content_blocks
                        content_blocks = getattr(message, "content_blocks", None)
                        if content_blocks:
                            for block in content_blocks:
                                if isinstance(block, dict) and block.get("type") == "reasoning":
                                    text = block.get("reasoning", "")
                                    if isinstance(text, list):
                                        text = " ".join(
                                            s.get("text", "") for s in text
                                            if isinstance(s, dict)
                                        )
                                    if text:
                                        yield sse("thinking", {"content": text})
                        # Claude: reasoning in additional_kwargs
                        elif hasattr(message, "additional_kwargs"):
                            reasoning = message.additional_kwargs.get("reasoning_content")
                            if reasoning:
                                yield sse("thinking", {"content": str(reasoning)})

                elif kind == "on_chat_model_stream":
                    chunk = data.get("chunk")
                    if chunk is None:
                        continue
                    content = getattr(chunk, "content", "")
                    tool_chunks = getattr(chunk, "tool_call_chunks", [])

                    if not content or tool_chunks:
                        continue

                    # Responses API: content is a list of content blocks
                    if isinstance(content, list):
                        for block in content:
                            if not isinstance(block, dict):
                                continue
                            btype = block.get("type", "")
                            if btype == "reasoning":
                                # Reasoning block — extract summary text
                                summaries = block.get("summary", [])
                                if summaries:
                                    text = " ".join(
                                        s.get("text", "") for s in summaries
                                        if isinstance(s, dict) and s.get("text")
                                    )
                                    if text:
                                        yield sse("thinking", {"content": text})
                            elif btype == "text":
                                text = block.get("text", "")
                                if text:
                                    yield sse("token", {"content": text})
                    # Chat Completions API: content is a plain string
                    elif isinstance(content, str):
                        yield sse("token", {"content": content})

            # Fetch structured product data for all collected IDs
            products = await fetch_products(collected_product_ids)

            # Check if judge captured a new insight
            try:
                async with db.get_db() as conn:
                    latest = await conn.query(
                        "SELECT insight, pattern_type, created_at FROM learned_pattern "
                        "WHERE created_at >= type::datetime($ts) "
                        "ORDER BY created_at DESC LIMIT 1",
                        {"ts": turn_start},
                    )
                    if latest and latest[0].get("insight"):
                        learn_insight = latest[0]["insight"]
                        yield sse("learn", {
                            "insight": learn_insight,
                            "type": latest[0].get("pattern_type", "success"),
                        })
            except Exception as learn_err:
                logger.debug(f"Learn event check failed: {learn_err}")

            # Final done event with aggregated data
            yield sse("done", {
                "thread_id": request.thread_id,
                "tool_calls": tool_calls,
                "products": products,
            })

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Stream error ({error_type}): {e}")
            products = await fetch_products(collected_product_ids)
            yield sse("error", {"message": str(e), "type": error_type})
            yield sse("done", {
                "thread_id": request.thread_id,
                "tool_calls": tool_calls,
                "products": products,
            })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
