"""FastAPI entry point for Taro.ai chatbot."""

import json
import os
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from loguru import logger
from pydantic import BaseModel, Field

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

# Activate LangSmith tracing (env vars must be set before LangChain imports)
if os.getenv("LANGSMITH_TRACING", "").lower() == "true":
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_API_KEY", os.getenv("LANGSMITH_API_KEY", ""))
    os.environ.setdefault("LANGCHAIN_PROJECT", os.getenv("LANGSMITH_PROJECT", "taro-ai-hackathon"))

from db import get_db
from graph import DEFAULT_MODEL, DEFAULT_PROVIDER, build_graph, get_llm
from prompts.system import list_prompts, load_prompt


# ── Models ───────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None  # e.g. "diego_carvalho" for personalized context
    channel: str = "lookfantastic"
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    prompt_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    tool_calls: list[dict] = []
    products: list[dict] = []


class DistillRequest(BaseModel):
    thread_id: str
    user_id: str  # e.g. "diego_carvalho"


class DistillResponse(BaseModel):
    user_id: str
    context: str
    updated: bool


AVAILABLE_MODELS = {
    "openai": {"default_model": "gpt-4o", "models": ["gpt-5.4", "gpt-5.2", "gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"]},
    "anthropic": {"default_model": "claude-sonnet-4-20250514", "models": ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"]},
    "google": {"default_model": "gemini-2.0-flash", "models": ["gemini-2.0-flash", "gemini-2.5-pro-preview-06-05"]},
}


# ── App ──────────────────────────────────────────────────────

_default_agent = None
_agent_cache: dict[tuple, object] = {}


def _get_agent(provider: Optional[str], model: Optional[str], prompt_id: str):
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _default_agent
    logger.info("Starting Taro.ai chatbot...")
    _default_agent = build_graph()
    logger.info("Agent ready")
    yield
    logger.info("Shutting down")


app = FastAPI(title="Taro.ai", description="SurrealDB Agentic Search Chatbot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _load_conversation(db, thread_id: str) -> list[dict]:
    """Load conversation messages from SurrealDB."""
    result = await db.query(
        "SELECT messages FROM conversation WHERE thread_id = $tid",
        {"tid": thread_id},
    )
    if result and isinstance(result[0], dict):
        return result[0].get("messages", [])
    return []


async def _save_conversation(db, thread_id: str, user_id: str | None, user_msg: str, assistant_msg: str, tool_calls: list[dict]):
    """Append messages to conversation in SurrealDB."""
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    new_messages = [
        {"role": "user", "content": user_msg, "timestamp": now},
        {"role": "assistant", "content": assistant_msg, "tool_calls": tool_calls, "timestamp": now},
    ]

    # Upsert: create or append
    existing = await db.query(
        "SELECT id, messages FROM conversation WHERE thread_id = $tid",
        {"tid": thread_id},
    )

    if existing and isinstance(existing[0], dict) and "id" in existing[0]:
        # Append to existing
        old_messages = existing[0].get("messages", [])
        all_messages = old_messages + new_messages
        conv_id = str(existing[0]["id"])
        await db.query(
            f"UPDATE {conv_id} SET messages = $msgs, updated_at = time::now()",
            {"msgs": all_messages},
        )
    else:
        # Create new
        await db.query(
            "CREATE conversation SET thread_id = $tid, user_id = $uid, "
            "messages = $msgs, created_at = time::now(), updated_at = time::now()",
            {"tid": thread_id, "uid": user_id, "msgs": new_messages},
        )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the chatbot."""
    logger.info(f"Chat request: thread={request.thread_id}, message='{request.message[:80]}'")

    try:
        agent = _get_agent(request.model_provider, request.model_name, request.prompt_id)

        config = {"configurable": {"thread_id": request.thread_id}}

        # Inject user context if user_id provided
        user_context = ""
        if request.user_id:
            try:
                from db import get_db
                async with get_db() as db:
                    user_result = await db.query(
                        f"SELECT * FROM customer:{request.user_id}"
                    )
                    if user_result:
                        user = user_result[0] if isinstance(user_result[0], dict) and "id" in user_result[0] else (user_result[0].get("result", [{}])[0] if isinstance(user_result[0], dict) else {})
                        if user:
                            name = user.get("name", request.user_id)
                            parts = [f"\n[User: {name} — customer:{request.user_id}]"]
                            # Graph hint so agent can traverse
                            parts.append(f"Graph entry: cat /users/{request.user_id} or graph_traverse('customer:{request.user_id}', 'placed')")
                            # Profile fields
                            if user.get("bio"):
                                parts.append(f"Bio: {user['bio']}")
                            if user.get("skin_type"):
                                parts.append(f"Skin type: {user['skin_type']}")
                            if user.get("hair_type"):
                                parts.append(f"Hair type: {user['hair_type']}")
                            if user.get("concerns"):
                                parts.append(f"Concerns: {', '.join(user['concerns'])}")
                            if user.get("allergies"):
                                parts.append(f"Allergies: {', '.join(user['allergies'])}")
                            if user.get("goals"):
                                parts.append(f"Goals: {', '.join(user['goals'])}")
                            if user.get("preferences"):
                                parts.append(f"Preferences: {', '.join(user['preferences'])}")
                            if user.get("preferred_brands"):
                                parts.append(f"Preferred brands: {', '.join(user['preferred_brands'])}")
                            if user.get("dietary_restrictions"):
                                parts.append(f"Dietary: {', '.join(user['dietary_restrictions'])}")
                            if user.get("context"):
                                parts.append(f"Previous context: {user['context']}")
                            if user.get("memory"):
                                parts.append(f"Key facts: {'; '.join(user['memory'])}")
                            user_context = " | ".join(parts)
            except Exception as ue:
                logger.warning(f"Failed to load user context: {ue}")

        message_content = request.message
        if user_context:
            message_content = f"{user_context}\n\n{request.message}"

        input_msg = {"messages": [HumanMessage(content=message_content)]}

        result = await agent.ainvoke(input_msg, config=config)

        # Extract final response
        messages = result.get("messages", [])
        reply = messages[-1].content if messages else "I couldn't generate a response."

        # Extract tool calls from message history
        tool_calls = []
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls.append({"name": tc.get("name", ""), "args": tc.get("args", {})})

        # Extract product data from tool result messages
        products: list[dict] = []
        seen_product_names: set[str] = set()
        for msg in messages:
            if msg.__class__.__name__ == "ToolMessage" and isinstance(msg.content, str):
                try:
                    data = json.loads(msg.content)
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if isinstance(item, dict) and "name" in item and "price" in item:
                            pname = item["name"]
                            if pname not in seen_product_names:
                                seen_product_names.add(pname)
                                products.append({
                                    "id": _str_id(item.get("id", "")),
                                    "name": pname,
                                    "price": item.get("price"),
                                    "avg_rating": item.get("avg_rating"),
                                    "image_url": item.get("image_url", ""),
                                    "vertical": item.get("vertical", ""),
                                    "subcategory": item.get("subcategory", ""),
                                })
                except (json.JSONDecodeError, TypeError):
                    pass

        # Persist conversation
        try:
            async with get_db() as db:
                await _save_conversation(
                    db, request.thread_id, request.user_id,
                    request.message, reply, tool_calls,
                )
        except Exception as save_err:
            logger.warning(f"Failed to save conversation: {save_err}")

        return ChatResponse(reply=reply, thread_id=request.thread_id, tool_calls=tool_calls, products=products)
    except Exception as e:
        import traceback
        error_type = type(e).__name__
        logger.error(f"Chat error ({error_type}): {e}\n{traceback.format_exc()}")

        # Retry once on rate limit errors
        if "RateLimit" in error_type or "rate_limit" in str(e).lower():
            import asyncio
            logger.info("Rate limited, retrying after 5s backoff...")
            await asyncio.sleep(5)
            try:
                result = await agent.ainvoke(input_msg, config=config)
                messages = result.get("messages", [])
                reply = messages[-1].content if messages else "I couldn't generate a response."
                tool_calls = []
                for msg in messages:
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            tool_calls.append({"name": tc.get("name", ""), "args": tc.get("args", {})})
                return ChatResponse(reply=reply, thread_id=request.thread_id, tool_calls=tool_calls)
            except Exception as retry_err:
                logger.error(f"Retry also failed: {retry_err}")

        return ChatResponse(
            reply=f"I encountered an error processing your request: {error_type}. Please try again.",
            thread_id=request.thread_id,
            tool_calls=[],
        )


@app.get("/conversations/{thread_id}")
async def get_conversation(thread_id: str):
    """Get conversation history by thread ID."""
    async with get_db() as db:
        result = await db.query(
            "SELECT * FROM conversation WHERE thread_id = $tid",
            {"tid": thread_id},
        )
        if not result:
            return {"error": "Conversation not found"}
        conv = result[0]
        conv["id"] = _str_id(conv.get("id", ""))
        return conv


@app.get("/conversations")
async def list_conversations(user_id: Optional[str] = None, limit: int = 20):
    """List recent conversations, optionally filtered by user."""
    async with get_db() as db:
        if user_id:
            result = await db.query(
                "SELECT thread_id, user_id, created_at, updated_at, "
                "array::len(messages) AS message_count "
                "FROM conversation WHERE user_id = $uid "
                "ORDER BY updated_at DESC LIMIT $lim",
                {"uid": user_id, "lim": limit},
            )
        else:
            result = await db.query(
                "SELECT thread_id, user_id, created_at, updated_at, "
                "array::len(messages) AS message_count "
                "FROM conversation ORDER BY updated_at DESC LIMIT $lim",
                {"lim": limit},
            )
        for r in result:
            r["id"] = _str_id(r.get("id", ""))
        return result


@app.post("/distill", response_model=DistillResponse)
async def distill(request: DistillRequest):
    """Distill conversation context into user memory.

    After a chat session, call this to extract key preferences, interests,
    and insights from the conversation and persist them in the user's
    context field in SurrealDB.
    """
    logger.info(f"Distill request: user={request.user_id}, thread={request.thread_id}")
    try:
        from db import get_db

        # Try persisted conversation first, fall back to checkpointer
        messages = []
        async with get_db() as db:
            conv_messages = await _load_conversation(db, request.thread_id)
            if conv_messages:
                from langchain_core.messages import HumanMessage as HM, AIMessage
                for m in conv_messages:
                    if m["role"] == "user":
                        messages.append(HM(content=m["content"]))
                    elif m["role"] == "assistant":
                        messages.append(AIMessage(content=m["content"]))

        # Fall back to checkpointer (in-memory, won't survive restart)
        if not messages:
            agent = _get_agent(None, None, "default")
            config = {"configurable": {"thread_id": request.thread_id}}
            state = await agent.aget_state(config)
            messages = state.values.get("messages", [])

        if not messages:
            return DistillResponse(user_id=request.user_id, context="", updated=False)

        # Build conversation summary for distillation
        convo_lines = []
        for msg in messages[-20:]:  # Last 20 messages max
            role = msg.__class__.__name__.replace("Message", "")
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            if content and len(content) > 10:  # Skip tool results noise
                convo_lines.append(f"{role}: {content[:300]}")
        convo_text = "\n".join(convo_lines)

        # Load existing context
        existing_context = ""
        async with get_db() as db:
            user_result = await db.query(f"SELECT context FROM customer:{request.user_id}")
            if user_result and isinstance(user_result[0], dict):
                existing_context = user_result[0].get("context", "") or ""

        # Use the LLM to distill
        from langchain_core.messages import HumanMessage as HM
        llm = get_llm()
        distill_prompt = (
            "You are a context distiller. Given a conversation between a user and a product assistant, "
            "extract the key preferences, interests, goals, and any insights about the user. "
            "Output a concise 2-4 sentence summary that would help personalize future conversations.\n\n"
            f"Existing context (merge with, don't lose): {existing_context}\n\n"
            f"Conversation:\n{convo_text}\n\n"
            "Distilled context:"
        )
        result = await llm.ainvoke([HM(content=distill_prompt)])
        new_context = result.content.strip()

        # Update user record
        async with get_db() as db:
            await db.query(
                f"UPDATE customer:{request.user_id} SET context = $context",
                {"context": new_context},
            )

        return DistillResponse(user_id=request.user_id, context=new_context, updated=True)
    except Exception as e:
        logger.error(f"Distill error: {e}")
        return DistillResponse(user_id=request.user_id, context=str(e), updated=False)


def _str_id(record_id) -> str:
    """Convert a SurrealDB RecordID to a plain string key."""
    s = str(record_id)
    # Strip table prefix (e.g. "product:abc123" -> "abc123")
    return s.split(":", 1)[1] if ":" in s else s


@app.get("/products")
async def list_products(
    vertical: Optional[str] = None,
    search: Optional[str] = None,
    brand: Optional[str] = None,
    limit: int = 2000,
    offset: int = 0,
):
    """List products with optional filters and pagination."""
    async with get_db() as db:
        where_clauses = []
        params: dict = {}

        if vertical:
            where_clauses.append("vertical = $vertical")
            params["vertical"] = vertical
        if search:
            where_clauses.append("(name ~ $search OR description ~ $search OR subcategory ~ $search)")
            params["search"] = search
        if brand:
            where_clauses.append("brand = $brand")
            params["brand"] = brand

        where = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        surql = (
            "SELECT id, name, vertical, subcategory, price, avg_rating, brand, "
            f"image_url, description FROM product{where} ORDER BY name "
            f"LIMIT {min(limit, 2000)} START {offset}"
        )
        rows = await db.query(surql, params)

        # Deduplicate by product name (CSV has ~1890 rows but only ~355 unique)
        seen: dict[str, bool] = {}
        deduped: list[dict] = []
        for row in rows:
            name = row.get("name", "")
            if name not in seen:
                seen[name] = True
                row["id"] = _str_id(row.get("id", ""))
                deduped.append(row)
        return deduped


@app.get("/products/{product_id}")
async def get_product(product_id: str):
    """Get product detail with also_bought graph edges and reviews."""
    async with get_db() as db:
        # Product record
        rows = await db.query(f"SELECT * FROM product:`{product_id}`")
        if not rows:
            return {"error": f"Product not found: {product_id}"}
        product = rows[0]
        product["id"] = _str_id(product.get("id", ""))

        # Also bought (product -> also_bought -> product)
        ab_rows = await db.query(
            f"SELECT ->also_bought->product.{{id, name, price, avg_rating, image_url, subcategory}} "
            f"AS also_bought FROM product:`{product_id}`"
        )
        also_bought = ab_rows[0].get("also_bought", []) if ab_rows else []
        for ab in also_bought:
            ab["id"] = _str_id(ab.get("id", ""))
        product["also_bought"] = also_bought

        # Reviews via order -> contains -> product, order -> has_review -> review
        rev_rows = await db.query(
            "SELECT id, score, comment, sentiment FROM review "
            f"WHERE <-has_review<-order->contains->product CONTAINS product:`{product_id}` "
            "ORDER BY score DESC LIMIT 10"
        )
        for r in rev_rows:
            r["review_id"] = _str_id(r.pop("id", ""))
        product["reviews"] = rev_rows

        return product


# ── Customer endpoints ──────────────────────────────────────


@app.get("/customers/{customer_id}/profile")
async def get_customer_profile(customer_id: str):
    """Return enriched customer profile with graph-derived data.

    Traverses: customer->placed->order->contains->product,
    order->has_review->review, product->supports_goal->goal,
    product->belongs_to->category.
    """
    async with get_db() as db:
        # 1. Customer record (all fields)
        rows = await db.query(f"SELECT * FROM customer:`{customer_id}`")
        if not rows:
            return {"error": f"Customer not found: {customer_id}"}
        customer = rows[0]
        customer["id"] = _str_id(customer.get("id", ""))

        # 2. Orders with products via graph traversal
        order_result = await db.query(
            f"SELECT ->placed->order.* AS orders FROM customer:`{customer_id}`"
        )
        orders_raw = order_result[0].get("orders", []) if order_result else []

        orders = []
        all_product_ids = []
        total_spent = 0.0
        for order in orders_raw:
            oid = str(order.get("id", ""))
            order["id"] = _str_id(oid)
            total_spent += order.get("price") or order.get("total") or 0

            # Products in this order
            prod_result = await db.query(
                f"SELECT ->contains->product.{{id, name, price, image_url, subcategory, vertical, brand, avg_rating}} "
                f"AS products FROM {oid}"
            )
            products = prod_result[0].get("products", []) if prod_result else []
            for p in products:
                pid_str = str(p.get("id", ""))
                p["id"] = _str_id(pid_str)
                all_product_ids.append(pid_str)
            order["products"] = products
            orders.append(order)

        # 3. Reviews via order->has_review->review
        reviews = []
        review_scores = []
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        for order in orders_raw:
            oid = str(order.get("id", ""))
            rev_result = await db.query(
                f"SELECT ->has_review->review.* AS reviews FROM {oid}"
            )
            order_reviews = rev_result[0].get("reviews", []) if rev_result else []
            for r in order_reviews:
                r["id"] = _str_id(r.get("id", ""))
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
            goal_result = await db.query(
                f"SELECT ->supports_goal->goal.{{id, name, description}} AS goals FROM {pid}"
            )
            g_list = goal_result[0].get("goals", []) if goal_result else []
            for g in g_list:
                gname = g.get("name", "")
                if gname and gname not in seen_goals:
                    seen_goals.add(gname)
                    g["id"] = _str_id(g.get("id", ""))
                    goals.append(g)

        # 5. Top categories via product->belongs_to->category
        cat_counts: dict[str, int] = {}
        cat_names: dict[str, str] = {}
        for pid in all_product_ids:
            cat_result = await db.query(
                f"SELECT ->belongs_to->category.{{id, name}} AS cats FROM {pid}"
            )
            cats = cat_result[0].get("cats", []) if cat_result else []
            for c in cats:
                cname = c.get("name", "")
                if cname:
                    cat_counts[cname] = cat_counts.get(cname, 0) + 1
                    cat_names[cname] = _str_id(c.get("id", ""))

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


@app.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    """Return customer profile by ID."""
    async with get_db() as db:
        rows = await db.query(f"SELECT * FROM customer:`{customer_id}`")
        if not rows:
            return {"error": f"Customer not found: {customer_id}"}
        customer = rows[0]
        customer["id"] = _str_id(customer.get("id", ""))
        return customer


@app.get("/customers/{customer_id}/orders")
async def get_customer_orders(customer_id: str):
    """Return user's order history with product details."""
    async with get_db() as db:
        # Verify customer exists
        user_rows = await db.query(f"SELECT id FROM customer:`{customer_id}`")
        if not user_rows:
            return {"error": f"Customer not found: {customer_id}"}

        # Get orders via placed edge (customer -> placed -> order)
        result = await db.query(
            f"SELECT ->placed->order.* AS orders FROM customer:`{customer_id}`"
        )
        orders = result[0].get("orders", []) if result else []

        # Enrich each order with product details
        enriched = []
        for order in orders:
            oid = str(order.get("id", ""))
            order["id"] = _str_id(oid)

            # Get products in this order (order -> contains -> product)
            prod_result = await db.query(
                f"SELECT ->contains->product.{{id, name, price, image_url, subcategory}} "
                f"AS products FROM {oid}"
            )
            products = prod_result[0].get("products", []) if prod_result else []
            for p in products:
                p["id"] = _str_id(p.get("id", ""))
            order["products"] = products
            enriched.append(order)

        return enriched


@app.get("/customers/{customer_id}/recommendations")
async def get_customer_recommendations(customer_id: str):
    """Get recommended products based on purchase history (also_bought edges)."""
    async with get_db() as db:
        # Get products the customer has bought
        bought_result = await db.query(
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
            ab_result = await db.query(
                f"SELECT ->also_bought->product.{{id, name, price, avg_rating, image_url, subcategory, brand}} "
                f"AS recs FROM {pid_str}"
            )
            ab_products = ab_result[0].get("recs", []) if ab_result else []
            for p in ab_products:
                rid = str(p.get("id", ""))
                if rid not in bought_set and rid not in recs:
                    p["id"] = _str_id(rid)
                    recs[rid] = p

        # Return top 10 by rating
        sorted_recs = sorted(recs.values(), key=lambda x: x.get("avg_rating", 0) or 0, reverse=True)
        return sorted_recs[:10]


# ── Category endpoints ──────────────────────────────────────


@app.get("/categories")
async def list_categories():
    """List all categories with hierarchy (verticals with nested subcategories)."""
    async with get_db() as db:
        # Get all categories
        rows = await db.query("SELECT id, name, level, description FROM category")

        verticals = []
        subcats_by_parent: dict[str, list] = {}

        # Get child_of edges to build hierarchy
        edges = await db.query(
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
            row["id"] = _str_id(rid)
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


@app.get("/categories/{category_id}")
async def get_category(category_id: str):
    """Category detail with products."""
    async with get_db() as db:
        cat_rows = await db.query(f"SELECT * FROM category:`{category_id}`")
        if not cat_rows:
            return {"error": f"Category not found: {category_id}"}
        category = cat_rows[0]
        category["id"] = _str_id(category.get("id", ""))

        # Products in this category (product -> belongs_to -> category)
        prod_result = await db.query(
            f"SELECT <-belongs_to<-product.{{id, name, price, avg_rating, brand, image_url, subcategory, dietary_tags}} "
            f"AS products FROM category:`{category_id}`"
        )
        products = prod_result[0].get("products", []) if prod_result else []
        for p in products:
            p["id"] = _str_id(p.get("id", ""))
        category["products"] = products

        # Subcategories (category <- child_of <- category)
        sub_result = await db.query(
            f"SELECT <-child_of<-category.{{id, name}} AS subcategories FROM category:`{category_id}`"
        )
        subs = sub_result[0].get("subcategories", []) if sub_result else []
        for s in subs:
            s["id"] = _str_id(s.get("id", ""))
        category["subcategories"] = subs

        return category


# ── Goal endpoints ──────────────────────────────────────────


@app.get("/goals")
async def list_goals():
    """List all goals."""
    async with get_db() as db:
        rows = await db.query("SELECT id, name, description, vertical FROM goal")
        for row in rows:
            row["id"] = _str_id(row.get("id", ""))
        return rows


@app.get("/goals/{goal_id}")
async def get_goal(goal_id: str):
    """Goal detail with supporting products."""
    async with get_db() as db:
        goal_rows = await db.query(f"SELECT * FROM goal:`{goal_id}`")
        if not goal_rows:
            return {"error": f"Goal not found: {goal_id}"}
        goal = goal_rows[0]
        goal["id"] = _str_id(goal.get("id", ""))

        # Products supporting this goal (product -> supports_goal -> goal)
        prod_result = await db.query(
            f"SELECT <-supports_goal<-product.{{id, name, price, avg_rating, brand, image_url, subcategory, dietary_tags}} "
            f"AS products FROM goal:`{goal_id}`"
        )
        products = prod_result[0].get("products", []) if prod_result else []
        for p in products:
            p["id"] = _str_id(p.get("id", ""))
        goal["products"] = products

        return goal


# ── Existing endpoints ──────────────────────────────────────


@app.get("/verticals")
async def list_verticals():
    """Return distinct product verticals for filter tabs."""
    async with get_db() as db:
        rows = await db.query(
            "SELECT vertical, count() AS count FROM product GROUP BY vertical ORDER BY vertical"
        )
        return [row["vertical"] for row in rows if row.get("vertical")]


@app.get("/models")
async def models():
    """Return available model providers and their models."""
    return {
        "default_provider": DEFAULT_PROVIDER,
        "default_model": DEFAULT_MODEL,
        "providers": AVAILABLE_MODELS,
    }


@app.get("/prompts")
async def prompts():
    """Return available prompt template IDs."""
    return {"prompts": list_prompts(), "default": "default"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "taro-ai"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8002")), reload=True)
