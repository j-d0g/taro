"""Conversation endpoints: GET /conversations, GET /conversations/{thread_id}, POST /distill."""

from typing import Optional

from fastapi import APIRouter
from loguru import logger

import db
from agent import get_agent
from graph import get_llm
from helpers import str_id
from models import DistillRequest, DistillResponse
from routes.chat import _load_conversation


router = APIRouter()


@router.get("/conversations/{thread_id}")
async def get_conversation(thread_id: str):
    """Get conversation history by thread ID."""
    async with db.get_db() as conn:
        result = await conn.query(
            "SELECT * FROM conversation WHERE thread_id = $tid",
            {"tid": thread_id},
        )
        if not result:
            return {"error": "Conversation not found"}
        conv = result[0]
        conv["id"] = str_id(conv.get("id", ""))
        return conv


@router.get("/conversations")
async def list_conversations(user_id: Optional[str] = None, limit: int = 20):
    """List recent conversations, optionally filtered by user."""
    async with db.get_db() as conn:
        if user_id:
            result = await conn.query(
                "SELECT thread_id, user_id, created_at, updated_at, "
                "array::len(messages) AS message_count "
                "FROM conversation WHERE user_id = $uid "
                "ORDER BY updated_at DESC LIMIT $lim",
                {"uid": user_id, "lim": limit},
            )
        else:
            result = await conn.query(
                "SELECT thread_id, user_id, created_at, updated_at, "
                "array::len(messages) AS message_count "
                "FROM conversation ORDER BY updated_at DESC LIMIT $lim",
                {"lim": limit},
            )
        for r in result:
            r["id"] = str_id(r.get("id", ""))
        return result


@router.post("/distill", response_model=DistillResponse)
async def distill(request: DistillRequest):
    """Distill conversation context into user memory.

    After a chat session, call this to extract key preferences, interests,
    and insights from the conversation and persist them in the user's
    context field in SurrealDB.
    """
    logger.info(f"Distill request: user={request.user_id}, thread={request.thread_id}")
    try:
        # Try persisted conversation first, fall back to checkpointer
        messages = []
        async with db.get_db() as conn:
            conv_messages = await _load_conversation(conn, request.thread_id)
            if conv_messages:
                from langchain_core.messages import HumanMessage as HM, AIMessage
                for m in conv_messages:
                    if m["role"] == "user":
                        messages.append(HM(content=m["content"]))
                    elif m["role"] == "assistant":
                        messages.append(AIMessage(content=m["content"]))

        # Fall back to checkpointer (in-memory, won't survive restart)
        if not messages:
            agent = get_agent(None, None, "default")
            config = {"configurable": {"thread_id": request.thread_id}}
            state = await agent.aget_state(config)
            messages = state.values.get("messages", [])

        if not messages:
            return DistillResponse(user_id=request.user_id, context="", updated=False)

        # Build conversation summary for distillation
        convo_lines = []
        for msg in messages[-20:]:  # Last 20 messages max
            role = msg.__class__.__name__.replace("Message", "")
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            if content and len(content) > 10:  # Skip tool results noise
                convo_lines.append(f"{role}: {content[:300]}")
        convo_text = "\n".join(convo_lines)

        # Load existing context
        existing_context = ""
        async with db.get_db() as conn:
            user_result = await conn.query(f"SELECT context FROM customer:{request.user_id}")
            if user_result and isinstance(user_result[0], dict):
                existing_context = user_result[0].get("context", "") or ""

        # Use the LLM to distill
        from langchain_core.messages import HumanMessage as HM
        llm = get_llm()
        distill_prompt = (
            "You are a context distiller. Given a conversation between a user and a product assistant, "
            "extract the key preferences, interests, goals, and any insights about the user. "
            "Output a concise 2-4 sentence summary that would help personalize future conversations.\n\n"
            f"Existing context (merge with, don't lose): {existing_context}\n\n"
            f"Conversation:\n{convo_text}\n\n"
            "Distilled context:"
        )
        result = await llm.ainvoke([HM(content=distill_prompt)])
        new_context = result.content.strip()

        # Update user record
        async with db.get_db() as conn:
            await conn.query(
                f"UPDATE customer:{request.user_id} SET context = $context",
                {"context": new_context},
            )

        return DistillResponse(user_id=request.user_id, context=new_context, updated=True)
    except Exception as e:
        logger.error(f"Distill error: {e}")
        return DistillResponse(user_id=request.user_id, context=str(e), updated=False)
