"""Seed script: populates SurrealDB with sample products, categories, and FAQs.

Usage: python schema/seed.py
"""

import asyncio
import os
import sys

# Add src to path for db module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

from db import get_db

# ── Sample data ──────────────────────────────────────────────

CATEGORIES = [
    {"id": "category:protein", "name": "Protein", "description": "Protein supplements for muscle growth and recovery"},
    {"id": "category:vitamins", "name": "Vitamins & Minerals", "description": "Essential vitamins and mineral supplements"},
    {"id": "category:snacks", "name": "Protein Snacks", "description": "High-protein snacks and bars"},
    {"id": "category:clothing", "name": "Activewear", "description": "Gym and fitness clothing"},
    {"id": "category:accessories", "name": "Accessories", "description": "Gym accessories and equipment"},
]

PRODUCTS = [
    {
        "id": "product:impact_whey",
        "name": "Impact Whey Protein",
        "brand": "Myprotein",
        "description": "Our bestselling whey protein powder. 21g protein per serving with great taste. Available in 40+ flavours including Chocolate Smooth, Vanilla, and Strawberry Cream. Ideal for post-workout recovery and muscle building.",
        "price": 18.99,
        "category": "Protein",
        "flavours": ["Chocolate Smooth", "Vanilla", "Strawberry Cream", "Salted Caramel", "Banana"],
        "key_benefits": ["21g protein per serving", "4.5g BCAAs", "Low fat", "Fast absorbing"],
        "url": "https://www.myprotein.com/sports-nutrition/impact-whey-protein/10530943.html",
    },
    {
        "id": "product:whey_isolate",
        "name": "Impact Whey Isolate",
        "brand": "Myprotein",
        "description": "Premium whey protein isolate with 23g protein per serving and less than 1g fat. Ultra-pure filtration process removes excess carbs and fat. Perfect for lean muscle building and those watching their macros.",
        "price": 24.99,
        "category": "Protein",
        "flavours": ["Chocolate Smooth", "Vanilla", "Unflavoured", "Strawberry Cream"],
        "key_benefits": ["23g protein per serving", "<1g fat", "Low carb", "90% protein content"],
        "url": "https://www.myprotein.com/sports-nutrition/impact-whey-isolate/10530911.html",
    },
    {
        "id": "product:creatine_mono",
        "name": "Creatine Monohydrate Powder",
        "brand": "Myprotein",
        "description": "Pure creatine monohydrate for improved strength and power. 3g creatine per serving. The most researched sports supplement, proven to increase physical performance in successive bursts of short-term, high-intensity exercise.",
        "price": 9.99,
        "category": "Protein",
        "flavours": ["Unflavoured", "Berry Blast", "Tropical"],
        "key_benefits": ["3g creatine per serving", "Improves strength", "Increases power output", "Clinically proven"],
        "url": "https://www.myprotein.com/sports-nutrition/creatine-monohydrate-powder/10530069.html",
    },
    {
        "id": "product:protein_bar",
        "name": "Layered Protein Bar",
        "brand": "Myprotein",
        "description": "Indulgent 6-layer protein bar with 20g protein. Triple Chocolate Fudge flavour. A convenient high-protein snack that tastes like a chocolate bar but delivers serious nutrition.",
        "price": 2.99,
        "category": "Protein Snacks",
        "flavours": ["Triple Chocolate Fudge", "Cookies & Cream", "Birthday Cake"],
        "key_benefits": ["20g protein", "6 indulgent layers", "Low sugar", "On-the-go nutrition"],
        "url": "https://www.myprotein.com/sports-nutrition/layered-protein-bar/11092400.html",
    },
    {
        "id": "product:multivitamin",
        "name": "Alpha Men Multivitamin",
        "brand": "Myprotein",
        "description": "Comprehensive daily multivitamin for active men. Contains essential vitamins A, C, D, E, K and minerals including zinc, magnesium, and selenium. Supports immune function, energy metabolism, and overall wellbeing.",
        "price": 8.99,
        "category": "Vitamins & Minerals",
        "flavours": [],
        "key_benefits": ["Complete A-Z vitamins", "Added zinc & magnesium", "Supports immunity", "One-a-day convenience"],
        "url": "https://www.myprotein.com/sports-nutrition/alpha-men-multivitamin/10529801.html",
    },
]

FAQS = [
    {
        "title": "How do I return an item?",
        "content": "You can return any unwanted items within 30 days of delivery. Items must be unused and in original packaging. Log into your account, go to Order History, select the item, and click 'Request Return'. You'll receive a prepaid returns label via email. Drop the parcel at your nearest collection point.",
    },
    {
        "title": "What is the delivery time?",
        "content": "Standard delivery takes 3-5 working days and is free on orders over 45 GBP. Express delivery (1-2 working days) is available for 4.99 GBP. Next-day delivery is available for 5.99 GBP if ordered before 9pm. Track your order in your account under Order History.",
    },
]

