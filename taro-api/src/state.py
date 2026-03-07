"""Minimal agent state extending MessagesState."""

from typing import Optional

from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """State for the ReAct agent. Extends MessagesState for LangGraph Studio compatibility."""

    channel: Optional[str] = None
    locale: Optional[str] = None
