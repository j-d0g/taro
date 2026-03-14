"""Filesystem-like tools for exploring the data graph.

Uses bash naming (ls, cat, grep, find) because LLMs already know them.
Stateless — every call takes a full path, no cd/pwd.
Graph edges appear as followable paths in ls output.
"""

import re
from functools import lru_cache

from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from loguru import logger

from db import get_db

# ── Embedding cache ──────────────────────────────────────────
# LRU cache on embedding calls to avoid redundant OpenAI API hits.
# Cuts rate-limit risk in half under stress testing.

_embeddings_model = None


def _get_embeddings():
    global _embeddings_model
    if _embeddings_model is None:
        _embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
    return _embeddings_model


# Cache up to 128 query embeddings (tuple key since lists aren't hashable)
_embedding_cache: dict[str, list[float]] = {}
_CACHE_MAX = 128


async def _cached_embed(query: str) -> list[float]:
    """Get embedding for a query, using cache if available."""
    if query in _embedding_cache:
        logger.debug(f"Embedding cache hit: '{query[:40]}...'")
        return _embedding_cache[query]

    embeddings = _get_embeddings()
    result = await embeddings.aembed_query(query)

    if len(_embedding_cache) >= _CACHE_MAX:
        # Evict oldest entry
        oldest = next(iter(_embedding_cache))
        del _embedding_cache[oldest]

    _embedding_cache[query] = result
    return result

# ── Path router ──────────────────────────────────────────────

ROUTES = [
    (re.compile(r"^/?$"), "_root"),
    (re.compile(r"^/users/?$"), "_list_users"),
    (re.compile(r"^/users/([^/]+)/orders/?$"), "_list_user_orders"),
    (re.compile(r"^/users/([^/]+)/preferences/?$"), "_list_user_preferences"),
    (re.compile(r"^/users/([^/]+)/?$"), "_show_user"),
    (re.compile(r"^/products/?$"), "_list_products"),
    (re.compile(r"^/products/([^/]+)/?$"), "_show_product"),
    (re.compile(r"^/categories/?$"), "_list_categories"),
    (re.compile(r"^/categories/([^/]+)/?$"), "_show_category"),
    (re.compile(r"^/goals/?$"), "_list_goals"),
    (re.compile(r"^/goals/([^/]+)/?$"), "_show_goal"),
    (re.compile(r"^/ingredients/?$"), "_list_ingredients"),
    (re.compile(r"^/ingredients/([^/]+)/?$"), "_show_ingredient"),
    (re.compile(r"^/system/patterns/?$"), "_list_patterns"),
]


def route(path: str) -> tuple[str, tuple] | None:
    """Match a path to a handler name and captured groups."""
    path = path.strip()
    if not path.startswith("/"):
        path = "/" + path
    for pattern, handler in ROUTES:
        m = pattern.match(path)
        if m:
            return (handler, m.groups())
    return None


# ── RRF fusion (shared with find) ───────────────────────────

def _rrf_fuse(vector_results: list, bm25_results: list, k: int = 60) -> list[dict]:
    """Fuse two ranked result lists using Reciprocal Rank Fusion."""
    scores: dict[str, float] = {}
    docs_by_id: dict[str, dict] = {}

    for rank, doc in enumerate(vector_results):
        doc_id = str(doc.get("id", ""))
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
        if doc_id not in docs_by_id:
            docs_by_id[doc_id] = doc
        else:
            docs_by_id[doc_id]["vec_score"] = doc.get("vec_score", 0)

    for rank, doc in enumerate(bm25_results):
        doc_id = str(doc.get("id", ""))
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
        if doc_id not in docs_by_id:
            docs_by_id[doc_id] = doc
        else:
            docs_by_id[doc_id]["bm25_score"] = doc.get("bm25_score", doc.get("score", 0))

    ranked_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    results = []
    for doc_id in ranked_ids:
        doc = docs_by_id[doc_id]
        doc["rrf_score"] = scores[doc_id]
        results.append(doc)
    return results


# ── Handlers ─────────────────────────────────────────────────

async def _handle_root(db, verbose=False):
    return "users/  products/  categories/  goals/  ingredients/  system/"


async def _handle_list_users(db, verbose=False):
    result = await db.query("SELECT id, name, profile_type, experience_level FROM customer")
    rows = result or []
    if not rows:
        return "No users found."
    lines = [f"{'Users' if not verbose else 'All users'} ({len(rows)}):"]
    for u in rows:
        uid = str(u.get("id", "")).replace("customer:", "")
        name = u.get("name", "?")
        ptype = u.get("profile_type", "")
        level = u.get("experience_level", "")
        lines.append(f"  {uid}/  {name} ({ptype}, {level})")
    return "\n".join(lines)


