"""Seed script: populates SurrealDB from trimmed CSV/JSON datasets.

Loads customers, products, orders, payments, reviews into SurrealDB with:
- Native record links (not string foreign keys)
- Vector embeddings on product documents AND review comments
- Derived graph edges: bought (customer→product), also_bought (product→product)
- Category hierarchy: subcategory -child_of-> vertical

Usage: python schema/seed.py
"""

import asyncio
import csv
import os
import sys
from collections import defaultdict
from itertools import combinations

# Add src to path for db module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

from db import get_db

# ── Paths ────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "Datasets", "trimmed")
FAQ_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "Datasets", "bitext_faq.csv")

EMBED_BATCH = 100  # OpenAI batch size for embeddings


def read_csv(filename: str) -> list[dict]:
    path = os.path.join(DATA_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def safe_float(val: str) -> float | None:
    try:
        return float(val) if val else None
    except ValueError:
        return None


def safe_int(val: str) -> int | None:
    try:
        return int(float(val)) if val else None
    except ValueError:
        return None


def make_cat_id(name: str) -> str:
    """Sanitise a category name into a SurrealDB record ID slug."""
    return name.lower().replace(" ", "_").replace("&", "and")


# ── Derived graph edges ──────────────────────────────────────

def derive_bought_edges(orders: list[dict]) -> dict[tuple[str, str], dict]:
    """Aggregate orders into customer→product edges with total_spent + order_count."""
    agg: dict[tuple[str, str], dict] = {}
    for row in orders:
        key = (row["customer_id"], row["product_id"])
        if key not in agg:
            agg[key] = {"total_spent": 0.0, "order_count": 0}
        price = safe_float(row.get("price", "")) or 0.0
        agg[key]["total_spent"] = round(agg[key]["total_spent"] + price, 2)
        agg[key]["order_count"] += 1
    return agg


def derive_also_bought_edges(orders: list[dict]) -> dict[tuple[str, str], dict]:
    """Find products co-purchased by the same customer. Returns product→product edges."""
    # Build customer → set of products
    cust_products: dict[str, set[str]] = defaultdict(set)
    for row in orders:
        cust_products[row["customer_id"]].add(row["product_id"])

    # For each customer with >1 product, create co-purchase pairs
    co_purchase: dict[tuple[str, str], dict] = {}
    for cid, products in cust_products.items():
        if len(products) < 2:
            continue
        for a, b in combinations(sorted(products), 2):
            # Bidirectional — create both directions
            for pair in [(a, b), (b, a)]:
                if pair not in co_purchase:
                    co_purchase[pair] = {"weight": 0, "customers": []}
                co_purchase[pair]["weight"] += 1
                if len(co_purchase[pair]["customers"]) < 5:  # cap sample
                    co_purchase[pair]["customers"].append(cid)
    return co_purchase


# ── Main seed ────────────────────────────────────────────────

async def seed():
    print("Loading CSV data...")
    customers_raw = read_csv("customers.csv")
    products_raw = read_csv("products.csv")
    orders_raw = read_csv("orders.csv")
    payments_raw = read_csv("payments.csv")
    reviews_raw = read_csv("reviews.csv")

    print(f"  customers: {len(customers_raw)}")
    print(f"  products:  {len(products_raw)}")
    print(f"  orders:    {len(orders_raw)}")
    print(f"  payments:  {len(payments_raw)}")
    print(f"  reviews:   {len(reviews_raw)}")

    # Pre-compute derived edges
    print("\nDeriving graph edges...")
    bought_edges = derive_bought_edges(orders_raw)
    also_bought_edges = derive_also_bought_edges(orders_raw)
    print(f"  bought edges (customer→product): {len(bought_edges)}")
    print(f"  also_bought edges (product→product): {len(also_bought_edges)}")

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

        # ── 1. Categories (vertical + subcategory hierarchy) ─
        print("\n[1/9] Seeding categories...")
        verticals = set()
        subcats = set()
        for row in products_raw:
            v = row.get("vertical", "")
            s = row.get("subcategory", "")
            if v:
                verticals.add(v)
            if s and v:
                subcats.add((v, s))

        # Create vertical-level categories
        for v in sorted(verticals):
            vid = make_cat_id(v)
            await db.query(
                f"CREATE category:`{vid}` SET name = $name, level = 'vertical'",
                {"name": v},
            )

        # Create subcategory-level categories + child_of edges
        for v, s in sorted(subcats):
            sid = make_cat_id(f"{v}__{s}")
            vid = make_cat_id(v)
            await db.query(
                f"CREATE category:`{sid}` SET name = $name, level = 'subcategory'",
                {"name": s},
            )
            # subcategory -child_of-> vertical
            await db.query(f"RELATE category:`{sid}`->child_of->category:`{vid}`")

        print(f"  {len(verticals)} verticals, {len(subcats)} subcategories")

        # ── 2. Customers ─────────────────────────────────────
        print("[2/9] Seeding customers...")
        for i in range(0, len(customers_raw), EMBED_BATCH):
            batch = customers_raw[i : i + EMBED_BATCH]
            for row in batch:
                cid = row["customer_id"]
                await db.query(
                    f"CREATE customer:`{cid}` SET name = $name, city = $city, state = $state",
                    {
                        "name": row["customer_name"],
                        "city": row["customer_city"] or None,
                        "state": row["customer_state"] or None,
                    },
                )
            print(f"  {min(i + EMBED_BATCH, len(customers_raw))}/{len(customers_raw)}")

        # ── 3. Products + belongs_to edges ───────────────────
        print("[3/9] Seeding products...")
        for i in range(0, len(products_raw), EMBED_BATCH):
            batch = products_raw[i : i + EMBED_BATCH]
            for row in batch:
                pid = row["product_id"]
                await db.query(
                    f"CREATE product:`{pid}` SET "
                    "name = $name, vertical = $vertical, subcategory = $subcat, "
                    "price = $price, avg_rating = $rating, description = $desc, "
                    "weight_g = $weight, image_url = $image_url",
                    {
                        "name": row["product_name"],
                        "vertical": row.get("vertical") or None,
                        "subcat": row.get("subcategory") or None,
                        "price": safe_float(row.get("price", "")),
                        "rating": safe_float(row.get("avg_rating", "")),
                        "desc": row.get("description") or None,
                        "weight": safe_float(row.get("weight_g", "")),
                        "image_url": row.get("image_url") or None,
                    },
                )
                # product -belongs_to-> subcategory
                subcat = row.get("subcategory", "")
                vertical = row.get("vertical", "")
                if subcat and vertical:
                    sid = make_cat_id(f"{vertical}__{subcat}")
                    await db.query(f"RELATE product:`{pid}`->belongs_to->category:`{sid}`")

            print(f"  {min(i + EMBED_BATCH, len(products_raw))}/{len(products_raw)}")

        # ── 4. Orders + placed + contains edges ──────────────
        print("[4/9] Seeding orders...")
        seen_orders = set()
        for i in range(0, len(orders_raw), EMBED_BATCH):
            batch = orders_raw[i : i + EMBED_BATCH]
            for row in batch:
                oid = row["order_id"]
                cid = row["customer_id"]
                pid = row["product_id"]
                price = safe_float(row.get("price", ""))

                if oid not in seen_orders:
                    await db.query(
                        f"CREATE order:`{oid}` SET price = $price",
                        {"price": price},
                    )
                    # customer -placed-> order (once per order)
                    await db.query(f"RELATE customer:`{cid}`->placed->order:`{oid}`")
                    seen_orders.add(oid)

                # order -contains-> product (once per line item)
                await db.query(f"RELATE order:`{oid}`->contains->product:`{pid}`")

            print(f"  {min(i + EMBED_BATCH, len(orders_raw))}/{len(orders_raw)}")

        # ── 5. Payments + paid_with edges ────────────────────
        print("[5/9] Seeding payments...")
        for i in range(0, len(payments_raw), EMBED_BATCH):
            batch = payments_raw[i : i + EMBED_BATCH]
            for row in batch:
                oid = row["order_id"]
                pay_id = f"{oid}_{row['payment_type']}"
                await db.query(
                    f"CREATE payment:`{pay_id}` SET "
                    "payment_type = $ptype, installments = $inst, value = $val",
                    {
                        "ptype": row["payment_type"],
                        "inst": safe_int(row.get("payment_installments", "")),
                        "val": safe_float(row.get("payment_value", "")),
                    },
                )
                # order -paid_with-> payment
                await db.query(f"RELATE order:`{oid}`->paid_with->payment:`{pay_id}`")

            print(f"  {min(i + EMBED_BATCH, len(payments_raw))}/{len(payments_raw)}")

        # ── 6. Reviews + has_review edges + embeddings ───────
        print("[6/9] Seeding reviews (with embeddings)...")
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        for i in range(0, len(reviews_raw), EMBED_BATCH):
            batch = reviews_raw[i : i + EMBED_BATCH]

            # Batch-embed review comments
            texts = [row.get("review_comment_message", "") or "" for row in batch]
            # Only embed non-empty comments
            non_empty_indices = [j for j, t in enumerate(texts) if t.strip()]
            non_empty_texts = [texts[j] for j in non_empty_indices]

            vecs = {}
            if non_empty_texts:
                embedded = await embeddings.aembed_documents(non_empty_texts)
                for idx, vec in zip(non_empty_indices, embedded):
                    vecs[idx] = vec

            for j, row in enumerate(batch):
                rid = row["review_id"]
                oid = row["order_id"]
                vec = vecs.get(j)
                await db.query(
                    f"CREATE review:`{rid}` SET "
                    "score = $score, comment = $comment, sentiment = $sentiment, "
                    "embedding = $embedding",
                    {
                        "score": safe_int(row.get("review_score", "")) or 0,
                        "comment": row.get("review_comment_message") or None,
                        "sentiment": row.get("sentiment") or None,
                        "embedding": vec,
                    },
                )
                # order -has_review-> review
                await db.query(f"RELATE order:`{oid}`->has_review->review:`{rid}`")

            print(f"  {min(i + EMBED_BATCH, len(reviews_raw))}/{len(reviews_raw)}")

        # ── 7. Derived: bought edges ─────────────────────────
        print("[7/9] Creating bought edges (customer→product)...")
        bought_items = list(bought_edges.items())
        for i in range(0, len(bought_items), EMBED_BATCH):
            batch = bought_items[i : i + EMBED_BATCH]
            for (cid, pid), stats in batch:
                await db.query(
                    f"RELATE customer:`{cid}`->bought->product:`{pid}` "
                    "SET total_spent = $spent, order_count = $cnt",
                    {"spent": stats["total_spent"], "cnt": stats["order_count"]},
                )
            print(f"  {min(i + EMBED_BATCH, len(bought_items))}/{len(bought_items)}")

        # ── 8. Derived: also_bought edges ────────────────────
        print("[8/9] Creating also_bought edges (product→product)...")
        also_items = list(also_bought_edges.items())
        for i in range(0, len(also_items), EMBED_BATCH):
            batch = also_items[i : i + EMBED_BATCH]
            for (pid_a, pid_b), stats in batch:
                await db.query(
                    f"RELATE product:`{pid_a}`->also_bought->product:`{pid_b}` "
                    "SET weight = $w, customers = $custs",
                    {"w": stats["weight"], "custs": stats["customers"]},
                )
            print(f"  {min(i + EMBED_BATCH, len(also_items))}/{len(also_items)}")

        # ── 9. Product + FAQ documents (vector + BM25) ───────
        print("[9/9] Seeding documents with embeddings...")

        # Product documents
        print("  Product documents...")
        for i in range(0, len(products_raw), EMBED_BATCH):
            batch = products_raw[i : i + EMBED_BATCH]
            texts = []
            for row in batch:
                desc = row.get("description", "") or ""
                text = f"{row['product_name']}: {desc}"
                texts.append(text)

            vecs = await embeddings.aembed_documents(texts)

            for row, vec in zip(batch, vecs):
                pid = row["product_id"]
                doc_id = f"prod_{pid[:16]}"
                desc = row.get("description", "") or ""
                content = f"{row['product_name']}: {desc}"
                await db.query(
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
                )
            print(f"  {min(i + EMBED_BATCH, len(products_raw))}/{len(products_raw)}")

        # FAQ documents
        if os.path.exists(FAQ_PATH):
            print("  FAQ documents...")
            with open(FAQ_PATH, encoding="utf-8") as f:
                faqs = list(csv.DictReader(f))

            # Deduplicate by intent
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

        # ── Summary ──────────────────────────────────────────
        print("\n" + "=" * 50)
        print("SEED COMPLETE")
        print("=" * 50)
        print(f"  Nodes:")
        print(f"    {len(customers_raw):>6} customers")
        print(f"    {len(products_raw):>6} products")
        print(f"    {len(verticals) + len(subcats):>6} categories ({len(verticals)} verticals + {len(subcats)} subcategories)")
        print(f"    {len(set(r['order_id'] for r in orders_raw)):>6} orders")
        print(f"    {len(payments_raw):>6} payments")
        print(f"    {len(reviews_raw):>6} reviews (with embeddings)")
        print(f"  Edges:")
        print(f"    placed:       customer → order")
        print(f"    contains:     order → product")
        print(f"    paid_with:    order → payment")
        print(f"    has_review:   order → review")
        print(f"    belongs_to:   product → category")
        print(f"    child_of:     subcategory → vertical")
        print(f"    bought:       {len(bought_edges):>6} customer → product (derived)")
        print(f"    also_bought:  {len(also_bought_edges):>6} product → product (derived)")
        print(f"  Documents:")
        print(f"    {len(products_raw):>6} product docs (vector + BM25)")
        faq_count = len(unique_faqs) if os.path.exists(FAQ_PATH) else 0
        print(f"    {faq_count:>6} FAQ docs (vector + BM25)")
        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(seed())
