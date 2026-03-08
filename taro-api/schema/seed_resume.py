"""Resume seed from step 5 (reviews) onward.

Steps 1-4 (categories, customers, products, orders) already completed.
This script resumes from reviews, then does also_bought edges, then documents.
Reconnects per batch to avoid WebSocket timeouts on cloud.

Usage: python schema/seed_resume.py
"""

import asyncio
import csv
import os
import sys
from collections import defaultdict
from itertools import combinations

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

from db import get_db

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "Datasets", "trimmed")
FAQ_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "Datasets", "bitext_faq.csv")
EMBED_BATCH = 50  # smaller batches to avoid cloud WebSocket timeouts


def read_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def safe_float(val):
    try:
        return float(val) if val else None
    except ValueError:
        return None


def safe_int(val):
    try:
        return int(float(val)) if val else None
    except ValueError:
        return None


def make_cat_id(name):
    return name.lower().replace(" ", "_").replace("&", "and")


def derive_also_bought_edges(orders):
    cust_products = defaultdict(set)
    for row in orders:
        cust_products[row["customer_id"]].add(row["product_id"])
    co_purchase = {}
    for _cid, products in cust_products.items():
        if len(products) < 2:
            continue
        for a, b in combinations(sorted(products), 2):
            for pair in [(a, b), (b, a)]:
                co_purchase[pair] = co_purchase.get(pair, 0) + 1
    return co_purchase


async def run_batch(queries, max_retries=3):
    """Run a batch of queries with a fresh connection and retry on failure."""
    for attempt in range(max_retries):
        try:
            async with get_db() as db:
                for q, params in queries:
                    try:
                        if params:
                            await db.query(q, params)
                        else:
                            await db.query(q)
                    except Exception as e:
                        err = str(e).lower()
                        if "already exists" in err or "duplicate" in err:
                            pass
                        elif "keepalive" in err or "ping timeout" in err or "1011" in err:
                            raise  # reconnect
                        else:
                            print(f"  Error: {e}")
                return  # success
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 5 * (attempt + 1)
                print(f"  Connection lost, retrying in {wait}s (attempt {attempt + 2}/{max_retries})...")
                await asyncio.sleep(wait)
            else:
                print(f"  Failed after {max_retries} attempts: {e}")
                raise