async def _handle_show_user(db, user_id, verbose=False):
    result = await db.query(f"SELECT * FROM customer:{user_id}")
    rows = result or []
    if not rows:
        return f"User not found: {user_id}"
    u = rows[0]
    uid = str(u.get("id", ""))

    if not verbose:
        # Brief: name, type, level + related paths
        name = u.get("name", "?")
        ptype = u.get("profile_type", "")
        level = u.get("experience_level", "")
        goals = ", ".join(u.get("goals", []))
        dietary = ", ".join(u.get("dietary_restrictions", [])) or "none"
        lines = [
            f"{uid} — {name}",
            f"  Type: {ptype} | Level: {level}",
            f"  Goals: {goals}",
            f"  Dietary: {dietary}",
            f"\nRelated:",
            f"  /users/{user_id}/orders/",
        ]
        return "\n".join(lines)
    else:
        # Verbose: all fields + orders with product names
        lines = [f"Record: {uid}"]
        for key, val in u.items():
            if key == "id":
                continue
            if isinstance(val, list):
                lines.append(f"  {key}: {', '.join(str(v) for v in val) if val else '—'}")
            else:
                lines.append(f"  {key}: {val}")

        # Fetch orders
        orders_result = await db.query(
            f"SELECT ->placed->order.* AS orders FROM customer:{user_id}"
        )
        orders = orders_result[0].get("orders", []) if orders_result else []
        if orders:
            lines.append(f"\nOrders ({len(orders)}):")
            for o in orders:
                oid = str(o.get("id", ""))
                date = str(o.get("order_date", ""))[:10]
                total = o.get("total", 0)
                currency = o.get("currency", "GBP")
                status = o.get("status", "?")
                lines.append(f"  {oid} — {date} — {currency} {total:.2f} — {status}")
                # Get products in this order
                oid_str = oid
                prods_result = await db.query(
                    f"SELECT ->contains->product.{{id, name}} AS products FROM {oid_str}"
                )
                prods = prods_result[0].get("products", []) if prods_result else []
                for p in prods:
                    pid = str(p.get("id", ""))
                    pname = p.get("name", "?")
                    lines.append(f"    → {pid} ({pname})")
        else:
            lines.append("\nNo orders found.")

        lines.append(f"\nBrowse: /users/{user_id}/orders/")
        return "\n".join(lines)


async def _handle_list_user_orders(db, user_id, verbose=False):
    result = await db.query(
        f"SELECT ->placed->order.* AS orders FROM customer:{user_id}"
    )
    orders = result[0].get("orders", []) if result else []
    if not orders:
        return f"No orders found for customer:{user_id}"

    lines = [f"Orders for customer:{user_id} ({len(orders)}):"]
    for o in orders:
        oid = str(o.get("id", ""))
        date = str(o.get("order_date", ""))[:10]
        total = o.get("total", 0)
        currency = o.get("currency", "GBP")
        status = o.get("status", "?")
        lines.append(f"  {oid} — {date} — {currency} {total:.2f} — {status}")
        # Get product summaries
        prods_result = await db.query(
            f"SELECT ->contains->product.{{id, name, price}} AS products FROM {oid}"
        )
        prods = prods_result[0].get("products", []) if prods_result else []
        for p in prods:
            pid = str(p.get("id", "")).replace("product:", "")
            pname = p.get("name", "?")
            pprice = p.get("price", 0)
            lines.append(f"    → {pid} ({pname}, £{pprice:.2f})")
    return "\n".join(lines)


async def _handle_list_user_preferences(db, user_id, verbose=False):
    result = await db.query(
        "SELECT "
        "->wants->product.{id, name, price} AS cart, "
        "->interested_in->product.{id, name, price} AS saved, "
        "->rejected->product.{id, name, price} AS rejected "
        f"FROM customer:{user_id}"
    )
    row = result[0] if result else {}
    lines = [f"Preferences for customer:{user_id}:"]

    def _line_list(items, prefix):
        out = []
        for p in items or []:
            pid = str(p.get("id", "")).replace("product:", "")
            name = p.get("name", "?")
            price = p.get("price", 0)
            out.append(f"  {prefix}: {pid}  {name} — £{price:.2f}")
        return out

    lines.extend(_line_list(row.get("cart"), "cart"))
    lines.extend(_line_list(row.get("saved"), "saved"))
    lines.extend(_line_list(row.get("rejected"), "rejected"))
    if len(lines) == 1:
        lines.append("  (no cart, saved, or rejected items)")
    return "\n".join(lines)


async def _handle_list_products(db, verbose=False):
    result = await db.query(
        "SELECT id, name, category, price, dietary_tags FROM product LIMIT 50"
    )
    rows = result or []
    if not rows:
        return "No products found."
    lines = [f"Products ({len(rows)}):"]
    for p in rows:
        pid = str(p.get("id", "")).replace("product:", "")
        name = p.get("name", "?")
        cat = p.get("category", "?")
        price = p.get("price", 0)
        tags = p.get("dietary_tags")
        tag_str = f" [{', '.join(tags)}]" if tags else ""
        lines.append(f"  {pid}/  {name} — £{price:.2f} ({cat}){tag_str}")
    return "\n".join(lines)


