"""Smoke tests: verify all modules import without errors."""


def test_import_db():
    from db import get_db, get_db_config

    config = get_db_config()
    assert "url" in config
    assert "namespace" in config
    assert "database" in config
    assert "user" in config
    assert "password" in config


def test_import_state():
    from state import AgentState

    assert hasattr(AgentState, "__annotations__")
    assert "channel" in AgentState.__annotations__
    assert "locale" in AgentState.__annotations__


def test_import_prompts():
    from prompts.system import load_prompt, list_prompts

    prompts = list_prompts()
    assert isinstance(prompts, list)
    assert "default" in prompts

    default_prompt = load_prompt("default")
    assert isinstance(default_prompt, str)
    assert len(default_prompt) > 100  # not empty


def test_import_helpers():
    from utils.helpers import get_last_user_message, Timer

    assert callable(get_last_user_message)
    assert Timer is not None


def test_import_all_tools():
    from tools import ALL_TOOLS

    assert isinstance(ALL_TOOLS, list)
    assert len(ALL_TOOLS) == 8

    tool_names = [t.name for t in ALL_TOOLS]
    expected = [
        "hybrid_search",
        "semantic_search",
        "keyword_search",
        "graph_traverse",
        "get_record",
        "explore_schema",
        "web_search",
        "surrealql_query",
    ]
    for name in expected:
        assert name in tool_names, f"Missing tool: {name}"
