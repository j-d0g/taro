"""Seed remaining product documents with retry logic.

Usage: python schema/seed_docs.py
"""

import asyncio
import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

from db import get_db

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "Datasets", "trimmed")
BATCH = 25


def read_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def safe_float(val):
    try:
        return float(val) if val else None
    except ValueError:
        return None


async def main():
    products_raw = read_csv("products.csv")
    print(f"Products: {len(products_raw)}")

    async with get_db() as db:
        existing = await db.query("SELECT id FROM documents WHERE doc_type = 'product'")
        existing_ids = set()
        if existing:
            for r in existing:
                rid = str(r.get("id", ""))
                if ":" in rid:
                    existing_ids.add(rid.split(":")[-1].strip("`"))
        print(f"Already seeded: {len(existing_ids)} product docs")

    to_seed = []
    for row in products_raw:
        doc_id = f"prod_{row['product_id'][:16]}"
        if doc_id not in existing_ids:
            to_seed.append(row)

    print(f"Remaining: {len(to_seed)} product docs")
    if not to_seed:
        print("Nothing to do!")
        return

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    for i in range(0, len(to_seed), BATCH):
        batch = to_seed[i: i + BATCH]
        texts = [f"{row['product_name']}: {row.get('description', '') or ''}" for row in batch]
        vecs = await embeddings.aembed_documents(texts)

        for attempt in range(3):
            try:
                async with get_db() as db:
                    for row, vec in zip(batch, vecs):
                        pid = row["product_id"]
                        doc_id = f"prod_{pid[:16]}"
                        content = f"{row['product_name']}: {row.get('description', '') or ''}"
                        await db.query(
                            f"CREATE documents:`{doc_id}` SET "
                            "doc_type = 'product', title = $title, content = $content, "
                            "metadata = $meta, embedding = $embedding",
                            {
                                "title": row["product_name"],
                                "content": content,
                                "meta": {
                                    "product_id": pid,
                                    "price": safe_float(row.get("price", "")),
                                    "vertical": row.get("vertical") or None,
                                    "subcategory": row.get("subcategory") or None,
                                },
                                "embedding": vec,
                            },
                        )
                break
            except Exception as e:
                if attempt < 2:
                    wait = 10 * (attempt + 1)
                    print(f"  Retry in {wait}s... ({e})")
                    await asyncio.sleep(wait)
                else:
                    print(f"  FAILED batch {i}: {e}")

        print(f"  {min(i + BATCH, len(to_seed))}/{len(to_seed)}")

    async with get_db() as db:
        result = await db.query("SELECT count(), doc_type FROM documents GROUP BY doc_type")
        print(f"\nFinal: {result}")
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
