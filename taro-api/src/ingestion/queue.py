"""Layer 2: async ingestion queue abstraction (none | file | redis)."""

from __future__ import annotations

import asyncio
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from ingestion.events import IngestionEvent
from ingestion.logutil import logger

if TYPE_CHECKING:
    pass


class IngestionQueue(ABC):
    @abstractmethod
    async def enqueue(self, event: IngestionEvent) -> None:
        pass

    @abstractmethod
    async def dequeue(self, timeout_sec: float = 5.0) -> IngestionEvent | None:
        pass


class NullQueue(IngestionQueue):
    """No queue; use direct processor calls."""

    async def enqueue(self, event: IngestionEvent) -> None:
        logger.debug(f"NullQueue drop: {event.source_key}")

    async def dequeue(self, timeout_sec: float = 5.0) -> IngestionEvent | None:
        await asyncio.sleep(timeout_sec)
        return None


class FileQueue(IngestionQueue):
    """Append-only JSONL under taro-api/.ingest_queue/pending.jsonl."""

    def __init__(self, base_dir: Path | None = None):
        api_root = Path(__file__).resolve().parent.parent.parent
        self._path = (base_dir or api_root / ".ingest_queue") / "pending.jsonl"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.touch()

    async def enqueue(self, event: IngestionEvent) -> None:
        line = json.dumps(event.to_json()) + "\n"

        def _append():
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(line)

        await asyncio.to_thread(_append)

    async def dequeue(self, timeout_sec: float = 5.0) -> IngestionEvent | None:
        deadline = asyncio.get_event_loop().time() + timeout_sec
        while asyncio.get_event_loop().time() < deadline:
            ev = await asyncio.to_thread(self._pop_one)
            if ev:
                return ev
            await asyncio.sleep(0.2)
        return None

    def _pop_one(self) -> IngestionEvent | None:
        if not self._path.exists() or self._path.stat().st_size == 0:
            return None
        lines = self._path.read_text(encoding="utf-8").splitlines()
        if not lines:
            return None
        first, rest = lines[0], lines[1:]
        self._path.write_text("\n".join(rest) + ("\n" if rest else ""), encoding="utf-8")
        return IngestionEvent.from_json(json.loads(first))


class RedisQueue(IngestionQueue):
    """Simple Redis list queue (LPUSH / BRPOP). Optional dependency."""

    def __init__(self, url: str, key: str = "taro:ingest"):
        try:
            import redis.asyncio as ai_redis
        except ImportError as e:
            raise RuntimeError("Install redis package for RedisQueue: pip install redis") from e
        self._redis = ai_redis.from_url(url, decode_responses=True)
        self._key = key

    async def enqueue(self, event: IngestionEvent) -> None:
        await self._redis.lpush(self._key, json.dumps(event.to_json()))

    async def dequeue(self, timeout_sec: float = 5.0) -> IngestionEvent | None:
        r = await self._redis.brpop(self._key, timeout=int(max(1, timeout_sec)))
        if not r:
            return None
        _, payload = r
        return IngestionEvent.from_json(json.loads(payload))


def get_queue() -> IngestionQueue:
    backend = os.getenv("INGESTION_BACKEND", "none").lower().strip()
    if backend in ("none", "", "null"):
        return NullQueue()
    if backend == "file":
        return FileQueue()
    if backend == "redis":
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        return RedisQueue(url)
    logger.warning(f"Unknown INGESTION_BACKEND={backend}, using NullQueue")
    return NullQueue()
