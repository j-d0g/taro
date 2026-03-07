"""Tests for utility helpers."""

from langchain_core.messages import HumanMessage, AIMessage

from utils.helpers import get_last_user_message, Timer


def test_get_last_user_message_string():
    msgs = [HumanMessage(content="hello"), AIMessage(content="hi")]
    assert get_last_user_message(msgs) == "hello"


def test_get_last_user_message_latest():
    msgs = [
        HumanMessage(content="first"),
        AIMessage(content="response"),
        HumanMessage(content="second"),
    ]
    assert get_last_user_message(msgs) == "second"


def test_get_last_user_message_studio_format():
    """LangGraph Studio sends content as list of dicts."""
    msgs = [HumanMessage(content=[{"type": "text", "text": "studio message"}])]
    assert get_last_user_message(msgs) == "studio message"


def test_get_last_user_message_empty():
    assert get_last_user_message([]) == ""
    assert get_last_user_message([AIMessage(content="no human")]) == ""


def test_timer_context_manager():
    with Timer("test") as t:
        x = 1 + 1
    # Should not raise
    assert x == 2
