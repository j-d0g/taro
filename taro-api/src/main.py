"""FastAPI entry point for Taro.ai chatbot."""

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
from graph import DEFAULT_MODEL, DEFAULT_PROVIDER, build_graph
from prompts.system import list_prompts, load_prompt


# ── Models ───────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    channel: str = "myprotein"
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    prompt_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    tool_calls: list[dict] = []


AVAILABLE_MODELS = {
    "openai": {"default_model": "gpt-4o", "models": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"]},
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


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the chatbot."""
    logger.info(f"Chat request: thread={request.thread_id}, message='{request.message[:80]}'")

    agent = _get_agent(request.model_provider, request.model_name, request.prompt_id)

    config = {"configurable": {"thread_id": request.thread_id}}
    input_msg = {"messages": [HumanMessage(content=request.message)]}

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

    return ChatResponse(reply=reply, thread_id=request.thread_id, tool_calls=tool_calls)


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
    limit: int = 100,
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
            f"LIMIT {min(limit, 200)} START {offset}"
        )
        rows = await db.query(surql, params)

        for row in rows:
            row["id"] = _str_id(row.get("id", ""))
        return rows


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


@app.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    """Return user profile by ID."""
    async with get_db() as db:
        rows = await db.query(f"SELECT * FROM user:`{customer_id}`")
        if not rows:
            return {"error": f"Customer not found: {customer_id}"}
        user = rows[0]
        user["id"] = _str_id(user.get("id", ""))
        return user


@app.get("/customers/{customer_id}/orders")
async def get_customer_orders(customer_id: str):
    """Return user's order history with product details."""
    async with get_db() as db:
        # Verify user exists
        user_rows = await db.query(f"SELECT id FROM user:`{customer_id}`")
        if not user_rows:
            return {"error": f"Customer not found: {customer_id}"}

        # Get orders via placed_by edge (user -> placed_by -> order)
        result = await db.query(
            f"SELECT ->placed_by->order.* AS orders FROM user:`{customer_id}`"
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
        # Get products the user has bought
        bought_result = await db.query(
            f"SELECT ->placed_by->order->contains->product.id AS bought FROM user:`{customer_id}`"
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