async def _handle_show_product(db, product_id, verbose=False):
    result = await db.query(f"SELECT * FROM product:{product_id}")
    rows = result or []
    if not rows:
        return f"Product not found: {product_id}"
    p = rows[0]
    pid = str(p.get("id", ""))

    if not verbose:
        name = p.get("name", "?")
        price = p.get("price", 0)
        cat = p.get("category", "?")
        desc = p.get("description", "")[:150]
        tags = p.get("dietary_tags")
        tag_str = f"\n  Dietary: {', '.join(tags)}" if tags else ""
        lines = [
            f"{pid} — {name}",
            f"  Price: £{price:.2f} | Category: {cat}",
            f"  {desc}{'...' if len(p.get('description', '')) > 150 else ''}",
        ]
        if tag_str:
            lines.append(tag_str.strip())
        # Related paths
        related_result = await db.query(
            f"SELECT ->related_to->product.id AS related FROM {pid}"
        )
        related_ids = related_result[0].get("related", []) if related_result else []
        if related_ids:
            lines.append("\nRelated:")
            for rid in related_ids[:5]:
                rid_str = str(rid).replace("product:", "")
                lines.append(f"  /products/{rid_str}")
        # Category
        cat_result = await db.query(
            f"SELECT ->belongs_to->category.id AS cats FROM {pid}"
        )
        cats = cat_result[0].get("cats", []) if cat_result else []
        if cats:
            cat_id = str(cats[0]).replace("category:", "")
            lines.append(f"  /categories/{cat_id}/")
        return "\n".join(lines)
    else:
        # Verbose: all fields + related product details
        lines = [f"Record: {pid}"]
        for key, val in p.items():
            if key == "id":
                continue
            if isinstance(val, list):
                lines.append(f"  {key}: {', '.join(str(v) for v in val) if val else '—'}")
            else:
                lines.append(f"  {key}: {val}")

        # Related products with names
        related_result = await db.query(
            f"SELECT ->related_to->product.{{id, name, price}} AS related FROM {pid}"
        )
        related = related_result[0].get("related", []) if related_result else []
        if related:
            lines.append("\nRelated products:")
            for r in related:
                rid = str(r.get("id", ""))
                rname = r.get("name", "?")
                rprice = r.get("price", 0)
                lines.append(f"  → {rid} ({rname}, £{rprice:.2f})")

        # Category
        cat_result = await db.query(
            f"SELECT ->belongs_to->category.{{id, name}} AS cats FROM {pid}"
        )
        cats = cat_result[0].get("cats", []) if cat_result else []
        if cats:
            cat_id = str(cats[0].get("id", "")).replace("category:", "")
            cat_name = cats[0].get("name", "?")
            lines.append(f"\nCategory: {cat_name} → /categories/{cat_id}/")

        # Graph edge counts — breadcrumbs to encourage graph_traverse
        edge_counts = await db.query(
            f"SELECT "
            f"count(->also_bought->product) AS also_bought, "
            f"count(->contains_ingredient->ingredient) AS ingredients, "
            f"count(->supports_goal->goal) AS goals, "
            f"count(->related_to->product) AS related_to "
            f"FROM {pid}"
        )
        if edge_counts:
            ec = edge_counts[0] if isinstance(edge_counts[0], dict) else {}
            parts = []
            for label, key in [("also_bought", "also_bought"), ("ingredients", "ingredients"),
                               ("goals", "goals"), ("related_to", "related_to")]:
                count = ec.get(key, 0)
                if count:
                    parts.append(f"{label}({count})")
            if parts:
                lines.append(f"\nGraph edges: {', '.join(parts)}")
                lines.append("  → Use graph_traverse to explore these connections")

        return "\n".join(lines)


async def _handle_list_categories(db, verbose=False):
    result = await db.query("SELECT id, name, description FROM category")
    rows = result or []
    if not rows:
        return "No categories found."
    lines = [f"Categories ({len(rows)}):"]
    for c in rows:
        cid = str(c.get("id", "")).replace("category:", "")
        name = c.get("name", "?")
        desc = c.get("description", "")
        lines.append(f"  {cid}/  {name}")
        if verbose and desc:
            lines.append(f"    {desc}")
    return "\n".join(lines)


async def _handle_show_category(db, category_id, verbose=False):
    # Get category info
    cat_result = await db.query(f"SELECT * FROM category:{category_id}")
    cat_rows = cat_result or []
    if not cat_rows:
        return f"Category not found: {category_id}"
    c = cat_rows[0]
    cname = c.get("name", "?")

    # Get products in this category
    result = await db.query(
        f"SELECT <-belongs_to<-product.{{id, name, price, dietary_tags}} AS products FROM category:{category_id}"
    )
    products = result[0].get("products", []) if result else []

    lines = [f"Category: {cname} ({len(products)} products)"]
    if c.get("description"):
        lines.append(f"  {c['description']}")
    lines.append("")
    for p in products:
        pid = str(p.get("id", "")).replace("product:", "")
        pname = p.get("name", "?")
        pprice = p.get("price", 0)
        tags = p.get("dietary_tags")
        tag_str = f" [{', '.join(tags)}]" if tags else ""
        lines.append(f"  {pid}/  {pname} — £{pprice:.2f}{tag_str}")

    # Subcategories
    sub_result = await db.query(
        f"SELECT <-child_of<-category.{{id, name}} AS children FROM category:{category_id}"
    )
    children = sub_result[0].get("children", []) if sub_result else []
    if children:
        lines.append("\nSubcategories:")
        for ch in children:
            chid = str(ch.get("id", "")).replace("category:", "")
            chname = ch.get("name", "?")
            lines.append(f"  {chid}/  {chname}")
    return "\n".join(lines)


async def _handle_list_goals(db, verbose=False):
    result = await db.query("SELECT id, name, description FROM goal")
    rows = result or []
    if not rows:
        return "No goals found."
    lines = [f"Goals ({len(rows)}):"]
    for g in rows:
        gid = str(g.get("id", "")).replace("goal:", "")
        name = g.get("name", "?")
        desc = g.get("description", "")
        lines.append(f"  {gid}/  {name}")
        if verbose and desc:
            lines.append(f"    {desc}")
    return "\n".join(lines)