async def seed_resume():
    print("Loading CSV data...")
    reviews_raw = read_csv("reviews.csv")
    orders_raw = read_csv("orders.csv")
    products_raw = read_csv("products.csv")
    print(f"  reviews: {len(reviews_raw)}, orders: {len(orders_raw)}, products: {len(products_raw)}")

    # Check what's already seeded
    async with get_db() as db:
        result = await db.query("SELECT count() FROM review GROUP ALL")
        existing_reviews = result[0]["count"] if result else 0
        print(f"  Existing reviews in DB: {existing_reviews}")

    # ── 5. Reviews (resume) ─────────────────────────────────
    start_from = existing_reviews  # skip already-seeded reviews
    remaining = len(reviews_raw) - start_from
    print(f"\n[5/7] Seeding reviews (resuming from {start_from}, {remaining} remaining)...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    for i in range(start_from, len(reviews_raw), EMBED_BATCH):
        batch = reviews_raw[i: i + EMBED_BATCH]

        # Embed
        texts = [row.get("review_comment_message", "") or "" for row in batch]
        non_empty_indices = [j for j, t in enumerate(texts) if t.strip()]
        non_empty_texts = [texts[j] for j in non_empty_indices]

        vecs = {}
        if non_empty_texts:
            embedded = await embeddings.aembed_documents(non_empty_texts)
            for idx, vec in zip(non_empty_indices, embedded):
                vecs[idx] = vec

        # Build queries for this batch
        queries = []
        for j, row in enumerate(batch):
            rid = row["review_id"]
            oid = row["order_id"]
            vec = vecs.get(j)
            queries.append((
                f"CREATE review:`{rid}` SET score = $score, comment = $comment, "
                "sentiment = $sentiment, embedding = $embedding",
                {
                    "score": safe_int(row.get("review_score", "")) or 0,
                    "comment": row.get("review_comment_message") or None,
                    "sentiment": row.get("sentiment") or None,
                    "embedding": vec,
                },
            ))
            queries.append((f"RELATE order:`{oid}`->has_review->review:`{rid}`", None))

        await run_batch(queries)
        print(f"  {min(i + EMBED_BATCH, len(reviews_raw))}/{len(reviews_raw)}")

    # ── 6. Also_bought edges ────────────────────────────────
    print("\n[6/7] Creating also_bought edges...")
    also_bought_edges = derive_also_bought_edges(orders_raw)
    print(f"  {len(also_bought_edges)} edges to create")

    also_items = list(also_bought_edges.items())
    for i in range(0, len(also_items), EMBED_BATCH):
        batch = also_items[i: i + EMBED_BATCH]
        queries = []
        for (pid_a, pid_b), weight in batch:
            queries.append((
                f"RELATE product:`{pid_a}`->also_bought->product:`{pid_b}` SET weight = $w",
                {"w": weight},
            ))
        await run_batch(queries)
        print(f"  {min(i + EMBED_BATCH, len(also_items))}/{len(also_items)}")

    # ── 7. Documents (product + FAQ) ────────────────────────
    print("\n[7/7] Seeding documents with embeddings...")

    # Check existing
    async with get_db() as db:
        result = await db.query("SELECT count() FROM documents GROUP ALL")
        existing_docs = result[0]["count"] if result else 0
        print(f"  Existing documents in DB: {existing_docs}")

    # Product documents
    print("  Product documents...")
    for i in range(0, len(products_raw), EMBED_BATCH):
        batch = products_raw[i: i + EMBED_BATCH]
        texts = [f"{row['product_name']}: {row.get('description', '') or ''}" for row in batch]
        vecs = await embeddings.aembed_documents(texts)

        queries = []
        for row, vec in zip(batch, vecs):
            pid = row["product_id"]
            doc_id = f"prod_{pid[:16]}"
            content = f"{row['product_name']}: {row.get('description', '') or ''}"
            queries.append((
                f"CREATE documents:`{doc_id}` SET "
                "doc_type = 'product', title = $title, content = $content, "
                "source_id = $source_id, metadata = $meta, embedding = $embedding",
                {
                    "title": row["product_name"],
                    "content": content,
                    "source_id": f"product:`{pid}`",
                    "meta": {
                        "product_id": pid,
                        "price": safe_float(row.get("price", "")),
                        "vertical": row.get("vertical") or None,
                        "subcategory": row.get("subcategory") or None,
                    },
                    "embedding": vec,
                },
            ))
        await run_batch(queries)
        print(f"  {min(i + EMBED_BATCH, len(products_raw))}/{len(products_raw)}")

    # FAQ documents
    if os.path.exists(FAQ_PATH):
        print("  FAQ documents...")
        with open(FAQ_PATH, encoding="utf-8") as f:
            faqs = list(csv.DictReader(f))

        seen_intents = set()
        unique_faqs = []
        for faq in faqs:
            intent = faq.get("intent", "")
            if intent not in seen_intents:
                seen_intents.add(intent)
                unique_faqs.append(faq)

        print(f"  {len(unique_faqs)} unique FAQ intents")

        for i in range(0, len(unique_faqs), EMBED_BATCH):
            batch = unique_faqs[i: i + EMBED_BATCH]
            texts = [f"{f.get('instruction', '')} {f.get('response', '')}" for f in batch]
            vecs = await embeddings.aembed_documents(texts)

            queries = []
            for j, (faq, vec) in enumerate(zip(batch, vecs)):
                idx = i + j
                queries.append((
                    f"CREATE documents:`faq_{idx}` SET "
                    "doc_type = 'faq', title = $title, content = $content, "
                    "metadata = $meta, embedding = $embedding",
                    {
                        "title": faq.get("instruction", ""),
                        "content": faq.get("response", ""),
                        "meta": {
                            "category": faq.get("category"),
                            "intent": faq.get("intent"),
                        },
                        "embedding": vec,
                    },
                ))
            await run_batch(queries)
            print(f"  {min(i + EMBED_BATCH, len(unique_faqs))}/{len(unique_faqs)}")

    # ── Summary ─────────────────────────────────────────────
    print("\n" + "=" * 50)
    async with get_db() as db:
        for table in ["customer", "product", "order", "review", "category", "documents"]:
            result = await db.query(f"SELECT count() FROM {table} GROUP ALL")
            count = result[0]["count"] if result else 0
            print(f"  {table}: {count}")
        for edge in ["placed", "contains", "has_review", "also_bought", "belongs_to", "child_of"]:
            result = await db.query(f"SELECT count() FROM {edge} GROUP ALL")
            count = result[0]["count"] if result else 0
            print(f"  {edge}: {count}")
    print("=" * 50)
    print("SEED RESUME COMPLETE!")


if __name__ == "__main__":
    asyncio.run(seed_resume())
