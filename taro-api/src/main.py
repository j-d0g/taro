"""FastAPI entry point for Taro.ai chatbot."""

import os
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from loguru import logger
from pydantic import BaseModel, Field

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

# Activate LangSmith tracing (env vars must be set before LangChain imports)
if os.getenv("LANGSMITH_TRACING", "").lower() == "true":
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_API_KEY", os.getenv("LANGSMITH_API_KEY", ""))
    os.environ.setdefault("LANGCHAIN_PROJECT", os.getenv("LANGSMITH_PROJECT", "taro-ai-hackathon"))

from graph import DEFAULT_MODEL, DEFAULT_PROVIDER, build_graph, get_llm
from prompts.system import list_prompts, load_prompt


# ── Models ───────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None  # e.g. "diego_carvalho" for personalized context
    channel: str = "myprotein"
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    prompt_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    tool_calls: list[dict] = []


class DistillRequest(BaseModel):
    thread_id: str
    user_id: str  # e.g. "diego_carvalho"


class DistillResponse(BaseModel):
    user_id: str
    context: str
    updated: bool


AVAILABLE_MODELS = {
    "openai": {"default_model": "gpt-4o", "models": ["gpt-5.4", "gpt-5.2", "gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"]},
    "anthropic": {"default_model": "claude-sonnet-4-20250514", "models": ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"]},
    "google": {"default_model": "gemini-2.0-flash", "models": ["gemini-2.0-flash", "gemini-2.5-pro-preview-06-05"]},
}


# ── App ──────────────────────────────────────────────────────

_default_agent = None
_agent_cache: dict[tuple, object] = {}


def _get_agent(provider: Optional[str], model: Optional[str], prompt_id: str):
    """Return a cached agent for the given config, building one if needed."""
    global _default_agent

    # No overrides -> use the default agent
    if not provider and not model and prompt_id == "default":
        return _default_agent

    key = (provider or DEFAULT_PROVIDER, model or DEFAULT_MODEL, prompt_id)
    if key not in _agent_cache:
        logger.info(f"Building new agent for config: {key}")
        _agent_cache[key] = build_graph(
            model_provider=provider,
            model_name=model,
            prompt=load_prompt(prompt_id) if prompt_id != "default" else None,
        )
    return _agent_cache[key]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _default_agent
    logger.info("Starting Taro.ai chatbot...")
    _default_agent = build_graph()
    logger.info("Agent ready")
    yield
    logger.info("Shutting down")


app = FastAPI(title="Taro.ai", description="SurrealDB Agentic Search Chatbot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the chatbot."""
    logger.info(f"Chat request: thread={request.thread_id}, message='{request.message[:80]}'")

    try:
        agent = _get_agent(request.model_provider, request.model_name, request.prompt_id)

        config = {"configurable": {"thread_id": request.thread_id}}

        # Inject user context if user_id provided
        user_context = ""
        if request.user_id:
            try:
                from db import get_db
                async with get_db() as db:
                    user_result = await db.query(
                        f"SELECT * FROM user:{request.user_id}"
                    )
                    if user_result:
                        user = user_result[0] if isinstance(user_result[0], dict) and "id" in user_result[0] else (user_result[0].get("result", [{}])[0] if isinstance(user_result[0], dict) else {})
                        if user:
                            name = user.get("name", request.user_id)
                            goals = ", ".join(user.get("goals", []))
                            skin_type = user.get("skin_type", "")
                            prefs = user.get("preferences", {})
                            context = user.get("context", "")
                            parts = [f"\n[User: {name}]"]
                            if goals:
                                parts.append(f"Goals: {goals}")
                            if skin_type:
                                parts.append(f"Skin type: {skin_type}")
                            if prefs:
                                parts.append(f"Preferences: {prefs}")
                            if context:
                                parts.append(f"Previous context: {context}")
                            user_context = " | ".join(parts)
            except Exception as ue:
                logger.warning(f"Failed to load user context: {ue}")

        message_content = request.message
        if user_context:
            message_content = f"{user_context}\n\n{request.message}"

        input_msg = {"messages": [HumanMessage(content=message_content)]}

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

        return ChatResponse(reply=reply, thread_id=request.thread_id, tool_calls=tool_calls)
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


@app.post("/distill", response_model=DistillResponse)
async def distill(request: DistillRequest):
    """Distill conversation context into user memory.

    After a chat session, call this to extract key preferences, interests,
    and insights from the conversation and persist them in the user's
    context field in SurrealDB.
    """
    logger.info(f"Distill request: user={request.user_id}, thread={request.thread_id}")
    try:
        from db import get_db

        # Get the agent's conversation history from the checkpointer
        agent = _get_agent(None, None, "default")
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
        async with get_db() as db:
            user_result = await db.query(f"SELECT context FROM user:{request.user_id}")
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
        async with get_db() as db:
            await db.query(
                f"UPDATE user:{request.user_id} SET context = $context",
                {"context": new_context},
            )

        return DistillResponse(user_id=request.user_id, context=new_context, updated=True)
    except Exception as e:
        logger.error(f"Distill error: {e}")
        return DistillResponse(user_id=request.user_id, context=str(e), updated=False)


@app.get("/models")
async def models():
    """Return available model providers and their models."""
    return {
        "default_provider": DEFAULT_PROVIDER,
        "default_model": DEFAULT_MODEL,
        "providers": AVAILABLE_MODELS,
    }


@app.get("/prompts")
async def prompts():
    """Return available prompt template IDs."""
    return {"prompts": list_prompts(), "default": "default"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "taro-ai"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
