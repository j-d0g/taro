"""Judge helper: user query extraction when profile is prepended."""

from judge import _user_query_for_judge


def test_judge_strips_profile_prefix():
    profile = (
        "[User: Jane — customer:jane] | Skin type: dry | Graph entry: cat /users/jane "
        "or graph_traverse('customer:jane', 'customer_history')"
    )
    q = "What is the returns policy?"
    combined = f"{profile}\n\n{q}"
    assert _user_query_for_judge(combined) == q


def test_judge_keeps_multiparagraph_without_profile():
    msg = "First line.\n\nSecond paragraph about returns."
    assert _user_query_for_judge(msg) == msg


def test_judge_empty():
    assert _user_query_for_judge("") == ""
