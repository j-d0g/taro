"""Prefer loguru; fall back to stdlib logging (shared by db, ingestion CLI, etc.)."""

from __future__ import annotations

try:
    from loguru import logger
except ImportError:
    import logging

    _log = logging.getLogger("taro")
    if not logging.root.handlers and not _log.handlers:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logger = _log  # type: ignore[misc,assignment]
