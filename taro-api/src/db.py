"""SurrealDB connection management."""

import os
from contextlib import asynccontextmanager
from functools import lru_cache

from surrealdb import AsyncSurreal

from logutil import logger

from env_bootstrap import load_app_dotenv

load_app_dotenv()

# Default port must match `make surrealdb` (see Makefile / config/.env.example). 8000 was a common footgun.
SURREALDB_URL = os.getenv("SURREALDB_URL", "ws://localhost:8001/rpc")
SURREALDB_NAMESPACE = os.getenv("SURREALDB_NAMESPACE", "hackathon")
SURREALDB_DATABASE = os.getenv("SURREALDB_DATABASE", "chatbot")
SURREALDB_USER = os.getenv("SURREALDB_USER", "root")
SURREALDB_PASS = os.getenv("SURREALDB_PASS", "root")
SURREALDB_TOKEN = os.getenv("SURREALDB_TOKEN", "")


@lru_cache(maxsize=1)
def get_db_config() -> dict:
    """Return config dict for SurrealSaver and other consumers."""
    return {
        "url": SURREALDB_URL,
        "namespace": SURREALDB_NAMESPACE,
        "database": SURREALDB_DATABASE,
        "user": SURREALDB_USER,
        "password": SURREALDB_PASS,
        "token": SURREALDB_TOKEN,
    }


@asynccontextmanager
async def get_db():
    """Async context manager that yields a connected AsyncSurreal instance.

    Supports both token auth (SurrealDB Cloud) and username/password (local).

    Usage:
        async with get_db() as db:
            result = await db.query("SELECT * FROM documents")
    """
    async with AsyncSurreal(SURREALDB_URL) as db:
        if SURREALDB_TOKEN:
            await db.authenticate(SURREALDB_TOKEN)
        else:
            await db.signin({
                "username": SURREALDB_USER,
                "password": SURREALDB_PASS,
            })
        await db.use(SURREALDB_NAMESPACE, SURREALDB_DATABASE)
        yield db
