"""LangGraph ReAct agent with SurrealDB checkpointer."""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from loguru import logger

from db import get_db_config
from prompts.system import load_prompt
from tools import ALL_TOOLS

# SurrealSaver: disabled until langgraph-checkpoint-surrealdb supports SurrealDB 3.0
# from langgraph_checkpoint_surrealdb import SurrealSaver

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

# Default LLM settings
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


def build_graph(model_provider: str = None, model_name: str = None, temperature: float = None, prompt: str = None):
    """Build the ReAct agent graph with SurrealDB checkpointer."""
    llm = get_llm(
        provider=model_provider or DEFAULT_PROVIDER,
        model=model_name or DEFAULT_MODEL,
        temperature=temperature if temperature is not None else DEFAULT_TEMPERATURE,
    )

    # TODO: Switch to SurrealSaver when langgraph-checkpoint-surrealdb supports SurrealDB 3.0
    # db_config = get_db_config()
    # checkpointer = SurrealSaver(url=db_config["url"], ...)
    checkpointer = MemorySaver()

    agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=prompt or load_prompt(),
        checkpointer=checkpointer,
    )

    logger.info(f"Built ReAct agent with {len(ALL_TOOLS)} tools and SurrealDB checkpointer")
    return agent


# Module-level graph for LangGraph Studio (uses env defaults)
graph = build_graph()