async def _handle_show_goal(db, goal_id, verbose=False):
    goal_result = await db.query(f"SELECT * FROM goal:{goal_id}")
    goal_rows = goal_result or []
    if not goal_rows:
        return f"Goal not found: {goal_id}"
    g = goal_rows[0]
    gname = g.get("name", "?")

    result = await db.query(
        f"SELECT <-supports_goal<-product.{{id, name, price, dietary_tags}} AS products FROM goal:{goal_id}"
    )
    products = result[0].get("products", []) if result else []

    lines = [f"Goal: {gname} ({len(products)} products)"]
    if g.get("description"):
        lines.append(f"  {g['description']}")
    lines.append("")
    for p in products:
        pid = str(p.get("id", "")).replace("product:", "")
        pname = p.get("name", "?")
        pprice = p.get("price", 0)
        tags = p.get("dietary_tags")
        tag_str = f" [{', '.join(tags)}]" if tags else ""
        lines.append(f"  {pid}/  {pname} — £{pprice:.2f}{tag_str}")
    return "\n".join(lines)


async def _handle_list_ingredients(db, verbose=False):
    result = await db.query("SELECT id, name, category, description FROM ingredient")
    rows = result or []
    if not rows:
        return "No ingredients found."
    lines = [f"Ingredients ({len(rows)}):"]
    for ing in rows:
        iid = str(ing.get("id", "")).replace("ingredient:", "")
        name = ing.get("name", "?")
        cat = ing.get("category", "")
        cat_str = f" ({cat})" if cat else ""
        lines.append(f"  {iid}/  {name}{cat_str}")
        if verbose and ing.get("description"):
            lines.append(f"    {ing['description']}")
    return "\n".join(lines)


async def _handle_show_ingredient(db, ingredient_id, verbose=False):
    ing_result = await db.query(f"SELECT * FROM ingredient:{ingredient_id}")
    ing_rows = ing_result or []
    if not ing_rows:
        return f"Ingredient not found: {ingredient_id}"
    ing = ing_rows[0]
    iname = ing.get("name", "?")

    result = await db.query(
        f"SELECT <-contains_ingredient<-product.{{id, name, price, dietary_tags}} AS products FROM ingredient:{ingredient_id}"
    )
    products = result[0].get("products", []) if result else []

    lines = [f"Ingredient: {iname} ({len(products)} products)"]
    if ing.get("description"):
        lines.append(f"  {ing['description']}")
    if ing.get("category"):
        lines.append(f"  Type: {ing['category']}")
    lines.append("")
    for p in products:
        pid = str(p.get("id", "")).replace("product:", "")
        pname = p.get("name", "?")
        pprice = p.get("price", 0)
        tags = p.get("dietary_tags")
        tag_str = f" [{', '.join(tags)}]" if tags else ""
        lines.append(f"  {pid}/  {pname} — £{pprice:.2f}{tag_str}")
    return "\n".join(lines)


async def _handle_list_patterns(db, verbose=False):
    """List learned tool-selection patterns and recent failures."""
    patterns = await db.query("SELECT * FROM learned_pattern ORDER BY success_count DESC LIMIT 20")
    failures = await db.query("SELECT * FROM failure_record ORDER BY created_at DESC LIMIT 10")
    patterns = patterns or []
    failures = failures or []

    lines = [f"Learned patterns ({len(patterns)}):"]
    for p in patterns:
        insight = p.get('insight', '')
        insight_str = f" — {insight}" if insight else ""
        lines.append(f"  [{p.get('pattern_type', '?')}] {p.get('query_pattern', '?')} -> {p.get('best_tool', '?')} (x{p.get('success_count', 0)}){insight_str}")
    lines.append(f"\nRecent failures ({len(failures)}):")
    for f in failures:
        lines.append(f"  {f.get('tool_used', '?')}: {f.get('error', '?')[:80]}")
    return "\n".join(lines)


# ── Dispatch ─────────────────────────────────────────────────

_HANDLERS = {
    "_root": _handle_root,
    "_list_users": _handle_list_users,
    "_show_user": _handle_show_user,
    "_list_user_orders": _handle_list_user_orders,
    "_list_user_preferences": _handle_list_user_preferences,
    "_list_products": _handle_list_products,
    "_show_product": _handle_show_product,
    "_list_categories": _handle_list_categories,
    "_show_category": _handle_show_category,
    "_list_goals": _handle_list_goals,
    "_show_goal": _handle_show_goal,
    "_list_ingredients": _handle_list_ingredients,
    "_show_ingredient": _handle_show_ingredient,
    "_list_patterns": _handle_list_patterns,
}


async def _dispatch(db, handler_name: str, args: tuple, verbose: bool = False):
    handler = _HANDLERS[handler_name]
    return await handler(db, *args, verbose=verbose)


# ── Tools ────────────────────────────────────────────────────

