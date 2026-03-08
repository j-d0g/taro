"""Unit tests for filesystem tool path routing (no DB required)."""

from tools.fs_tools import route


def test_route_root():
    assert route("/") == ("_root", ())


def test_route_root_empty():
    assert route("") == ("_root", ())


def test_route_users():
    assert route("/users/") == ("_list_users", ())


def test_route_users_no_slash():
    assert route("/users") == ("_list_users", ())


def test_route_user_by_id():
    assert route("/users/sarah_v") == ("_show_user", ("sarah_v",))


def test_route_user_by_id_trailing_slash():
    assert route("/users/sarah_v/") == ("_show_user", ("sarah_v",))


def test_route_user_orders():
    assert route("/users/sarah_v/orders/") == ("_list_user_orders", ("sarah_v",))


def test_route_user_orders_no_slash():
    assert route("/users/sarah_v/orders") == ("_list_user_orders", ("sarah_v",))


def test_route_products():
    assert route("/products/") == ("_list_products", ())


def test_route_products_no_slash():
    assert route("/products") == ("_list_products", ())


def test_route_product_by_id():
    assert route("/products/impact_whey") == ("_show_product", ("impact_whey",))


def test_route_product_by_id_trailing_slash():
    assert route("/products/impact_whey/") == ("_show_product", ("impact_whey",))


def test_route_categories():
    assert route("/categories/") == ("_list_categories", ())


def test_route_categories_no_slash():
    assert route("/categories") == ("_list_categories", ())


def test_route_category_by_id():
    assert route("/categories/protein") == ("_show_category", ("protein",))


def test_route_category_by_id_trailing_slash():
    assert route("/categories/protein/") == ("_show_category", ("protein",))


def test_route_goals():
    assert route("/goals/") == ("_list_goals", ())


def test_route_goals_no_slash():
    assert route("/goals") == ("_list_goals", ())


def test_route_goal_by_id():
    assert route("/goals/muscle_gain") == ("_show_goal", ("muscle_gain",))


def test_route_goal_by_id_trailing_slash():
    assert route("/goals/muscle_gain/") == ("_show_goal", ("muscle_gain",))


def test_route_ingredients():
    assert route("/ingredients/") == ("_list_ingredients", ())


def test_route_ingredients_no_slash():
    assert route("/ingredients") == ("_list_ingredients", ())


def test_route_ingredient_by_id():
    assert route("/ingredients/creatine") == ("_show_ingredient", ("creatine",))


def test_route_ingredient_by_id_trailing_slash():
    assert route("/ingredients/creatine/") == ("_show_ingredient", ("creatine",))


def test_route_system_patterns():
    assert route("/system/patterns") == ("_list_patterns", ())


def test_route_system_patterns_trailing_slash():
    assert route("/system/patterns/") == ("_list_patterns", ())


def test_route_invalid():
    assert route("/invalid/path/that/doesnt/match") is None


def test_route_invalid_nested():
    assert route("/users/sarah_v/orders/123/items") is None


def test_trailing_slash_normalization():
    """Trailing slash should not affect routing."""
    assert route("/users/") == route("/users")
    assert route("/products/") == route("/products")
    assert route("/categories/") == route("/categories")
    assert route("/goals/") == route("/goals")
    assert route("/ingredients/") == route("/ingredients")
    assert route("/users/sarah_v/") == route("/users/sarah_v")
    assert route("/products/impact_whey/") == route("/products/impact_whey")
    assert route("/categories/protein/") == route("/categories/protein")
    assert route("/goals/muscle_gain/") == route("/goals/muscle_gain")
    assert route("/ingredients/creatine/") == route("/ingredients/creatine")
    assert route("/users/sarah_v/orders/") == route("/users/sarah_v/orders")


def test_route_without_leading_slash():
    """Paths without leading slash should still work."""
    assert route("users") == ("_list_users", ())
    assert route("products/impact_whey") == ("_show_product", ("impact_whey",))
    assert route("categories/protein") == ("_show_category", ("protein",))
    assert route("goals/muscle_gain") == ("_show_goal", ("muscle_gain",))
    assert route("ingredients/creatine") == ("_show_ingredient", ("creatine",))
