"""FastAPI entry point for Taro.ai chatbot."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from env_bootstrap import load_app_dotenv

load_app_dotenv()

# Default LangSmith API host (US). Override with LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com for EU.
_LANGSMITH_DEFAULT_API = "https://api.smith.langchain.com"

# LangSmith — must run before LangChain imports.
# If LANGSMITH_TRACING=true but the key is empty (placeholder .env), force tracing off to avoid 403 spam.
# If LANGSMITH_TRACING is unset, do not override LANGCHAIN_* (supports shell-only LangChain config).
_smith_on = os.getenv("LANGSMITH_TRACING", "").lower() == "true"
_key = (os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY") or "").strip()
if _smith_on:
    if _key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = _key
        os.environ.setdefault("LANGCHAIN_PROJECT", os.getenv("LANGSMITH_PROJECT", "taro-ai-hackathon"))
        ep = (os.getenv("LANGSMITH_ENDPOINT") or _LANGSMITH_DEFAULT_API).strip()
        os.environ.setdefault("LANGCHAIN_ENDPOINT", ep)
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"

import agent as agent_module
from routes.chat import router as chat_router
from routes.conversations import router as conversations_router
from routes.products import router as products_router
from routes.customers import router as customers_router
from routes.preferences import router as preferences_router
from routes.catalog import router as catalog_router
from routes.config import router as config_router
from routes.documents import router as documents_router
from routes.ingestion_route import router as ingestion_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    import db as db_mod

    logger.info("Starting Taro.ai chatbot...")
    logger.info(
        f"SurrealDB: url={db_mod.SURREALDB_URL} namespace={db_mod.SURREALDB_NAMESPACE} "
        f"database={db_mod.SURREALDB_DATABASE} (policy chunks must exist here for find/grep)"
    )
    agent_module.init_default_agent()
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

app.include_router(chat_router)
app.include_router(conversations_router)
app.include_router(products_router)
app.include_router(customers_router)
app.include_router(preferences_router)
app.include_router(catalog_router)
app.include_router(config_router)
app.include_router(documents_router)
app.include_router(ingestion_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8002")), reload=True)