@tool
async def ls(path: str = "/") -> str:
    """[GATHER] List contents of a path in the data graph. Like bash `ls`.

    Use in the GATHER phase to orient yourself before searching. Browse the data
    graph to understand what entities exist and how they connect.

    Paths:
      /              → Top-level directories (users, products, categories, goals, ingredients)
      /users/        → List all users with profile types
      /users/{id}    → User summary + link to their orders
      /users/{id}/orders/ → User's order history with product names
      /users/{id}/preferences/ → User's cart, saved, and rejected products
      /products/     → List all products with prices
      /products/{id} → Product summary + related products
      /categories/   → List all categories
      /categories/{id}/ → Products in a category
      /goals/        → List all beauty/skincare goals
      /goals/{id}/   → Products supporting a goal
      /ingredients/  → List all key ingredients
      /ingredients/{id}/ → Products containing an ingredient

    Args:
        path: The path to list (default: "/" for root).
    """
    logger.info(f"ls: path='{path}'")
    match = route(path)
    if not match:
        return (
            f"Invalid path: {path}\n"
            "Valid paths: /, /users/, /users/{{id}}, /users/{{id}}/orders/, /users/{{id}}/preferences/, "
            "/products/, /products/{{id}}, /categories/, /categories/{{id}}/, "
            "/goals/, /goals/{{id}}/, /ingredients/, /ingredients/{{id}}/"
        )
    handler_name, args = match
    try:
        async with get_db() as db:
            return await _dispatch(db, handler_name, args, verbose=False)
    except Exception as e:
        logger.error(f"ls error: {e}")
        return f"Error listing {path}: {e}"


@tool
async def cat(path: str) -> str:
    """[GATHER/VERIFY] Read full details of a record. Like bash `cat`.

    GATHER: Use after `ls` to deeply understand a record's fields and relationships.
    VERIFY: Use to confirm product details (price, description) before recommending.

    Returns all fields, related records, and graph connections.

    Paths (same as ls):
      /users/{id}        → Full profile + order history with products
      /products/{id}     → All fields + related products + category
      /categories/{id}/  → Category description + all products in it

    Args:
        path: Path to the record to read.
    """
    logger.info(f"cat: path='{path}'")
    match = route(path)
    if not match:
        return (
            f"Invalid path: {path}\n"
            "Valid paths: /users/{{id}}, /products/{{id}}, /categories/{{id}}/"
        )
    handler_name, args = match
    try:
        async with get_db() as db:
            return await _dispatch(db, handler_name, args, verbose=True)
    except Exception as e:
        logger.error(f"cat error: {e}")
        return f"Error reading {path}: {e}"


@tool
async def grep(query: str, scope: str = "") -> str:
    """[ACT] Keyword text search within a scope. Like bash `grep`.

    Use in the ACT phase for exact keyword matching within a specific scope.
    Searches using BM25 full-text matching for exact terms and names.

    Args:
        query: Search terms (e.g. "vegan protein", "Sarah", "creatine").
        scope: Path to search within. Options:
            ""  or "/"     → Search all documents
            "/products"    → Search product documents only
            "/users"       → Search user names
            "/categories"  → Search category names
    """
    logger.info(f"grep: query='{query}', scope='{scope}'")
    scope = scope.strip().rstrip("/")
    try:
        async with get_db() as db:
            if scope in ("", "/", "/products"):
                # Keyword search on documents table (CONTAINS fallback for BM25 broken in SurrealDB 3.0)
                type_filter = "AND doc_type = 'product'" if scope == "/products" else ""
                words = query.split()[:4]
                contains_filter = " OR ".join(
                    f"string::lowercase(content) CONTAINS string::lowercase('{w}')"
                    for w in words
                )
                surql = f"""
                    SELECT id, title, content, doc_type, source_id, 1.0 AS score
                    FROM documents
                    WHERE ({contains_filter}) {type_filter}
                    LIMIT 10
                """
                result = await db.query(surql, {"query": query})
                docs = result if isinstance(result, list) else []
                if not docs:
                    return f"No results for '{query}' in {scope or 'all documents'}"
                lines = [f"grep '{query}' {scope or '/'} ({len(docs)} matches):"]
                for doc in docs:
                    title = doc.get("title", "Untitled")
                    score = doc.get("score", 0)
                    source = str(doc.get("source_id", ""))
                    content = doc.get("content", "")[:150]
                    lines.append(f"\n  {title} (score: {score:.2f})")
                    if source:
                        sid = source.replace("product:", "")
                        lines.append(f"    → /products/{sid}")
                    lines.append(f"    {content}...")
                return "\n".join(lines)

            elif scope == "/users":
                surql = "SELECT id, name, profile_type, experience_level FROM customer WHERE name ~ $query"
                result = await db.query(surql, {"query": query})
                rows = result or []
                if not rows:
                    return f"No users matching '{query}'"
                lines = [f"grep '{query}' /users ({len(rows)} matches):"]
                for u in rows:
                    uid = str(u.get("id", "")).replace("customer:", "")
                    name = u.get("name", "?")
                    ptype = u.get("profile_type", "")
                    lines.append(f"  {uid}/  {name} ({ptype})")
                    lines.append(f"    → /users/{uid}")
                return "\n".join(lines)

            elif scope == "/categories":
                surql = "SELECT id, name, description FROM category WHERE name ~ $query"
                result = await db.query(surql, {"query": query})
                rows = result or []
                if not rows:
                    return f"No categories matching '{query}'"
                lines = [f"grep '{query}' /categories ({len(rows)} matches):"]
                for c in rows:
                    cid = str(c.get("id", "")).replace("category:", "")
                    cname = c.get("name", "?")
                    lines.append(f"  {cid}/  {cname}")
                    lines.append(f"    → /categories/{cid}/")
                return "\n".join(lines)

            else:
                return f"Unknown scope: {scope}. Use: /products, /users, /categories, or empty for all."
    except Exception as e:
        logger.error(f"grep error: {e}")
        return f"Error searching '{query}': {e}"