# ── Graph relations ──────────────────────────────────────────

RELATIONS = [
    # Products -> Categories
    ("product:impact_whey", "belongs_to", "category:protein"),
    ("product:whey_isolate", "belongs_to", "category:protein"),
    ("product:creatine_mono", "belongs_to", "category:protein"),
    ("product:protein_bar", "belongs_to", "category:snacks"),
    ("product:multivitamin", "belongs_to", "category:vitamins"),
    # Category hierarchy
    ("category:snacks", "child_of", "category:protein"),
    # Related products
    ("product:impact_whey", "related_to", "product:whey_isolate"),
    ("product:impact_whey", "related_to", "product:creatine_mono"),
    ("product:whey_isolate", "related_to", "product:impact_whey"),
    ("product:creatine_mono", "related_to", "product:protein_bar"),
]

RELATION_REASONS = {
    ("product:impact_whey", "product:whey_isolate"): "Same protein line, isolate is premium version",
    ("product:impact_whey", "product:creatine_mono"): "Commonly stacked together for strength training",
    ("product:whey_isolate", "product:impact_whey"): "Same protein line, whey is budget-friendly version",
    ("product:creatine_mono", "product:protein_bar"): "Both popular post-workout supplements",
}


async def seed():
    print("Connecting to SurrealDB...")
    async with get_db() as db:
        # Apply schema
        print("Applying schema...")
        schema_path = os.path.join(os.path.dirname(__file__), "schema.surql")
        with open(schema_path) as f:
            schema = f.read()
        # Execute each statement separately (SurrealDB needs individual statements)
        for statement in schema.split(";"):
            stmt = statement.strip()
            if stmt and not stmt.startswith("--"):
                try:
                    await db.query(stmt)
                except Exception as e:
                    print(f"  Schema warning: {e}")

        # Generate embeddings
        print("Generating embeddings...")
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        # Seed categories
        print("Seeding categories...")
        for cat in CATEGORIES:
            await db.query(
                f"CREATE {cat['id']} SET name = $name, description = $desc",
                {"name": cat["name"], "desc": cat["description"]},
            )

        # Seed products + documents
        print("Seeding products and documents...")
        for prod in PRODUCTS:
            # Create structured product record
            await db.query(
                f"CREATE {prod['id']} SET "
                "name = $name, brand = $brand, description = $desc, "
                "price = $price, category = $cat, flavours = $flavours, "
                "key_benefits = $benefits, url = $url",
                {
                    "name": prod["name"],
                    "brand": prod["brand"],
                    "desc": prod["description"],
                    "price": prod["price"],
                    "cat": prod["category"],
                    "flavours": prod["flavours"],
                    "benefits": prod["key_benefits"],
                    "url": prod["url"],
                },
            )

            # Create searchable document with embedding
            doc_content = f"{prod['name']}: {prod['description']} Benefits: {', '.join(prod['key_benefits'])}."
            embedding = await embeddings.aembed_query(doc_content)
            doc_id = prod["id"].replace("product:", "documents:prod_")
            await db.query(
                f"CREATE {doc_id} SET "
                "doc_type = 'product', title = $title, content = $content, "
                "source_id = $source_id, metadata = $meta, embedding = $embedding",
                {
                    "title": prod["name"],
                    "content": doc_content,
                    "source_id": prod["id"],
                    "meta": {"product_id": prod["id"], "price": prod["price"], "category": prod["category"]},
                    "embedding": embedding,
                },
            )

        # Seed FAQs as documents
        print("Seeding FAQs...")
        for i, faq in enumerate(FAQS):
            embedding = await embeddings.aembed_query(f"{faq['title']} {faq['content']}")
            await db.query(
                f"CREATE documents:faq_{i} SET "
                "doc_type = 'faq', title = $title, content = $content, "
                "metadata = $meta, embedding = $embedding",
                {
                    "title": faq["title"],
                    "content": faq["content"],
                    "meta": {"faq_index": i},
                    "embedding": embedding,
                },
            )

        # Create graph relations
        print("Creating graph relations...")
        for from_id, edge, to_id in RELATIONS:
            reason = RELATION_REASONS.get((from_id, to_id))
            if reason:
                await db.query(
                    f"RELATE {from_id}->{edge}->{to_id} SET reason = $reason",
                    {"reason": reason},
                )
            else:
                await db.query(f"RELATE {from_id}->{edge}->{to_id}")

        print(f"\nSeeded: {len(PRODUCTS)} products, {len(CATEGORIES)} categories, "
              f"{len(FAQS)} FAQs, {len(RELATIONS)} relations")
        print("Done!")


if __name__ == "__main__":
    asyncio.run(seed())
