"""Seed script: populates SurrealDB with mock dataset for Taro.ai hackathon.

Seeds rich mock data including:
- 15 user personas with preferences, context, and memory
- ~130 products across Beauty/Fitness/Wellness verticals
- 38 orders with coherent purchase patterns
- 38 reviews with realistic comments and sentiment
- 9 goals, 20 ingredients with product mappings
- 9 graph edge types connecting everything
- Product + FAQ documents with vector embeddings

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

# Import mock data
sys.path.insert(0, os.path.dirname(__file__))
from mock_data import (
    GOALS,
    INGREDIENTS,
    ORDERS,
    ORDER_PRODUCT_FIXUPS,
    PRODUCT_GOAL_EDGES,
    PRODUCT_INGREDIENT_EDGES,
    PRODUCTS,
    RELATED_PRODUCTS,
    REVIEWS,
    USERS,
)

FAQ_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "Datasets", "bitext_faq.csv")
EMBED_BATCH = 100


def make_cat_id(name: str) -> str:
    """Sanitise a category name into a SurrealDB record ID slug."""
    return name.lower().replace(" ", "_").replace("&", "and")


async def seed():
    print("Loading mock data...")
    print(f"  users:       {len(USERS)}")
    print(f"  products:    {len(PRODUCTS)}")
    print(f"  orders:      {len(ORDERS)}")
    print(f"  reviews:     {len(REVIEWS)}")
    print(f"  goals:       {len(GOALS)}")
    print(f"  ingredients: {len(INGREDIENTS)}")

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

        # ── 1. Categories ────────────────────────────────────
        print("\n[1/10] Seeding categories...")
        verticals = set()
        subcats = set()
        for p in PRODUCTS:
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

        # ── 2. Goals ─────────────────────────────────────────
        print("[2/10] Seeding goals...")
        for g in GOALS:
            await db.query(
                f"CREATE goal:`{g['id']}` SET name = $name, description = $desc, vertical = $vertical",
                {"name": g["name"], "desc": g.get("description"), "vertical": g.get("vertical")},
            )
        print(f"  {len(GOALS)} goals")

        # ── 3. Ingredients ───────────────────────────────────
        print("[3/10] Seeding ingredients...")
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

        # ── 4. Users ─────────────────────────────────────────
        print("[4/10] Seeding users...")
        for u in USERS:
            await db.query(
                f"CREATE user:`{u['id']}` SET "
                "name = $name, email = $email, city = $city, age = $age, "
                "profile_type = $profile_type, experience_level = $exp_level, "
                "goals = $goals, dietary_restrictions = $dietary, "
                "preferred_brands = $brands, skin_type = $skin_type, "
                "context = $context, memory = $memory",
                {
                    "name": u["name"],
                    "email": u.get("email"),
                    "city": u.get("city"),
                    "age": u.get("age"),
                    "profile_type": u.get("profile_type"),
                    "exp_level": u.get("experience_level"),
                    "goals": u.get("goals", []),
                    "dietary": u.get("dietary_restrictions", []),
                    "brands": u.get("preferred_brands", []),
                    "skin_type": u.get("skin_type"),
                    "context": u.get("context"),
                    "memory": u.get("memory", []),
                },
            )
        print(f"  {len(USERS)} users")

        # ── 5. Products + belongs_to ─────────────────────────
        print("[5/10] Seeding products...")
        for p in PRODUCTS:
            pid = p["id"]
            await db.query(
                f"CREATE product:`{pid}` SET "
                "name = $name, vertical = $vertical, subcategory = $subcat, "
                "category = $subcat, price = $price, avg_rating = $rating, "
                "description = $desc, brand = $brand, ingredients = $ingredients, "
                "tags = $tags, dietary_tags = $dietary_tags, "
                "weight_g = $weight, image_url = $image_url",
                {
                    "name": p["name"],
                    "vertical": p.get("vertical"),
                    "subcat": p.get("subcategory"),
                    "price": p.get("price"),
                    "rating": p.get("avg_rating"),
                    "desc": p.get("description"),
                    "brand": p.get("brand"),
                    "ingredients": p.get("ingredients", []),
                    "tags": p.get("tags", []),
                    "dietary_tags": p.get("dietary_tags", []),
                    "weight": p.get("weight_g"),
                    "image_url": p.get("image_url", ""),
                },
            )
            subcat = p.get("subcategory", "")
            vertical = p.get("vertical", "")
            if subcat and vertical:
                sid = make_cat_id(f"{vertical}__{subcat}")
                await db.query(f"RELATE product:`{pid}`->belongs_to->category:`{sid}`")

        print(f"  {len(PRODUCTS)} products")

        # ── 6. Orders + placed_by + contains ─────────────────
        print("[6/10] Seeding orders...")
        for o in ORDERS:
            oid = o["id"]
            uid = o["user_id"]
            await db.query(
                f"CREATE order:`{oid}` SET total = $total, price = $total, "
                "status = $status, order_date = $order_date, currency = 'GBP'",
                {
                    "total": o.get("total"),
                    "status": o.get("status", "delivered"),
                    "order_date": o.get("order_date"),
                },
            )
            # user -placed_by-> order
            await db.query(f"RELATE user:`{uid}`->placed_by->order:`{oid}`")
            # order -contains-> product
            for pid in o.get("products", []):
                # Apply fixups for any product ID mismatches
                pid = ORDER_PRODUCT_FIXUPS.get(pid, pid)
                await db.query(f"RELATE order:`{oid}`->contains->product:`{pid}`")

        print(f"  {len(ORDERS)} orders")

        # ── 7. Reviews + has_review + embeddings ─────────────
        print("[7/10] Seeding reviews (with embeddings)...")
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        for i in range(0, len(REVIEWS), EMBED_BATCH):
            batch = REVIEWS[i : i + EMBED_BATCH]
            texts = [r.get("comment", "") or "" for r in batch]
            non_empty = [(j, t) for j, t in enumerate(texts) if t.strip()]

            vecs = {}
            if non_empty:
                embedded = await embeddings.aembed_documents([t for _, t in non_empty])
                for (j, _), vec in zip(non_empty, embedded):
                    vecs[j] = vec

            for j, r in enumerate(batch):
                rid = r["id"]
                oid = r["order_id"]
                vec = vecs.get(j)
                await db.query(
                    f"CREATE review:`{rid}` SET "
                    "score = $score, comment = $comment, sentiment = $sentiment, "
                    "embedding = $embedding",
                    {
                        "score": r.get("score", 0),
                        "comment": r.get("comment"),
                        "sentiment": r.get("sentiment"),
                        "embedding": vec,
                    },
                )
                await db.query(f"RELATE order:`{oid}`->has_review->review:`{rid}`")

            print(f"  {min(i + EMBED_BATCH, len(REVIEWS))}/{len(REVIEWS)}")

        # ── 8. Graph edges: supports_goal, contains_ingredient, related_to, also_bought ──
        print("[8/10] Seeding graph edges...")

        # supports_goal: product -> goal
        for pid, gid in PRODUCT_GOAL_EDGES:
            await db.query(f"RELATE product:`{pid}`->supports_goal->goal:`{gid}`")
        print(f"  {len(PRODUCT_GOAL_EDGES)} supports_goal edges")

        # contains_ingredient: product -> ingredient
        for pid, iid, conc in PRODUCT_INGREDIENT_EDGES:
            await db.query(
                f"RELATE product:`{pid}`->contains_ingredient->ingredient:`{iid}` "
                "SET concentration = $conc",
                {"conc": conc},
            )
        print(f"  {len(PRODUCT_INGREDIENT_EDGES)} contains_ingredient edges")

        # related_to: product <-> product (bidirectional)
        for pid_a, pid_b, reason in RELATED_PRODUCTS:
            await db.query(
                f"RELATE product:`{pid_a}`->related_to->product:`{pid_b}` SET reason = $reason",
                {"reason": reason},
            )
            await db.query(
                f"RELATE product:`{pid_b}`->related_to->product:`{pid_a}` SET reason = $reason",
                {"reason": reason},
            )
        print(f"  {len(RELATED_PRODUCTS) * 2} related_to edges (bidirectional)")

        # also_bought: derived from co-purchase in orders
        user_products: dict[str, set[str]] = defaultdict(set)
        for o in ORDERS:
            for pid in o.get("products", []):
                pid = ORDER_PRODUCT_FIXUPS.get(pid, pid)
                user_products[o["user_id"]].add(pid)

        also_bought: dict[tuple[str, str], int] = {}
        for _uid, products in user_products.items():
            if len(products) < 2:
                continue
            for a, b in combinations(sorted(products), 2):
                for pair in [(a, b), (b, a)]:
                    also_bought[pair] = also_bought.get(pair, 0) + 1

        for (pid_a, pid_b), weight in also_bought.items():
            await db.query(
                f"RELATE product:`{pid_a}`->also_bought->product:`{pid_b}` SET weight = $w",
                {"w": weight},
            )
        print(f"  {len(also_bought)} also_bought edges (derived)")

        # ── 9. Documents with embeddings ─────────────────────
        print("[9/10] Seeding product documents (with embeddings)...")
        for i in range(0, len(PRODUCTS), EMBED_BATCH):
            batch = PRODUCTS[i : i + EMBED_BATCH]
            texts = []
            for p in batch:
                desc = p.get("description", "") or ""
                brand = p.get("brand", "") or ""
                tags = ", ".join(p.get("tags", []))
                text = f"{p['name']} by {brand}: {desc} Tags: {tags}"
                texts.append(text)

            vecs = await embeddings.aembed_documents(texts)

            for p, vec in zip(batch, vecs):
                pid = p["id"]
                doc_id = f"prod_{pid}"
                desc = p.get("description", "") or ""
                brand = p.get("brand", "") or ""
                tags = ", ".join(p.get("tags", []))
                content = f"{p['name']} by {brand}: {desc} Tags: {tags}"
                await db.query(
                    f"CREATE documents:`{doc_id}` SET "
                    "doc_type = 'product', title = $title, content = $content, "
                    "source_id = $source_id, metadata = $meta, embedding = $embedding",
                    {
                        "title": p["name"],
                        "content": content,
                        "source_id": f"product:`{pid}`",
                        "meta": {
                            "product_id": pid,
                            "price": p.get("price"),
                            "vertical": p.get("vertical"),
                            "subcategory": p.get("subcategory"),
                            "brand": brand,
                        },
                        "embedding": vec,
                    },
                )
            print(f"  {min(i + EMBED_BATCH, len(PRODUCTS))}/{len(PRODUCTS)}")

        # ── 10. FAQ documents ────────────────────────────────
        print("[10/10] Seeding FAQ documents...")
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
        print(f"    {len(USERS):>6} users (with preferences, context, memory)")
        print(f"    {len(PRODUCTS):>6} products (with brand, ingredients, tags)")
        print(f"    {len(verticals) + len(subcats):>6} categories ({len(verticals)} verticals + {len(subcats)} subcategories)")
        print(f"    {len(ORDERS):>6} orders")
        print(f"    {len(REVIEWS):>6} reviews (with embeddings)")
        print(f"    {len(GOALS):>6} goals")
        print(f"    {len(INGREDIENTS):>6} ingredients")
        print(f"  Edges (9 types):")
        print(f"    placed_by:           user -> order")
        print(f"    contains:            order -> product")
        print(f"    has_review:          order -> review")
        print(f"    belongs_to:          product -> category")
        print(f"    child_of:            subcategory -> vertical")
        print(f"    supports_goal:       {len(PRODUCT_GOAL_EDGES):>4} product -> goal")
        print(f"    contains_ingredient: {len(PRODUCT_INGREDIENT_EDGES):>4} product -> ingredient")
        print(f"    related_to:          {len(RELATED_PRODUCTS) * 2:>4} product <-> product")
        print(f"    also_bought:         {len(also_bought):>4} product <-> product (derived)")
        print(f"  Documents:")
        print(f"    {len(PRODUCTS):>6} product docs (vector + BM25)")
        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(seed())