@tool
async def find(query: str, doc_type: str = "", limit: int = 5) -> str:
    """[ACT] Semantic + keyword hybrid search using vector embeddings and BM25. Like bash `find`.

    Use in the ACT phase for discovering NEW products by concept or description.
    Combines meaning-based vector search with exact keyword matching via RRF.

    Best for: product recommendations, conceptual queries, "find something for X".

    Do NOT use for: relationship queries (co-purchases, ingredients, categories, reviews, goals).
    For those, use `graph_traverse` instead — it follows actual graph edges in the database.

    Args:
        query: Natural language search query (e.g. "vegan protein for muscle gain").
        doc_type: Optional filter: 'product', 'faq', or 'article'.
        limit: Max results (default 5).
    """
    logger.info(f"find: query='{query}', doc_type='{doc_type}'")
    try:
        # Cached + retry embedding call (avoids redundant OpenAI API hits)
        query_embedding = None
        for attempt in range(3):
            try:
                query_embedding = await _cached_embed(query)
                break
            except Exception as embed_err:
                if attempt < 2:
                    import asyncio
                    await asyncio.sleep(1 * (attempt + 1))
                    logger.warning(f"find: embedding retry {attempt + 1}: {embed_err}")
                else:
                    raise embed_err

        async with get_db() as db:
            type_filter = "AND doc_type = $doc_type" if doc_type else ""
            params: dict = {"embedding": query_embedding, "query": query}
            if doc_type:
                params["doc_type"] = doc_type

            fetch_limit = limit * 3

            # Vector search: cosine similarity ORDER BY (KNN <|N|> broken in SurrealDB 3.0)
            vec_surql = f"""
                SELECT id, title, content, doc_type, source_id,
                       vector::similarity::cosine(embedding, $embedding) AS vec_score
                FROM documents
                WHERE doc_type IS NOT NONE {type_filter}
                ORDER BY vec_score DESC
                LIMIT {fetch_limit}
            """

            # Keyword search: try BM25, fall back to CONTAINS
            bm25_surql = f"""
                SELECT id, title, content, doc_type, source_id,
                       search::score(1) AS bm25_score
                FROM documents
                WHERE content @1@ $query {type_filter}
                ORDER BY bm25_score DESC
                LIMIT {fetch_limit}
            """

            vec_result = await db.query(vec_surql, params)
            bm25_result = await db.query(bm25_surql, params)

            # Normalize results (SurrealDB 3.0 returns flat list, handle string errors)
            vec_docs = vec_result if isinstance(vec_result, list) else []
            bm25_docs = bm25_result if isinstance(bm25_result, list) else []

            # BM25 fallback: if @1@ returned empty, use CONTAINS
            if not bm25_docs:
                # Split query into words for multi-word CONTAINS
                words = query.split()[:3]  # Use first 3 words
                contains_filter = " OR ".join(f"string::lowercase(content) CONTAINS string::lowercase('{w}')" for w in words)
                fallback_surql = f"""
                    SELECT id, title, content, doc_type, source_id, 1.0 AS bm25_score
                    FROM documents
                    WHERE ({contains_filter}) {type_filter}
                    LIMIT {fetch_limit}
                """
                bm25_result = await db.query(fallback_surql, params)
                bm25_docs = bm25_result if isinstance(bm25_result, list) else []

            fused = _rrf_fuse(vec_docs, bm25_docs)[:limit]

            if not fused:
                return f"No results for '{query}'. Try broader terms or grep for exact matches."

            lines = [f"find '{query}' ({len(fused)} results, from {len(vec_docs)} vector + {len(bm25_docs)} keyword):"]
            for doc in fused:
                title = doc.get("title", "Untitled")
                rrf = doc.get("rrf_score", 0)
                vec = doc.get("vec_score", 0)
                bm25 = doc.get("bm25_score", 0)
                dtype = doc.get("doc_type", "?")
                source = str(doc.get("source_id", ""))
                content = doc.get("content", "")[:200]

                lines.append(f"\n  {title} (rrf: {rrf:.4f}, vec: {vec:.3f}, bm25: {bm25:.2f}, type: {dtype})")
                if source:
                    sid = source.replace("product:", "")
                    lines.append(f"    → /products/{sid}")
                lines.append(f"    {content}{'...' if len(doc.get('content', '')) > 200 else ''}")
            return "\n".join(lines)
    except Exception as e:
        logger.error(f"find error: {e}")
        return f"Error in hybrid search: {e}"


# ── Tree helpers ────────────────────────────────────────────

# Containment edges: expand in tree output
# Cross-reference edges (related_to): show as pointers only
_MAX_INLINE = 3       # show first N items before truncating
_MAX_LINES = 100      # hard cap on output lines


