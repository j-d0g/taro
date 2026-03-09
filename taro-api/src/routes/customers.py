"""Customer endpoints: GET /customers/{id}, /profile, /orders, /recommendations."""

from fastapi import APIRouter

import db
from helpers import str_id


router = APIRouter()


@router.get("/customers/{customer_id}/profile")
async def get_customer_profile(customer_id: str):
    """Return enriched customer profile with graph-derived data.

    Traverses: customer->placed->order->contains->product,
    order->has_review->review, product->supports_goal->goal,
    product->belongs_to->category.
    """
    async with db.get_db() as conn:
        # 1. Customer record (all fields)
        rows = await conn.query(f"SELECT * FROM customer:`{customer_id}`")
        if not rows:
            return {"error": f"Customer not found: {customer_id}"}
        customer = rows[0]
        customer["id"] = str_id(customer.get("id", ""))

        # 2. Orders with products via graph traversal
        order_result = await conn.query(
            f"SELECT ->placed->order.* AS orders FROM customer:`{customer_id}`"
        )
        orders_raw = order_result[0].get("orders", []) if order_result else []

        orders = []
        all_product_ids = []
        total_spent = 0.0
        for order in orders_raw:
            oid = str(order.get("id", ""))
            order["id"] = str_id(oid)
            total_spent += order.get("price") or order.get("total") or 0

            # Products in this order
            prod_result = await conn.query(
                f"SELECT ->contains->product.{{id, name, price, image_url, subcategory, vertical, brand, avg_rating}} "
                f"AS products FROM {oid}"
            )
            products = prod_result[0].get("products", []) if prod_result else []
            for p in products:
                pid_str = str(p.get("id", ""))
                p["id"] = str_id(pid_str)
                all_product_ids.append(pid_str)
            order["products"] = products
            orders.append(order)

        # 3. Reviews via order->has_review->review
        reviews = []
        review_scores = []
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        for order in orders_raw:
            oid = str(order.get("id", ""))
            rev_result = await conn.query(
                f"SELECT ->has_review->review.* AS reviews FROM {oid}"
            )
            order_reviews = rev_result[0].get("reviews", []) if rev_result else []
            for r in order_reviews:
                r["id"] = str_id(r.get("id", ""))
                reviews.append(r)
                if r.get("score"):
                    review_scores.append(r["score"])
                sentiment = r.get("sentiment", "neutral")
                if sentiment in sentiment_counts:
                    sentiment_counts[sentiment] += 1

        avg_review_score = sum(review_scores) / len(review_scores) if review_scores else 0

        # 4. Inferred goals via product->supports_goal->goal
        goals = []
        seen_goals = set()
        for pid in all_product_ids:
            goal_result = await conn.query(
                f"SELECT ->supports_goal->goal.{{id, name, description}} AS goals FROM {pid}"
            )
            g_list = goal_result[0].get("goals", []) if goal_result else []
            for g in g_list:
                gname = g.get("name", "")
                if gname and gname not in seen_goals:
                    seen_goals.add(gname)
                    g["id"] = str_id(g.get("id", ""))
                    goals.append(g)

        # 5. Top categories via product->belongs_to->category
        cat_counts: dict[str, int] = {}
        cat_names: dict[str, str] = {}
        for pid in all_product_ids:
            cat_result = await conn.query(
                f"SELECT ->belongs_to->category.{{id, name}} AS cats FROM {pid}"
            )
            cats = cat_result[0].get("cats", []) if cat_result else []
            for c in cats:
                cname = c.get("name", "")
                if cname:
                    cat_counts[cname] = cat_counts.get(cname, 0) + 1
                    cat_names[cname] = str_id(c.get("id", ""))

        top_categories = sorted(
            [{"name": k, "id": cat_names[k], "count": v} for k, v in cat_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )

        unique_products = set(all_product_ids)

        return {
            **customer,
            "orders": orders,
            "reviews": reviews,
            "review_stats": {
                "count": len(review_scores),
                "avg_score": round(avg_review_score, 1),
                "sentiment": sentiment_counts,
            },
            "inferred_goals": goals,
            "top_categories": top_categories,
            "stats": {
                "total_spent": round(total_spent, 2),
                "order_count": len(orders),
                "unique_products": len(unique_products),
            },
        }


@router.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    """Return customer profile by ID."""
    async with db.get_db() as conn:
        rows = await conn.query(f"SELECT * FROM customer:`{customer_id}`")
        if not rows:
            return {"error": f"Customer not found: {customer_id}"}
        customer = rows[0]
        customer["id"] = str_id(customer.get("id", ""))
        return customer


@router.get("/customers/{customer_id}/orders")
async def get_customer_orders(customer_id: str):
    """Return user's order history with product details."""
    async with db.get_db() as conn:
        # Verify customer exists
        user_rows = await conn.query(f"SELECT id FROM customer:`{customer_id}`")
        if not user_rows:
            return {"error": f"Customer not found: {customer_id}"}

        # Get orders via placed edge (customer -> placed -> order)
        result = await conn.query(
            f"SELECT ->placed->order.* AS orders FROM customer:`{customer_id}`"
        )
        orders = result[0].get("orders", []) if result else []

        # Enrich each order with product details
        enriched = []
        for order in orders:
            oid = str(order.get("id", ""))
            order["id"] = str_id(oid)

            # Get products in this order (order -> contains -> product)
            prod_result = await conn.query(
                f"SELECT ->contains->product.{{id, name, price, image_url, subcategory}} "
                f"AS products FROM {oid}"
            )
            products = prod_result[0].get("products", []) if prod_result else []
            for p in products:
                p["id"] = str_id(p.get("id", ""))
            order["products"] = products
            enriched.append(order)

        return enriched


@router.get("/customers/{customer_id}/recommendations")
async def get_customer_recommendations(customer_id: str):
    """Get recommended products based on purchase history (also_bought edges)."""
    async with db.get_db() as conn:
        # Get products the customer has bought
        bought_result = await conn.query(
            f"SELECT ->placed->order->contains->product.id AS bought FROM customer:`{customer_id}`"
        )
        bought_ids = bought_result[0].get("bought", []) if bought_result else []
        if not bought_ids:
            return []

        bought_set = {str(pid) for pid in bought_ids}

        # Follow also_bought edges from purchased products
        recs: dict[str, dict] = {}
        for pid in bought_ids:
            pid_str = str(pid)
            ab_result = await conn.query(
                f"SELECT ->also_bought->product.{{id, name, price, avg_rating, image_url, subcategory, brand}} "
                f"AS recs FROM {pid_str}"
            )
            ab_products = ab_result[0].get("recs", []) if ab_result else []
            for p in ab_products:
                rid = str(p.get("id", ""))
                if rid not in bought_set and rid not in recs:
                    p["id"] = str_id(rid)
                    recs[rid] = p

        # Return top 10 by rating
        sorted_recs = sorted(recs.values(), key=lambda x: x.get("avg_rating", 0) or 0, reverse=True)
        return sorted_recs[:10]
