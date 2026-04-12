"""LangGraph parent StateGraph: ReAct agent subgraph → judge node.

The parent graph has two visible nodes in LangSmith/Studio:
  1. "agent" — the full ReAct tool-calling subgraph (create_react_agent)
  2. "judge" — evaluates tool selection quality (observational, no message mutation)

Only the parent graph gets a checkpointer; the ReAct subgraph runs without one
so that LangSmith shows the complete topology including the judge.
"""

import os
import sys

# Ensure src/ is on Python path (needed for LangGraph Studio which loads from project root)
sys.path.insert(0, os.path.dirname(__file__))

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import create_react_agent
from loguru import logger

from db import get_db_config
from judge import evaluate_turn
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

# Default LLM settings
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-5.4")
DEFAULT_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))


def get_llm(provider: str = DEFAULT_PROVIDER, model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE):
    """Return the appropriate LangChain chat model for the given provider."""
    provider = provider.lower()

    if provider == "openai":
        # reasoning_effort is only supported on /v1/responses, not /v1/chat/completions.
        # Omit it so gpt-5.4 and other models work with the default endpoint.
        return ChatOpenAI(
            model=model,
            temperature=temperature,
        )

    if provider == "anthropic":
        if ChatAnthropic is None:
            raise ImportError("Install langchain-anthropic: pip install langchain-anthropic")
        return ChatAnthropic(model=model, temperature=temperature)

    if provider == "google":
        if ChatGoogleGenerativeAI is None:
            raise ImportError("Install langchain-google-genai: pip install langchain-google-genai")
        return ChatGoogleGenerativeAI(model=model, temperature=temperature)

    raise ValueError(f"Unsupported LLM provider: {provider}. Use 'openai', 'anthropic', or 'google'.")


async def judge_node(state: MessagesState) -> dict:
    """Evaluate the agent's tool selection after the turn completes.

    Observational only — returns empty messages so the conversation state
    is not modified. The verdict is persisted to SurrealDB by evaluate_turn.
    """
    messages = state["messages"]
    await evaluate_turn(messages)
    return {"messages": []}


def build_graph(model_provider: str = None, model_name: str = None, temperature: float = None, prompt: str = None, use_checkpointer: bool = True):
    """Build a parent StateGraph with agent (ReAct subgraph) → judge nodes.

    When use_checkpointer=False, LangGraph Studio provides its own persistence.
    """
    llm = get_llm(
        provider=model_provider or DEFAULT_PROVIDER,
        model=model_name or DEFAULT_MODEL,
        temperature=temperature if temperature is not None else DEFAULT_TEMPERATURE,
    )

    if use_checkpointer:
        # SurrealSaver has compatibility issues with SurrealDB 3.0 checkpoint retrieval
        # (e.g. "string indices must be integers, not 'str'"). Use MemorySaver so chat works.
        # Conversation history is still persisted via routes/chat.py -> conversation table.
        use_surreal_saver = os.getenv("USE_SURREAL_SAVER", "").lower() == "true"
        if use_surreal_saver:
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
            checkpointer = MemorySaver()
            logger.info("Using MemorySaver for checkpoints (conversation persisted to SurrealDB via conversation table)")
    else:
        checkpointer = None

    # ReAct subgraph — no checkpointer (parent owns persistence)
    react_agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=prompt or load_prompt(),
    )

    # Parent graph: agent → judge
    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", react_agent)
    workflow.add_node("judge", judge_node)
    workflow.add_edge(START, "agent")
    workflow.add_edge("agent", "judge")
    workflow.add_edge("judge", END)

    compiled = workflow.compile(checkpointer=checkpointer)

    logger.info(f"Built parent graph (agent → judge) with {len(ALL_TOOLS)} tools (checkpointer={'enabled' if use_checkpointer else 'platform-managed'})")
    return compiled


# Detect if running under LangGraph Studio (it sets LANGGRAPH_API_URL or similar env vars)
_is_studio = os.getenv("LANGGRAPH_STORE_URI") is not None or "langgraph_api" in sys.modules

# Module-level graph for LangGraph Studio (uses env defaults)
graph = build_graph(use_checkpointer=not _is_studio)