async def _tree_children(db, path: str) -> list[tuple[str, str, bool]]:
    """Return (label, child_path, is_expandable) for a given path."""
    path = path.rstrip("/")

    if path == "":
        # Root: count each top-level collection
        counts = {}
        for table in ("customer", "product", "category", "goal", "ingredient"):
            result = await db.query(f"SELECT count() AS c FROM {table} GROUP ALL")
            counts[table] = result[0].get("c", 0) if result else 0
        return [
            (f"users/ ({counts['customer']})", "/users", True),
            (f"products/ ({counts['product']} items — use ls /products/)", "/products", False),
            (f"categories/ ({counts['category']})", "/categories", True),
            (f"goals/ ({counts['goal']})", "/goals", True),
            (f"ingredients/ ({counts['ingredient']})", "/ingredients", True),
        ]

    if path == "/users":
        result = await db.query("SELECT id, name, profile_type FROM customer")
        rows = result or []
        return [
            (
                f"{str(u['id']).replace('customer:', '')}  {u.get('name', '?')} ({u.get('profile_type', '')})",
                f"/users/{str(u['id']).replace('customer:', '')}",
                True,
            )
            for u in rows
        ]

    m = re.match(r"^/users/([^/]+)$", path)
    if m:
        uid = m.group(1)
        # Count orders for this customer
        result = await db.query(
            f"SELECT count() AS c FROM order WHERE <-placed<-customer CONTAINS customer:{uid} GROUP ALL"
        )
        count = result[0].get("c", 0) if result else 0
        # Preferences summary (cart/saved/rejected)
        pref_rows = await db.query(
            "SELECT "
            "array::len(->wants->product) AS cart_count, "
            "array::len(->interested_in->product) AS saved_count, "
            "array::len(->rejected->product) AS rejected_count "
            f"FROM customer:{uid}"
        )
        prefs = pref_rows[0] if pref_rows else {}
        cart_c = prefs.get("cart_count", 0) or 0
        saved_c = prefs.get("saved_count", 0) or 0
        rej_c = prefs.get("rejected_count", 0) or 0
        children = [
            (f"orders/ ({count})", f"/users/{uid}/orders", True),
            (f"preferences/ (cart:{cart_c}, saved:{saved_c}, rejected:{rej_c})", f"/users/{uid}/preferences", True),
        ]
        return children

    m = re.match(r"^/users/([^/]+)/orders$", path)
    if m:
        uid = m.group(1)
        result = await db.query(
            f"SELECT ->placed->order.{{id, order_date, total, status}} AS orders FROM customer:{uid}"
        )
        orders = result[0].get("orders", []) if result else []
        children = []
        for o in orders:
            oid = str(o.get("id", ""))
            date = str(o.get("order_date", ""))[:10]
            total = o.get("total", 0)
            status = o.get("status", "?")
            children.append((f"{oid}  {date} £{total:.2f} [{status}]", f"/{oid}", True))
        return children

    m = re.match(r"^/users/([^/]+)/preferences$", path)
    if m:
        uid = m.group(1)
        result = await db.query(
            "SELECT "
            "->wants->product.{id, name, price} AS cart, "
            "->interested_in->product.{id, name, price} AS saved, "
            "->rejected->product.{id, name, price} AS rejected "
            f"FROM customer:{uid}"
        )
        row = result[0] if result else {}
        def _label_list(items, prefix):
            labels = []
            for p in items or []:
                pid = str(p.get("id", "")).replace("product:", "")
                name = p.get("name", "?")
                price = p.get("price", 0)
                labels.append((f"{prefix}: {pid}  {name} — £{price:.2f}", f"/products/{pid}", False))
            return labels

        children = []
        children.extend(_label_list(row.get("cart"), "cart"))
        children.extend(_label_list(row.get("saved"), "saved"))
        children.extend(_label_list(row.get("rejected"), "rejected"))
        if not children:
            return [("(no preferences)", f"/users/{uid}", False)]
        return children

    m = re.match(r"^/order:([^/]+)$", path)
    if m:
        oid = f"order:{m.group(1)}"
        result = await db.query(
            f"SELECT ->contains->product.{{id, name, price}} AS products FROM {oid}"
        )
        prods = result[0].get("products", []) if result else []
        return [
            (
                f"{str(p['id']).replace('product:', '')}  {p.get('name', '?')} — £{p.get('price', 0):.2f}",
                f"/products/{str(p['id']).replace('product:', '')}",
                False,
            )
            for p in prods
        ]

    if path == "/categories":
        # Top-level categories (no parent / not child_of anything)
        result = await db.query(
            "SELECT id, name FROM category WHERE id NOT IN (SELECT in FROM child_of)"
        )
        rows = result or []
        children = []
        for c in rows:
            cid = str(c.get("id", "")).replace("category:", "")
            cname = c.get("name", "?")
            children.append((f"{cid}/  {cname}", f"/categories/{cid}", True))
        return children

    m = re.match(r"^/categories/([^/]+)$", path)
    if m:
        cid = m.group(1)
        children = []
        # Subcategories
        sub_result = await db.query(
            f"SELECT <-child_of<-category.{{id, name}} AS children FROM category:{cid}"
        )
        subs = sub_result[0].get("children", []) if sub_result else []
        for s in subs:
            sid = str(s.get("id", "")).replace("category:", "")
            sname = s.get("name", "?")
            children.append((f"{sid}/  {sname} (subcategory)", f"/categories/{sid}", True))
        # Products in this category
        prod_result = await db.query(
            f"SELECT <-belongs_to<-product.{{id, name, price, dietary_tags}} AS products FROM category:{cid}"
        )
        prods = prod_result[0].get("products", []) if prod_result else []
        for p in prods:
            pid = str(p.get("id", "")).replace("product:", "")
            pname = p.get("name", "?")
            pprice = p.get("price", 0)
            tags = p.get("dietary_tags")
            tag_str = f" [{', '.join(tags)}]" if tags else ""
            children.append((f"{pid}  {pname} — £{pprice:.2f}{tag_str}", f"/products/{pid}", False))
        return children

    if path == "/goals":
        result = await db.query("SELECT id, name FROM goal")
        rows = result or []
        return [
            (
                f"{str(g['id']).replace('goal:', '')}/  {g.get('name', '?')}",
                f"/goals/{str(g['id']).replace('goal:', '')}",
                True,
            )
            for g in rows
        ]

    m = re.match(r"^/goals/([^/]+)$", path)
    if m:
        gid = m.group(1)
        result = await db.query(
            f"SELECT <-supports_goal<-product.{{id, name, price, dietary_tags}} AS products FROM goal:{gid}"
        )
        prods = result[0].get("products", []) if result else []
        return [
            (
                f"{str(p['id']).replace('product:', '')}  {p.get('name', '?')} — £{p.get('price', 0):.2f}"
                + (f" [{', '.join(p['dietary_tags'])}]" if p.get("dietary_tags") else ""),
                f"/products/{str(p['id']).replace('product:', '')}",
                False,
            )
            for p in prods
        ]

    if path == "/ingredients":
        result = await db.query("SELECT id, name, category FROM ingredient")
        rows = result or []
        return [
            (
                f"{str(i['id']).replace('ingredient:', '')}/  {i.get('name', '?')}"
                + (f" ({i['category']})" if i.get("category") else ""),
                f"/ingredients/{str(i['id']).replace('ingredient:', '')}",
                True,
            )
            for i in rows
        ]

    m = re.match(r"^/ingredients/([^/]+)$", path)
    if m:
        iid = m.group(1)
        result = await db.query(
            f"SELECT <-contains_ingredient<-product.{{id, name, price, dietary_tags}} AS products FROM ingredient:{iid}"
        )
        prods = result[0].get("products", []) if result else []
        return [
            (
                f"{str(p['id']).replace('product:', '')}  {p.get('name', '?')} — £{p.get('price', 0):.2f}"
                + (f" [{', '.join(p['dietary_tags'])}]" if p.get("dietary_tags") else ""),
                f"/products/{str(p['id']).replace('product:', '')}",
                False,
            )
            for p in prods
        ]

    # Products: show pointers for related_to (cross-ref, not expanded)
    m = re.match(r"^/products/([^/]+)$", path)
    if m:
        pid = m.group(1)
        result = await db.query(
            f"SELECT ->related_to->product.{{id, name}} AS related FROM product:{pid}"
        )
        related = result[0].get("related", []) if result else []
        return [
            (
                f"→ see: {str(r['id']).replace('product:', '')}  {r.get('name', '?')}",
                "",
                False,
            )
            for r in related
        ]

    return []


