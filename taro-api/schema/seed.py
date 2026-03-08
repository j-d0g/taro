"""Seed script: populates SurrealDB with scraped lookfantastic dataset + enrichment.

Data sources:
- Products, customers, orders, reviews: Datasets/trimmed/ CSVs (1,890 scraped products)
- Goals, ingredients, user personas: schema/mock_data.py (curated enrichment)
- FAQs: Datasets/bitext_faq.csv (26K Q&A pairs, deduplicated by intent)

Usage: python schema/seed.py
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

# Import enrichment data (goals, ingredients, user personas)
sys.path.insert(0, os.path.dirname(__file__))
from mock_data import (
    GOALS,
    INGREDIENTS,
)

# ── CSV paths ──────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "Datasets", "trimmed")
FAQ_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "Datasets", "bitext_faq.csv")
EMBED_BATCH = 100


def safe_float(val: str) -> float | None:
    """Convert string to float, return None on failure."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def load_csv(filename: str) -> list[dict]:
    """Load a CSV file from the trimmed data directory."""
    path = os.path.join(DATA_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def make_cat_id(name: str) -> str:
    """Sanitise a category name into a SurrealDB record ID slug."""
    return name.lower().replace(" ", "_").replace("&", "and")


async def seed():
    # ── Load CSV data ──────────────────────────────────────────
    print("Loading CSV data...")
    products_raw = load_csv("products.csv")
    customers_raw = load_csv("customers.csv")
    orders_raw = load_csv("orders.csv")
    reviews_raw = load_csv("reviews.csv")

    print(f"  products:    {len(products_raw)}")
    print(f"  customers:   {len(customers_raw)}")
    print(f"  orders:      {len(orders_raw)}")
    print(f"  reviews:     {len(reviews_raw)}")
    print(f"  goals:       {len(GOALS)} (enrichment)")
    print(f"  ingredients: {len(INGREDIENTS)} (enrichment)")

    print("\nConnecting to SurrealDB...")
    async with get_db() as db:
        # ── Apply schema ─────────────────────────────────────
        print("Applying schema...")
        schema_path = os.path.join(os.path.dirname(__file__), "schema.surql")
        with open(schema_path) as f:
            schema = f.read()
        for statement in schema.split(";"):
            stmt = statement.strip()
            if stmt and not stmt.startswith("--"):
                try:
                    await db.query(stmt)
                except Exception as e:
                    print(f"  Schema warning: {e}")

        # ── 1. Categories (derived from products) ─────────────
        print("\n[1/9] Seeding categories...")
        verticals = set()
        subcats = set()
        for p in products_raw:
            v = p.get("vertical", "")
            s = p.get("subcategory", "")
            if v:
                verticals.add(v)
            if s and v:
                subcats.add((v, s))

        for v in sorted(verticals):
            vid = make_cat_id(v)
            await db.query(
                f"CREATE category:`{vid}` SET name = $name, level = 'vertical'",
                {"name": v},
            )

        for v, s in sorted(subcats):
            sid = make_cat_id(f"{v}__{s}")
            vid = make_cat_id(v)
            await db.query(
                f"CREATE category:`{sid}` SET name = $name, level = 'subcategory'",
                {"name": s},
            )
            await db.query(f"RELATE category:`{sid}`->child_of->category:`{vid}`")

        print(f"  {len(verticals)} verticals, {len(subcats)} subcategories")

        # ── 2. Goals + Ingredients (enrichment) ────────────────
        print("[2/9] Seeding goals...")
        for g in GOALS:
            await db.query(
                f"CREATE goal:`{g['id']}` SET name = $name, description = $desc, vertical = $vertical",
                {"name": g["name"], "desc": g.get("description"), "vertical": g.get("vertical")},
            )
        print(f"  {len(GOALS)} goals")

        print("[3/9] Seeding ingredients...")
        for ing in INGREDIENTS:
            await db.query(
                f"CREATE ingredient:`{ing['id']}` SET name = $name, role = $role, "
                "category = $cat, description = $desc, common_in = $common_in",
                {
                    "name": ing["name"],
                    "role": ing.get("role"),
                    "cat": ing.get("category"),
                    "desc": ing.get("description"),
                    "common_in": ing.get("common_in", []),
                },
            )
        print(f"  {len(INGREDIENTS)} ingredients")

        # ── 3. Customers ──────────────────────────────────────
        print("[4/9] Seeding customers...")
        for i in range(0, len(customers_raw), EMBED_BATCH):
            batch = customers_raw[i : i + EMBED_BATCH]
            for row in batch:
                cid = row["customer_id"]
                await db.query(
                    f"CREATE customer:`{cid}` SET "
                    "name = $name, city = $city, state = $state",
                    {
                        "name": row.get("customer_name") or None,
                        "city": row.get("customer_city") or None,
                        "state": row.get("customer_state") or None,
                    },
                )
            print(f"  {min(i + EMBED_BATCH, len(customers_raw))}/{len(customers_raw)}")

        # ── 4. Products + belongs_to ──────────────────────────
        print("[5/9] Seeding products...")
        product_ids = set()
        for i in range(0, len(products_raw), EMBED_BATCH):
            batch = products_raw[i : i + EMBED_BATCH]
            for row in batch:
                pid = row["product_id"]
                product_ids.add(pid)
                await db.query(
                    f"CREATE product:`{pid}` SET "
                    "name = $name, vertical = $vertical, subcategory = $subcat, "
                    "price = $price, avg_rating = $rating, description = $desc, "
                    "weight_g = $weight, image_url = $image_url, product_url = $product_url",
                    {
                        "name": row["product_name"],
                        "vertical": row.get("vertical") or None,
                        "subcat": row.get("subcategory") or None,
                        "price": safe_float(row.get("price", "")),
                        "rating": safe_float(row.get("avg_rating", "")),
                        "desc": row.get("description") or None,
                        "weight": safe_float(row.get("weight_g", "")),
                        "image_url": row.get("image_url") or None,
                        "product_url": row.get("product_url") or None,
                    },
                )
                # product -belongs_to-> subcategory
                subcat = row.get("subcategory", "")
                vertical = row.get("vertical", "")
                if subcat and vertical:
                    sid = make_cat_id(f"{vertical}__{subcat}")
                    await db.query(f"RELATE product:`{pid}`->belongs_to->category:`{sid}`")
            print(f"  {min(i + EMBED_BATCH, len(products_raw))}/{len(products_raw)}")

        # ── 5. Orders + placed + contains ─────────────────────
        print("[6/9] Seeding orders...")
        customer_products: dict[str, set[str]] = defaultdict(set)
        for i in range(0, len(orders_raw), EMBED_BATCH):
            batch = orders_raw[i : i + EMBED_BATCH]
            for row in batch:
                oid = row["order_id"]
                cid = row["customer_id"]
                pid = row["product_id"]

                # Skip orders referencing missing products
                if pid not in product_ids:
                    continue

                await db.query(
                    f"CREATE order:`{oid}` SET price = $price, status = 'delivered', currency = 'GBP'",
                    {"price": safe_float(row.get("price", ""))},
                )
                # customer -placed-> order
                await db.query(f"RELATE customer:`{cid}`->placed->order:`{oid}`")
                # order -contains-> product
                await db.query(f"RELATE order:`{oid}`->contains->product:`{pid}`")
                # Track for also_bought
                customer_products[cid].add(pid)
            print(f"  {min(i + EMBED_BATCH, len(orders_raw))}/{len(orders_raw)}")

        # ── 6. Reviews + has_review ───────────────────────────
        print("[7/9] Seeding reviews...")
        order_ids_in_db = set(row["order_id"] for row in orders_raw)
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        for i in range(0, len(reviews_raw), EMBED_BATCH):
            batch = reviews_raw[i : i + EMBED_BATCH]
            texts = [r.get("review_comment_message", "") or "" for r in batch]
            non_empty = [(j, t) for j, t in enumerate(texts) if t.strip()]

            vecs = {}
            if non_empty:
                embedded = await embeddings.aembed_documents([t for _, t in non_empty])
                for (j, _), vec in zip(non_empty, embedded):
                    vecs[j] = vec

            for j, r in enumerate(batch):
                rid = r["review_id"]
                oid = r["order_id"]
                if oid not in order_ids_in_db:
                    continue
                vec = vecs.get(j)
                score = int(r.get("review_score", 0) or 0)
                await db.query(
                    f"CREATE review:`{rid}` SET "
                    "score = $score, comment = $comment, sentiment = $sentiment, "
                    "embedding = $embedding",
                    {
                        "score": score,
                        "comment": r.get("review_comment_message") or None,
                        "sentiment": r.get("sentiment") or None,
                        "embedding": vec,
                    },
                )
                await db.query(f"RELATE order:`{oid}`->has_review->review:`{rid}`")

            print(f"  {min(i + EMBED_BATCH, len(reviews_raw))}/{len(reviews_raw)}")

        # ── 7. Also-bought edges (derived from co-purchase) ───
        print("[8/9] Seeding also_bought edges...")
        also_bought: dict[tuple[str, str], int] = {}
        for _cid, prods in customer_products.items():
            if len(prods) < 2:
                continue
            for a, b in combinations(sorted(prods), 2):
                for pair in [(a, b), (b, a)]:
                    also_bought[pair] = also_bought.get(pair, 0) + 1

        for (pid_a, pid_b), weight in also_bought.items():
            await db.query(
                f"RELATE product:`{pid_a}`->also_bought->product:`{pid_b}` SET weight = $w",
                {"w": weight},
            )
        print(f"  {len(also_bought)} also_bought edges")

        # ── 8. Product documents with embeddings ──────────────
        print("[9/9] Seeding documents (with embeddings)...")
        print("  Product documents...")
        for i in range(0, len(products_raw), EMBED_BATCH):
            batch = products_raw[i : i + EMBED_BATCH]
            texts = []
            for p in batch:
                desc = p.get("description", "") or ""
                text = f"{p['product_name']}: {desc}"
                texts.append(text)

            vecs = await embeddings.aembed_documents(texts)

            for p, vec in zip(batch, vecs):
                pid = p["product_id"]
                doc_id = f"prod_{pid}"
                desc = p.get("description", "") or ""
                content = f"{p['product_name']}: {desc}"
                await db.query(
                    f"CREATE documents:`{doc_id}` SET "
                    "doc_type = 'product', title = $title, content = $content, "
                    f"source_id = product:`{pid}`, metadata = $meta, embedding = $embedding",
                    {
                        "title": p["product_name"],
                        "content": content,
                        "meta": {
                            "product_id": pid,
                            "price": safe_float(p.get("price", "")),
                            "vertical": p.get("vertical"),
                            "subcategory": p.get("subcategory"),
                        },
                        "embedding": vec,
                    },
                )
            print(f"  {min(i + EMBED_BATCH, len(products_raw))}/{len(products_raw)}")

        # FAQ documents
        print("  FAQ documents...")
        if os.path.exists(FAQ_PATH):
            with open(FAQ_PATH, encoding="utf-8") as f:
                faqs = list(csv.DictReader(f))

            seen_intents = set()
            unique_faqs = []
            for faq in faqs:
                intent = faq.get("intent", "")
                if intent not in seen_intents:
                    seen_intents.add(intent)
                    unique_faqs.append(faq)

            print(f"  {len(unique_faqs)} unique FAQ intents (from {len(faqs)} rows)")

            for i in range(0, len(unique_faqs), EMBED_BATCH):
                batch = unique_faqs[i : i + EMBED_BATCH]
                texts = [f"{f.get('instruction', '')} {f.get('response', '')}" for f in batch]
                vecs = await embeddings.aembed_documents(texts)

                for j, (faq, vec) in enumerate(zip(batch, vecs)):
                    idx = i + j
                    await db.query(
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
                    )
                print(f"  {min(i + EMBED_BATCH, len(unique_faqs))}/{len(unique_faqs)}")
        else:
            print(f"  FAQ file not found at {FAQ_PATH}, skipping")

        # ── Summary ──────────────────────────────────────────
        print("\n" + "=" * 60)
        print("SEED COMPLETE")
        print("=" * 60)
        print(f"  Nodes:")
        print(f"    {len(customers_raw):>6} customers")
        print(f"    {len(products_raw):>6} products (scraped lookfantastic)")
        print(f"    {len(verticals) + len(subcats):>6} categories ({len(verticals)} verticals + {len(subcats)} subcategories)")
        print(f"    {len(orders_raw):>6} orders")
        print(f"    {len(reviews_raw):>6} reviews (with embeddings)")
        print(f"    {len(GOALS):>6} goals (enrichment)")
        print(f"    {len(INGREDIENTS):>6} ingredients (enrichment)")
        print(f"  Edges:")
        print(f"    placed:       customer -> order")
        print(f"    contains:     order -> product")
        print(f"    has_review:   order -> review")
        print(f"    belongs_to:   product -> category")
        print(f"    child_of:     subcategory -> vertical")
        print(f"    also_bought:  {len(also_bought):>4} product <-> product (derived)")
        print(f"  Documents:")
        print(f"    {len(products_raw):>6} product docs (vector + BM25)")
        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(seed())
