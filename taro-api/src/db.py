"""SurrealDB connection management."""

import os
from contextlib import asynccontextmanager
from functools import lru_cache

from dotenv import load_dotenv
from loguru import logger
from surrealdb import AsyncSurreal

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

SURREALDB_URL = os.getenv("SURREALDB_URL", "ws://localhost:8000/rpc")
SURREALDB_NAMESPACE = os.getenv("SURREALDB_NAMESPACE", "hackathon")
SURREALDB_DATABASE = os.getenv("SURREALDB_DATABASE", "chatbot")
SURREALDB_USER = os.getenv("SURREALDB_USER", "root")
SURREALDB_PASS = os.getenv("SURREALDB_PASS", "root")


@lru_cache(maxsize=1)
def get_db_config() -> dict:
    """Return config dict for SurrealSaver and other consumers."""
    return {
        "url": SURREALDB_URL,
        "namespace": SURREALDB_NAMESPACE,
        "database": SURREALDB_DATABASE,
        "user": SURREALDB_USER,
        "password": SURREALDB_PASS,
    }


@asynccontextmanager
async def get_db():
    """Async context manager that yields a connected AsyncSurreal instance.

    Usage:
        async with get_db() as db:
            result = await db.query("SELECT * FROM documents")
    """
    async with AsyncSurreal(SURREALDB_URL) as db:
        await db.signin({"username": SURREALDB_USER, "password": SURREALDB_PASS})
        await db.use(SURREALDB_NAMESPACE, SURREALDB_DATABASE)
        yield db