async def _tree_node(db, path: str, depth: int, prefix: str, lines: list[str]):
    """Recursively build tree output lines."""
    if len(lines) >= _MAX_LINES:
        return

    children = await _tree_children(db, path)
    if not children:
        return

    # Truncate long lists
    show = children
    truncated = 0
    if len(children) > _MAX_INLINE and depth < 2:
        show = children[:_MAX_INLINE]
        truncated = len(children) - _MAX_INLINE

    for i, (label, child_path, expandable) in enumerate(show):
        if len(lines) >= _MAX_LINES:
            lines.append(f"{prefix}└── ...truncated (output limit)")
            return

        is_last = (i == len(show) - 1) and truncated == 0
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{label}")

        if expandable and depth > 0 and child_path:
            child_prefix = prefix + ("    " if is_last else "│   ")
            await _tree_node(db, child_path, depth - 1, child_prefix, lines)

    if truncated > 0:
        if len(lines) < _MAX_LINES:
            lines.append(f"{prefix}└── ...{truncated} more")


@tool
async def tree(path: str = "/", depth: int = 2) -> str:
    """[GATHER] Recursively list the data graph hierarchy. Like bash `tree`.

    Use in the GATHER phase to quickly see the full structure of a branch of the
    data graph. Expands containment edges (categories -> products, goals -> products).
    Cross-references (related products) shown as pointers, not expanded.

    Args:
        path: Starting path (default "/").
        depth: Max levels to expand (default 2, max 4).
    """
    logger.info(f"tree: path='{path}', depth={depth}")
    depth = max(0, min(depth, 4))

    # Normalize path
    path = path.strip()
    if not path.startswith("/"):
        path = "/" + path
    path = path.rstrip("/")
    if path == "":
        path = ""

    # Root label
    label = path.rstrip("/").split("/")[-1] if path else "/"
    if not path:
        label = "/"

    lines = [label]
    try:
        async with get_db() as db:
            await _tree_node(db, path, depth, "", lines)
    except Exception as e:
        logger.error(f"tree error: {e}")
        return f"Error building tree for {path}: {e}"

    if len(lines) == 1:
        return f"{label} (empty)"

    return "\n".join(lines)
