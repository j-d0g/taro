"""Agent factory and cache for the Taro.ai chatbot."""

from typing import Optional

from loguru import logger

import db
from graph import DEFAULT_MODEL, DEFAULT_PROVIDER, build_graph
from prompts.system import load_prompt


_default_agent = None
_agent_cache: dict[tuple, object] = {}


def init_default_agent():
    """Build and cache the default agent. Called during app lifespan startup."""
    global _default_agent
    _default_agent = build_graph()


def get_agent(provider: Optional[str], model: Optional[str], prompt_id: str):
    """Return a cached agent for the given config, building one if needed."""
    global _default_agent

    # No overrides -> use the default agent
    if not provider and not model and prompt_id == "default":
        return _default_agent

    key = (provider or DEFAULT_PROVIDER, model or DEFAULT_MODEL, prompt_id)
    if key not in _agent_cache:
        logger.info(f"Building new agent for config: {key}")
        _agent_cache[key] = build_graph(
            model_provider=provider,
            model_name=model,
            prompt=load_prompt(prompt_id) if prompt_id != "default" else None,
        )
    return _agent_cache[key]


async def build_message_content(message: str, user_id: str | None) -> str:
    """Prepend user context to the message if user_id is provided."""
    if not user_id:
        return message
    try:
        async with db.get_db() as conn:
            user_result = await conn.query(f"SELECT * FROM customer:{user_id}")
            if not user_result:
                return message
            user = user_result[0] if isinstance(user_result[0], dict) and "id" in user_result[0] else (
                user_result[0].get("result", [{}])[0] if isinstance(user_result[0], dict) else {}
            )
            if not user:
                return message
            name = user.get("name", user_id)
            parts = [f"\n[User: {name} — customer:{user_id}]"]

            # Profile fields
            profile_fields = {
                "bio": "Bio", "skin_type": "Skin type", "hair_type": "Hair type",
                "context": "Previous context",
            }
            list_fields = {
                "concerns": "Concerns", "allergies": "Allergies", "goals": "Goals",
                "preferences": "Preferences", "preferred_brands": "Preferred brands",
                "dietary_restrictions": "Dietary",
            }
            for field, label in profile_fields.items():
                if user.get(field):
                    parts.append(f"{label}: {user[field]}")
            for field, label in list_fields.items():
                if user.get(field):
                    parts.append(f"{label}: {', '.join(user[field])}")
            if user.get("memory"):
                parts.append(f"Key facts: {'; '.join(user['memory'])}")

            # Purchase history via graph traversal
            purchase_rows = await conn.query(
                "SELECT ->placed->order->contains->product.{name, price, subcategory} "
                f"AS products FROM customer:{user_id}"
            )
            bought_products = purchase_rows[0].get("products", []) if purchase_rows else []
            if bought_products:
                purchase_summary = [f"{p['name']} (£{p.get('price', '?')})" for p in bought_products[:8]]
                parts.append(f"Recent purchases: {', '.join(purchase_summary)}")

            # Reviews via graph traversal
            review_rows = await conn.query(
                "SELECT ->placed->order->has_review->review.{score, comment, sentiment} "
                f"AS reviews FROM customer:{user_id}"
            )
            reviews = review_rows[0].get("reviews", []) if review_rows else []
            if reviews:
                review_parts = []
                for r in reviews[:5]:
                    score = r.get("score", "?")
                    comment = r.get("comment", "")
                    snippet = comment[:60] + "..." if len(comment) > 60 else comment
                    sentiment = r.get("sentiment", "")
                    review_parts.append(f"{score}/5 ({sentiment}): \"{snippet}\"")
                parts.append(f"Their reviews: {'; '.join(review_parts)}")

            # Explicit preferences via graph edges
            pref_rows = await conn.query(
                "SELECT "
                "->wants->product.{id, name} AS wants, "
                "->interested_in->product.{id, name} AS saved, "
                "->rejected->product.{id, name} AS rejected "
                f"FROM customer:{user_id}"
            )
            prefs = pref_rows[0] if pref_rows else {}

            def _names(items):
                names = []
                if isinstance(items, list):
                    for it in items:
                        if isinstance(it, dict):
                            n = it.get("name")
                            if n:
                                names.append(str(n))
                return names

            likes = _names(prefs.get("wants", [])) + _names(prefs.get("saved", []))
            dislikes = _names(prefs.get("rejected", []))
            if likes:
                parts.append(f"Likes: {', '.join(likes[:6])}")
            if dislikes:
                parts.append(f"Not interested in: {', '.join(dislikes[:6])}")

            # Graph hint for deeper exploration
            parts.append(f"Graph entry: cat /users/{user_id} or graph_traverse('customer:{user_id}', 'customer_history')")

            return " | ".join(parts) + f"\n\n{message}"
    except Exception as ue:
        logger.warning(f"Failed to load user context: {ue}")
        return message
