"""Seed script: populates SurrealDB with scraped lookfantastic dataset + enrichment.

Data sources:
- Products, customers, orders, reviews: Datasets/trimmed/ CSVs (1,890 scraped products)
- Goals, ingredients: inline (curated beauty enrichment)
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

# ── Beauty goals & ingredients (LookFantastic catalog) ─────────────

GOALS = [
    {"id": "clear_skin", "name": "Clear Skin", "description": "Achieve a clear, blemish-free complexion through targeted skincare", "vertical": "Skincare"},
    {"id": "anti_aging", "name": "Anti-Aging", "description": "Reduce fine lines and wrinkles, maintain youthful skin", "vertical": "Skincare"},
    {"id": "hydration", "name": "Hydration", "description": "Deep moisture for skin, hair, and body", "vertical": "Skincare"},
    {"id": "hair_growth", "name": "Hair Growth", "description": "Support healthy hair growth and reduce thinning", "vertical": "Haircare"},
    {"id": "brightening", "name": "Brightening", "description": "Even out skin tone and fade dark spots", "vertical": "Skincare"},
    {"id": "sun_protection", "name": "Sun Protection", "description": "Shield skin from UV damage and prevent premature aging", "vertical": "Skincare"},
]

INGREDIENTS = [
    {"id": "hyaluronic_acid", "name": "Hyaluronic Acid", "role": "hydration", "category": "skincare", "description": "Moisture-binding molecule that holds 1000x its weight in water", "common_in": ["serums", "moisturisers", "masks"]},
    {"id": "retinol", "name": "Retinol", "role": "anti-aging", "category": "skincare", "description": "Vitamin A derivative that boosts cell turnover and collagen production", "common_in": ["serums", "night creams"]},
    {"id": "niacinamide", "name": "Niacinamide", "role": "pore control", "category": "skincare", "description": "Vitamin B3 that minimises pores and evens skin tone", "common_in": ["serums", "moisturisers", "toners"]},
    {"id": "salicylic_acid", "name": "Salicylic Acid", "role": "exfoliation", "category": "skincare", "description": "BHA that penetrates pores to clear breakouts", "common_in": ["cleansers", "toners", "spot treatments"]},
    {"id": "vitamin_c", "name": "Vitamin C", "role": "brightening", "category": "skincare", "description": "Antioxidant that brightens skin and fades dark spots", "common_in": ["serums", "moisturisers"]},
    {"id": "glycolic_acid", "name": "Glycolic Acid", "role": "exfoliation", "category": "skincare", "description": "AHA that resurfaces skin for a smoother texture", "common_in": ["toners", "peeling solutions", "masks"]},
    {"id": "ceramides", "name": "Ceramides", "role": "barrier repair", "category": "skincare", "description": "Lipids that strengthen the skin barrier and lock in moisture", "common_in": ["moisturisers", "cleansers"]},
    {"id": "squalane", "name": "Squalane", "role": "hydration", "category": "skincare", "description": "Lightweight oil that mimics skin's natural sebum", "common_in": ["oils", "moisturisers"]},
    {"id": "spf", "name": "SPF Filters", "role": "sun protection", "category": "skincare", "description": "UV filters that protect skin from sun damage", "common_in": ["sunscreens", "moisturisers", "primers"]},
    {"id": "peptides", "name": "Peptides", "role": "anti-aging", "category": "skincare", "description": "Short chains of amino acids that signal collagen production", "common_in": ["serums", "eye creams"]},
    {"id": "caffeine", "name": "Caffeine", "role": "depuffing", "category": "skincare", "description": "Constricts blood vessels to reduce puffiness and dark circles", "common_in": ["eye creams", "serums"]},
    {"id": "collagen", "name": "Collagen", "role": "firming", "category": "skincare", "description": "Structural protein supporting skin elasticity and firmness", "common_in": ["creams", "masks", "serums"]},
    {"id": "biotin", "name": "Biotin", "role": "hair and nail growth", "category": "haircare", "description": "B-vitamin that supports keratin production for healthy hair and nails", "common_in": ["hair treatments", "supplements"]},
    {"id": "argan_oil", "name": "Argan Oil", "role": "nourishment", "category": "haircare", "description": "Rich in vitamin E and fatty acids for hair shine and softness", "common_in": ["hair oils", "conditioners", "masks"]},
    {"id": "lavender", "name": "Lavender Oil", "role": "calming", "category": "body", "description": "Essential oil with calming and soothing properties", "common_in": ["bath products", "body lotions", "candles"]},
]

# ── CSV paths ──────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
FAQ_PATH = os.path.join(os.path.dirname(__file__), "data", "bitext_faq.csv")
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

        # ── 3b. Charlotte Gong (rich demo customer) ──────────
        print("  + Charlotte Gong (demo customer with rich profile)")
        await db.query(
            "CREATE customer:`charlotte_gong` SET "
            "name = $name, city = $city, state = $state, "
            "skin_type = $skin_type, hair_type = $hair_type, "
            "concerns = $concerns, preferences = $preferences, "
            "allergies = $allergies, age = $age, bio = $bio, "
            "profile_type = $profile_type, experience_level = $experience_level, "
            "preferred_brands = $preferred_brands",
            {
                "name": "Charlotte Gong",
                "city": "London",
                "state": None,
                "skin_type": "Combination",
                "hair_type": "Fine, straight",
                "concerns": ["Hydration", "Anti-aging prevention", "T-zone oil control", "Sensitivity"],
                "preferences": ["Korean skincare", "Multi-step routines", "Fragrance-free", "Lightweight textures"],
                "allergies": ["Synthetic fragrance", "Denatured alcohol"],
                "age": 27,
                "bio": "Junior architect in London with a passion for Korean-inspired multi-step skincare. Combination skin with dry cheeks and an oily T-zone. Focused on hydration and early anti-aging prevention.",
                "profile_type": "Skincare enthusiast",
                "experience_level": "Intermediate",
                "preferred_brands": ["LANEIGE", "Clinique", "The INKEY List", "Weleda", "NEOM"],
            },
        )

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

        # ── 5b. Charlotte's orders ────────────────────────────
        print("  + Charlotte's 5 orders")
        charlotte_orders = [
            {
                "id": "charlotte_ord_1",
                "total": 61.30,
                "products": ["457953cd", "919f3715", "70c32528"],
            },
            {
                "id": "charlotte_ord_2",
                "total": 24.79,
                "products": ["94e25ee5", "07761550"],
            },
            {
                "id": "charlotte_ord_3",
                "total": 50.00,
                "products": ["c6336fa9"],
            },
            {
                "id": "charlotte_ord_4",
                "total": 43.90,
                "products": ["fff0a542", "3fcd8dfe"],
            },
            {
                "id": "charlotte_ord_5",
                "total": 33.00,
                "products": ["ace5d86c"],
            },
        ]
        charlotte_product_ids: set[str] = set()
        for co in charlotte_orders:
            oid = co["id"]
            await db.query(
                f"CREATE order:`{oid}` SET price = $price, total = $total, "
                "status = 'delivered', currency = 'GBP'",
                {"price": co["total"], "total": co["total"]},
            )
            await db.query(f"RELATE customer:`charlotte_gong`->placed->order:`{oid}`")
            for pid in co["products"]:
                # Use first 8 chars as prefix — match full ID from products_raw
                full_pid = None
                for pr in products_raw:
                    if pr["product_id"].startswith(pid):
                        full_pid = pr["product_id"]
                        break
                if full_pid:
                    await db.query(f"RELATE order:`{oid}`->contains->product:`{full_pid}`")
                    charlotte_product_ids.add(full_pid)
                    customer_products["charlotte_gong"].add(full_pid)
                else:
                    print(f"    WARNING: Product {pid}... not found in CSV")

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

        # ── 6b. Charlotte's reviews ───────────────────────────
        print("  + Charlotte's 4 reviews")
        charlotte_reviews = [
            {
                "id": "charlotte_rev_1",
                "order": "charlotte_ord_1",
                "score": 5,
                "comment": "This cream is my holy grail — lightweight but deeply hydrating. My dry cheeks feel plump all day without making my T-zone greasy.",
                "sentiment": "positive",
            },
            {
                "id": "charlotte_rev_2",
                "order": "charlotte_ord_2",
                "score": 4,
                "comment": "Love the ceramide treatment for overnight repair. Woke up with visibly smoother skin. Only wish the tube was bigger.",
                "sentiment": "positive",
            },
            {
                "id": "charlotte_rev_3",
                "order": "charlotte_ord_3",
                "score": 5,
                "comment": "The Clinique set is perfect for travel. Moisture Surge is the best gel-cream I've tried — bouncy, fragrance-free hydration.",
                "sentiment": "positive",
            },
            {
                "id": "charlotte_rev_4",
                "order": "charlotte_ord_4",
                "score": 3,
                "comment": "The Weleda kit is very rich — almost too heavy for my combination skin. Great for winter evenings on dry patches only.",
                "sentiment": "neutral",
            },
        ]
        review_texts = [r["comment"] for r in charlotte_reviews]
        review_vecs = await embeddings.aembed_documents(review_texts)
        for r, vec in zip(charlotte_reviews, review_vecs):
            await db.query(
                f"CREATE review:`{r['id']}` SET "
                "score = $score, comment = $comment, sentiment = $sentiment, "
                "embedding = $embedding",
                {
                    "score": r["score"],
                    "comment": r["comment"],
                    "sentiment": r["sentiment"],
                    "embedding": vec,
                },
            )
            await db.query(f"RELATE order:`{r['order']}`->has_review->review:`{r['id']}`")

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
