"""Preference endpoints: POST /preferences, GET /preferences/{user_id}."""

from fastapi import APIRouter
from loguru import logger

import db
from helpers import str_id
from models import PreferenceRequest
from routes.chat import append_preference_context


router = APIRouter()


@router.post("/preferences")
async def set_preference(request: PreferenceRequest):
    """Record a user's preference for a product (cart/keep/remove)."""
    edge_map = {
        "cart": "wants",
        "keep": "interested_in",
        "remove": "rejected",
    }
    edge_type = edge_map.get(request.action)
    if not edge_type:
        return {"error": f"Invalid action: {request.action}. Use cart, keep, or remove.", "success": False}

    product_name = None
    async with db.get_db() as conn:
        # Remove any existing preference edges for this user-product pair
        for et in edge_map.values():
            await conn.query(
                f"DELETE {et} WHERE in = customer:`{request.user_id}` AND out = product:`{request.product_id}`"
            )

        # Create the new edge
        if request.action == "remove" and request.reason:
            await conn.query(
                f"RELATE customer:`{request.user_id}`->{edge_type}->product:`{request.product_id}` "
                f"SET reason = $reason, added_at = time::now()",
                {"reason": request.reason},
            )
        else:
            await conn.query(
                f"RELATE customer:`{request.user_id}`->{edge_type}->product:`{request.product_id}` "
                f"SET added_at = time::now()"
            )

        # Optionally append preference context to conversation so agent adapts in-session
        if request.thread_id:
            try:
                prod = await conn.query(
                    f"SELECT name FROM product:{request.product_id}"
                )
                if prod and isinstance(prod[0], dict):
                    product_name = prod[0].get("name")
                await append_preference_context(
                    conn, request.thread_id, request.user_id,
                    request.product_id, product_name, request.action, request.reason,
                )
            except Exception as e:
                logger.warning(f"Could not append preference context to thread {request.thread_id}: {e}")

    logger.info(f"Preference: {request.user_id} -> {request.action} -> {request.product_id}")
    return {"action": request.action, "product_id": request.product_id, "success": True}


@router.get("/preferences/{user_id}")
async def get_preferences(user_id: str):
    """Get a user's product preferences (cart, saved, rejected)."""
    async with db.get_db() as conn:
        cart = await conn.query(
            f"SELECT ->wants->product.{{id, name, price, image_url}} AS products FROM customer:`{user_id}`"
        )
        saved = await conn.query(
            f"SELECT ->interested_in->product.{{id, name, price, image_url}} AS products FROM customer:`{user_id}`"
        )
        rejected = await conn.query(
            f"SELECT ->rejected->product.{{id, name, price}} AS products FROM customer:`{user_id}`"
        )

        def extract(result):
            items = result[0].get("products", []) if result else []
            for item in items:
                item["id"] = str_id(item.get("id", ""))
            return items

        return {
            "cart": extract(cart),
            "saved": extract(saved),
            "rejected": extract(rejected),
        }
