"""Read landing files, chunk, hash, embed, upsert into documents (Layer 3)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import db
from ingestion.logutil import logger
from ingestion.chunking import chunk_markdown_policy
from ingestion.hashing import chunk_record_key, content_hash

# Default landing dir: taro-api/content/policy/
_DEFAULT_POLICY_DIR = Path(__file__).resolve().parent.parent.parent / "content" / "policy"


def _embeddings():
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(model="text-embedding-3-small")


def _title_from_markdown(source_text: str, source_key: str) -> str:
    for line in source_text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return source_key.replace("policy/", "").replace(".md", "").replace("_", " ").title()


async def delete_policy_by_source_key(conn, source_key: str) -> None:
    """Remove all document rows for this source_key."""
    await conn.query(
        "DELETE documents WHERE doc_type = 'policy' AND metadata.source_key = $sk",
        {"sk": source_key},
    )


async def ingest_policy_file(
    path: Path | str,
    *,
    source_key: str | None = None,
    policy_dir: Path | None = None,
) -> dict:
    """
    Ingest one markdown file into documents as doc_type=policy.

    source_key: e.g. policy/shipping.md (default: path relative to content/)
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)

    policy_root = policy_dir or _DEFAULT_POLICY_DIR
    content_dir = policy_root.parent  # .../content

    text = path.read_text(encoding="utf-8")
    if source_key is None:
        try:
            rel = path.resolve().relative_to(content_dir)
            source_key = str(rel).replace("\\", "/")
        except ValueError:
            source_key = f"policy/{path.name}"

    chunks = chunk_markdown_policy(text)
    if not chunks:
        return {"source_key": source_key, "chunks": 0, "ids": []}

    embeddings = _embeddings()
    indexed_at = datetime.now(timezone.utc).isoformat()
    stats: dict = {"source_key": source_key, "chunks": 0, "ids": []}

    async with db.get_db() as conn:
        await delete_policy_by_source_key(conn, source_key)

        vecs = await embeddings.aembed_documents(chunks)

        for idx, (chunk, vec) in enumerate(zip(chunks, vecs)):
            ch = content_hash(chunk)
            rid_suffix = chunk_record_key(source_key, idx, ch)
            # Must match seed.py: CREATE documents:`faq_0` — backticks wrap ONLY the record id
            # segment, not `documents:...`. Wrapping `documents:pol_...` breaks the statement;
            # rows never show up in SELECT FROM documents.
            record_key = f"pol_{rid_suffix}"
            record_id = f"documents:{record_key}"
            title = _title_from_markdown(text, source_key)
            if len(chunks) > 1:
                title = f"{title} (part {idx + 1}/{len(chunks)})"

            meta = {
                "source_key": source_key,
                "chunk_index": idx,
                "content_hash": ch,
                "indexed_at": indexed_at,
                "version": "",
            }

            await conn.query(
                f"CREATE documents:`{record_key}` SET doc_type = 'policy', title = $title, content = $content, "
                "metadata = $meta, embedding = $embedding, source_id = NONE",
                {
                    "title": title,
                    "content": chunk,
                    "meta": meta,
                    "embedding": vec,
                },
            )
            stats["chunks"] += 1
            stats["ids"].append(record_id)

    logger.info(f"Ingested policy {source_key}: {stats['chunks']} chunks")
    return stats


async def _verify_policy_rows_visible(ingest_report: list[dict]) -> None:
    """Confirm rows landed in the same DB Studio should use (catch env / instance mismatches)."""
    expected = sum(r.get("chunks", 0) for r in ingest_report)
    if expected <= 0:
        return
    logger.info(
        f"Verifying policy rows against url={db.SURREALDB_URL} "
        f"namespace={db.SURREALDB_NAMESPACE} database={db.SURREALDB_DATABASE}"
    )
    async with db.get_db() as conn:
        raw = await conn.query(
            "SELECT id FROM documents WHERE doc_type = 'policy' LIMIT 100"
        )
    if raw is None:
        rows: list = []
    elif isinstance(raw, tuple):
        rows = list(raw)
    elif isinstance(raw, list):
        rows = raw
    else:
        rows = [raw]
    n = len(rows)
    if n == 0:
        logger.error(
            "ingest-policy reported chunks, but SELECT found no doc_type='policy' rows in this "
            "namespace/database. Common causes: (1) Surrealist / Studio connected to a different "
            "Surreal process or port than SURREALDB_URL; (2) shell env set SURREALDB_NAMESPACE / "
            "SURREALDB_DATABASE and dotenv did not override — run `env | grep SURREAL` and "
            "`unset` stray vars, or ensure .config/.env lists the target NS/DB; (3) DB was wiped "
            "or replaced after ingest (e.g. switched surrealdb-memory vs rocksdb data dir)."
        )
    else:
        logger.info(f"Verified {n} policy row(s) visible in SurrealDB (expect ~{expected} total)")


async def ingest_policy_dir(policy_dir: Path | None = None) -> list[dict]:
    """Ingest all .md files under policy dir (default: content/policy)."""
    root = policy_dir or _DEFAULT_POLICY_DIR
    if not root.is_dir():
        logger.warning(f"Policy content dir missing: {root}")
        return []

    out = []
    for p in sorted(root.glob("**/*.md")):
        out.append(await ingest_policy_file(p, policy_dir=root))
    if out:
        await _verify_policy_rows_visible(out)
    return out
