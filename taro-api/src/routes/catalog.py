"""Catalog endpoints: categories, goals, verticals."""

from fastapi import APIRouter

import db
from helpers import str_id


router = APIRouter()


@router.get("/categories")
async def list_categories():
    """List all categories with hierarchy (verticals with nested subcategories)."""
    async with db.get_db() as conn:
        # Get all categories
        rows = await conn.query("SELECT id, name, level, description FROM category")

        verticals = []
        subcats_by_parent: dict[str, list] = {}

        # Get child_of edges to build hierarchy
        edges = await conn.query(
            "SELECT in AS child, out AS parent FROM child_of"
        )

        # Map child -> parent
        child_parent: dict[str, str] = {}
        for edge in edges:
            child_id = str(edge.get("child", ""))
            parent_id = str(edge.get("parent", ""))
            child_parent[child_id] = parent_id

        # Separate verticals and subcategories
        for row in rows:
            rid = str(row.get("id", ""))
            row["id"] = str_id(rid)
            if row.get("level") == "vertical":
                row["subcategories"] = []
                verticals.append(row)
            else:
                parent = child_parent.get(rid, "")
                if parent not in subcats_by_parent:
                    subcats_by_parent[parent] = []
                subcats_by_parent[parent].append(row)

        # Nest subcategories under verticals
        for v in verticals:
            full_id = f"category:{v['id']}"
            v["subcategories"] = subcats_by_parent.get(full_id, [])

        return verticals


@router.get("/categories/{category_id}")
async def get_category(category_id: str):
    """Category detail with products."""
    async with db.get_db() as conn:
        cat_rows = await conn.query(f"SELECT * FROM category:`{category_id}`")
        if not cat_rows:
            return {"error": f"Category not found: {category_id}"}
        category = cat_rows[0]
        category["id"] = str_id(category.get("id", ""))

        # Products in this category (product -> belongs_to -> category)
        prod_result = await conn.query(
            f"SELECT <-belongs_to<-product.{{id, name, price, avg_rating, brand, image_url, subcategory, dietary_tags}} "
            f"AS products FROM category:`{category_id}`"
        )
        products = prod_result[0].get("products", []) if prod_result else []
        for p in products:
            p["id"] = str_id(p.get("id", ""))
        category["products"] = products

        # Subcategories (category <- child_of <- category)
        sub_result = await conn.query(
            f"SELECT <-child_of<-category.{{id, name}} AS subcategories FROM category:`{category_id}`"
        )
        subs = sub_result[0].get("subcategories", []) if sub_result else []
        for s in subs:
            s["id"] = str_id(s.get("id", ""))
        category["subcategories"] = subs

        return category


@router.get("/goals")
async def list_goals():
    """List all goals."""
    async with db.get_db() as conn:
        rows = await conn.query("SELECT id, name, description, vertical FROM goal")
        for row in rows:
            row["id"] = str_id(row.get("id", ""))
        return rows


@router.get("/goals/{goal_id}")
async def get_goal(goal_id: str):
    """Goal detail with supporting products."""
    async with db.get_db() as conn:
        goal_rows = await conn.query(f"SELECT * FROM goal:`{goal_id}`")
        if not goal_rows:
            return {"error": f"Goal not found: {goal_id}"}
        goal = goal_rows[0]
        goal["id"] = str_id(goal.get("id", ""))

        # Products supporting this goal (product -> supports_goal -> goal)
        prod_result = await conn.query(
            f"SELECT <-supports_goal<-product.{{id, name, price, avg_rating, brand, image_url, subcategory, dietary_tags}} "
            f"AS products FROM goal:`{goal_id}`"
        )
        products = prod_result[0].get("products", []) if prod_result else []
        for p in products:
            p["id"] = str_id(p.get("id", ""))
        goal["products"] = products

        return goal


@router.get("/verticals")
async def list_verticals():
    """Return distinct product verticals for filter tabs."""
    async with db.get_db() as conn:
        rows = await conn.query(
            "SELECT vertical, count() AS count FROM product GROUP BY vertical ORDER BY vertical"
        )
        return [row["vertical"] for row in rows if row.get("vertical")]
