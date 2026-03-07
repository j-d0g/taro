"""Utility helpers ported from services/api."""

from time import perf_counter

from langchain_core.messages import HumanMessage
from loguru import logger


def get_last_user_message(messages: list) -> str:
    """Get the customer's last query. Handles string and LangGraph Studio formats."""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            content = msg.content
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        return item.get("text", "")
                return ""
            else:
                return str(content)
    return ""


class Timer:
    """Simple timing context manager."""

    def __init__(self, label: str):
        self.label = label
        self._start_time = 0.0

    def __enter__(self):
        self._start_time = perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(f"Timer '{self.label}' aborted: {exc_type.__name__}")
            return False
        elapsed = perf_counter() - self._start_time
        logger.info(f"{self.label}: {elapsed:.3f}s")
        return False
