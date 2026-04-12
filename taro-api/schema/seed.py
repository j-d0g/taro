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
from pathlib import Path
from collections import defaultdict
from itertools import combinations

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from env_bootstrap import load_app_dotenv
from langchain_openai import OpenAIEmbeddings

load_app_dotenv(api_root=Path(__file__).resolve().parent.parent)

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
            "preferred_brands = $preferred_brands, "
            "email = $email, goals = $goals, "
            "context = $context, memory = $memory",
            {
                "name": "Charlotte Gong",
                "city": "London",
                "state": None,
                "skin_type": "Combination",
                "hair_type": "Fine, straight, colour-treated (balayage)",
                "concerns": [
                    "Hydration", "Anti-aging prevention", "T-zone oil control",
                    "Sensitivity", "Hair volume", "Colour preservation",
                    "Dry elbows in winter", "Brittle nails",
                ],
                "preferences": [
                    "Korean skincare", "Multi-step routines", "Fragrance-free face products",
                    "Lightweight textures", "Gel-cream over heavy cream",
                    "Cruelty-free", "Vegan-preferred", "Sustainable packaging",
                    "Sulphate-free shampoo", "Light floral body scents",
                ],
                "allergies": ["Synthetic fragrance", "Denatured alcohol", "SLS/SLES", "Parabens"],
                "age": 27,
                "bio": (
                    "Junior architect in London with a passion for Korean-inspired "
                    "multi-step skincare. Combination skin with dry cheeks and an oily "
                    "T-zone. Fine colour-treated hair needing volume and protection. "
                    "Evening bath ritual lover. Researches ingredients before buying."
                ),
                "profile_type": "Beauty enthusiast",
                "experience_level": "Intermediate",
                "preferred_brands": [
                    "LANEIGE", "Clinique", "The INKEY List", "Weleda", "NEOM",
                    "Olaplex", "Moroccanoil", "Molton Brown",
                ],
                "email": "charlotte.gong@taro.ai",
                "goals": ["hydration", "anti_aging", "clear_skin", "sun_protection"],
                "context": (
                    "Charlotte is a 27-year-old skincare-maximalist architect in London "
                    "(hard water area, temperate humid climate). SKINCARE: Combination "
                    "skin — dry cheeks need deep hydration, oily T-zone needs oil control. "
                    "Runs a 5-7 step K-beauty routine AM & PM. Holy grail product is "
                    "Clinique Moisture Surge — she rated it 5/5 calling it 'bouncy, "
                    "fragrance-free hydration'. Loves gel-cream and water-based textures. "
                    "Hates heavy/rich creams — rated Weleda 3/5 saying 'too rich for "
                    "combination skin, winter only on dry patches'. Active ingredients "
                    "she already uses: hyaluronic acid, ceramides, retinol, niacinamide. "
                    "Started retinol at 27 for early anti-aging prevention. Strictly "
                    "avoids synthetic fragrance, denatured alcohol, SLS, and parabens. "
                    "HAIRCARE: Fine straight colour-treated hair (balayage). Washes 3x "
                    "per week. Needs volume without weight and colour protection. Uses "
                    "heat tools (blow-dry, occasional straightener). Oily roots, dry "
                    "ends. Prefers sulphate-free shampoo. BODY & FRAGRANCE: Loves "
                    "evening bath rituals with candles. Scent profile: light florals "
                    "(peony, bergamot, white tea) — dislikes musk and patchouli. "
                    "Fragrance-free on face but welcomes scent on body. Eczema-prone "
                    "elbows in winter. Brittle nails. LIFESTYLE: Urban office worker, "
                    "yoga 2x/week, budget sweet spot £15-55 per product, total spend "
                    "~£213 across 5 orders. Values cruelty-free, vegan-preferred, "
                    "sustainable packaging. Research-heavy buyer — reads ingredient "
                    "lists before purchasing. Switches routine seasonally: lighter in "
                    "summer, richer in winter."
                ),
                "memory": [
                    "Holy grail: Clinique Moisture Surge — lightweight, bouncy, fragrance-free gel-cream (rated 5/5)",
                    "Weleda kit too heavy for combination skin — only usable on dry patches in winter (rated 3/5)",
                    "Loves ceramide overnight repair — wanted a bigger tube (rated 4/5)",
                    "Prefers gel-cream and water-based textures over rich creams or oils",
                    "Travel-size sets appeal to her — rated Clinique travel set 5/5",
                    "Started retinol early (age 27) for anti-aging prevention via The INKEY List",
                    "Would rebuy: Moisture Surge, ceramide treatment. Would NOT rebuy: Weleda kit",
                    "Hair: needs volume products that won't weigh down fine hair or strip colour",
                    "Body: evening bath ritual person, loves peony and bergamot scents",
                    "Brittle nails — interested in biotin and nail treatments",
                ],
            },
        )

        # ── 3c. Jordan (grooming minimalist) ────────────────
        print("  + Jordan (demo customer — grooming minimalist)")
        await db.query(
            "CREATE customer:`jordan` SET "
            "name = $name, city = $city, state = $state, "
            "skin_type = $skin_type, hair_type = $hair_type, "
            "concerns = $concerns, preferences = $preferences, "
            "allergies = $allergies, age = $age, bio = $bio, "
            "profile_type = $profile_type, experience_level = $experience_level, "
            "preferred_brands = $preferred_brands, "
            "email = $email, goals = $goals, "
            "context = $context, memory = $memory",
            {
                "name": "Jordan",
                "city": "Manchester",
                "state": None,
                "skin_type": "Oily",
                "hair_type": "Thick, wavy, prone to frizz",
                "concerns": [
                    "Acne scarring", "Oily T-zone", "Large pores",
                    "Frizz control", "Razor burn", "Post-gym breakouts",
                ],
                "preferences": [
                    "Minimalist routine", "3 steps max", "Unscented",
                    "Matte finish", "Fast-absorbing", "No greasy residue",
                    "Gym-proof", "Anti-shine",
                ],
                "allergies": ["Coconut oil", "Heavy silicones"],
                "age": 26,
                "bio": (
                    "Personal trainer in Manchester. Oily skin that breaks out "
                    "after workouts. Wants a fast, no-fuss routine — cleanser, "
                    "treatment, moisturiser, done. Thick wavy hair that frizzes "
                    "in humidity. Prefers unscented, matte-finish products."
                ),
                "profile_type": "Grooming minimalist",
                "experience_level": "Beginner",
                "preferred_brands": [
                    "The INKEY List", "Clinique", "Moroccanoil",
                ],
                "email": "jordan@taro.ai",
                "goals": ["clear_skin", "hydration"],
                "context": (
                    "Jordan is a 26-year-old personal trainer in Manchester. "
                    "SKINCARE: Oily skin prone to post-gym breakouts and acne "
                    "scarring. Large pores on nose and cheeks. Hates greasy products "
                    "— needs matte finish that survives sweat. Runs a strict 3-step "
                    "routine: salicylic acid cleanser, niacinamide serum, lightweight "
                    "gel moisturiser. Rated The INKEY List Salicylic Acid Cleanser 5/5 "
                    "saying 'only cleanser that keeps my skin clear after heavy sessions'. "
                    "Tried Clinique Dramatically Different and liked it — light enough "
                    "for oily skin. Avoids coconut oil and heavy silicones. "
                    "HAIRCARE: Thick wavy hair that frizzes in Manchester humidity. "
                    "Washes daily after gym. Needs frizz control without weight. Tried "
                    "Moroccanoil Treatment and loved the shine without grease. "
                    "BODY & FRAGRANCE: Not into fragrance — prefers functional products. "
                    "Uses Molton Brown Eucalyptus shower gel post-gym for the cooling "
                    "effect. Gets razor burn on neck — needs soothing aftershave care. "
                    "LIFESTYLE: Trains 6x/week, outdoors and gym. Budget £5-25 per "
                    "product — value-focused. Total spend ~£95 across 3 orders. "
                    "Wants products that work, not luxury packaging."
                ),
                "memory": [
                    "Best cleanser: INKEY List Salicylic Acid — only thing keeping post-gym breakouts at bay (rated 5/5)",
                    "Clinique Dramatically Different works well for oily skin — lightweight enough (rated 4/5)",
                    "Moroccanoil Treatment gave great shine without weighing down thick hair (rated 4/5)",
                    "Hates greasy residue — any product must absorb fast",
                    "Gets razor burn easily — needs gentle, alcohol-free aftershave products",
                    "Molton Brown Eucalyptus shower gel is his post-gym staple",
                    "Wants to address acne scarring but doesn't know where to start",
                ],
            },
        )

        # ── 3d. Shaswat (ingredient-obsessed) ─────────────────
        print("  + Shaswat (demo customer — ingredient scientist)")
        await db.query(
            "CREATE customer:`shaswat` SET "
            "name = $name, city = $city, state = $state, "
            "skin_type = $skin_type, hair_type = $hair_type, "
            "concerns = $concerns, preferences = $preferences, "
            "allergies = $allergies, age = $age, bio = $bio, "
            "profile_type = $profile_type, experience_level = $experience_level, "
            "preferred_brands = $preferred_brands, "
            "email = $email, goals = $goals, "
            "context = $context, memory = $memory",
            {
                "name": "Shaswat",
                "city": "Cambridge",
                "state": None,
                "skin_type": "Dry, eczema-prone",
                "hair_type": "Straight, thinning at crown",
                "concerns": [
                    "Eczema flare-ups", "Barrier repair", "Redness",
                    "Hair thinning", "Scalp dryness", "Dry hands from lab work",
                ],
                "preferences": [
                    "Ingredient-first shopping", "Clinical formulations",
                    "Fragrance-free everything", "Ceramide-based",
                    "Dermatologist-recommended", "No essential oils",
                ],
                "allergies": ["Essential oils", "Lanolin", "Artificial dyes"],
                "age": 29,
                "bio": (
                    "PhD researcher at Cambridge. Extremely dry, eczema-prone skin — "
                    "reads every ingredient list before buying. Believes in ceramides, "
                    "peptides, and clinical evidence. Hair thinning at the crown, looking "
                    "for science-backed solutions. Fragrance-free absolutist."
                ),
                "profile_type": "Ingredient scientist",
                "experience_level": "Advanced",
                "preferred_brands": [
                    "The INKEY List", "Clinique", "Weleda", "The Ordinary",
                ],
                "email": "shaswat@taro.ai",
                "goals": ["hydration", "anti_aging", "hair_growth"],
                "context": (
                    "Shaswat is a 29-year-old PhD researcher in Cambridge with "
                    "extremely dry, eczema-prone skin. SKINCARE: Barrier repair is "
                    "his #1 priority. Uses ceramide-heavy routine — INKEY List Bio-Active "
                    "Ceramide Moisturizer is his staple (rated 5/5: 'finally a "
                    "moisturiser that calms my eczema without irritation'). Also uses "
                    "The Ordinary Multi-Peptide serum for anti-aging. Strictly avoids "
                    "essential oils, lanolin, and artificial dyes — all trigger flare-ups. "
                    "Fragrance-free absolutist. Reads clinical studies before trying "
                    "anything new. Rated Weleda Skin Food 3/5 — 'too many botanicals, "
                    "made my eczema worse'. HAIRCARE: Straight hair thinning at the "
                    "crown. Looking for evidence-based treatments — interested in "
                    "peptide-based scalp serums. Dry scalp from hard water in Cambridge. "
                    "BODY: Chronic dry hands from lab work — needs intensive hand cream. "
                    "No interest in fragrance or bath products. LIFESTYLE: Academic, "
                    "budget-conscious, £10-30 per product. Total spend ~£120 across "
                    "4 orders. Buys based on ingredient lists and PubMed, not marketing."
                ),
                "memory": [
                    "Holy grail: INKEY List Ceramide Moisturizer — only moisturiser that calms eczema (rated 5/5)",
                    "Weleda Skin Food triggered eczema — too many botanical extracts (rated 3/5)",
                    "The Ordinary Multi-Peptide serum is his anti-aging pick — values peptide science",
                    "Absolutely no essential oils — triggers eczema flare-ups immediately",
                    "Hair thinning at crown — wants science-backed peptide scalp treatments",
                    "Dry hands from lab work — needs intensive barrier repair hand cream",
                    "Reads PubMed before buying anything — respects clinical evidence over marketing",
                    "Fragrance-free absolutist across ALL categories",
                ],
            },
        )

        # ── 3e. Baran (fragrance collector) ────────────────────
        print("  + Baran (demo customer — fragrance collector)")
        await db.query(
            "CREATE customer:`baran` SET "
            "name = $name, city = $city, state = $state, "
            "skin_type = $skin_type, hair_type = $hair_type, "
            "concerns = $concerns, preferences = $preferences, "
            "allergies = $allergies, age = $age, bio = $bio, "
            "profile_type = $profile_type, experience_level = $experience_level, "
            "preferred_brands = $preferred_brands, "
            "email = $email, goals = $goals, "
            "context = $context, memory = $memory",
            {
                "name": "Baran",
                "city": "London",
                "state": None,
                "skin_type": "Normal",
                "hair_type": "Thick, curly, coarse",
                "concerns": [
                    "Fragrance layering", "Curl definition",
                    "Dry skin in winter", "Gift shopping",
                ],
                "preferences": [
                    "Luxury packaging", "Niche fragrances", "Woody and amber scents",
                    "Curl-friendly", "Sulphate-free", "Gift sets",
                    "Premium brands", "Candles and diffusers",
                ],
                "allergies": [],
                "age": 28,
                "bio": (
                    "Creative director at a branding agency in Shoreditch. Obsessed with "
                    "fragrance layering and collecting scents. Thick curly hair that needs "
                    "moisture and definition. Loves luxury packaging and premium gifting."
                ),
                "profile_type": "Fragrance collector",
                "experience_level": "Advanced",
                "preferred_brands": [
                    "Molton Brown", "Estée Lauder", "Sol de Janeiro", "NEOM",
                    "Moroccanoil",
                ],
                "email": "baran@taro.ai",
                "goals": ["hydration"],
                "context": (
                    "Baran is a 28-year-old creative director in Shoreditch, London. "
                    "SKINCARE: Normal skin, low-maintenance — Clinique Dramatically "
                    "Different is his daily moisturiser. Not fussy about skincare. "
                    "Gets dry in winter, uses richer cream seasonally. "
                    "HAIRCARE: Thick curly coarse hair — his biggest grooming focus. "
                    "Moroccanoil Treatment is essential for curl definition and shine "
                    "(rated 5/5: 'the only oil that doesn't weigh down my curls'). "
                    "Sulphate-free shampoo only. Weekly deep conditioning mask. "
                    "BODY & FRAGRANCE: This is his passion. Collects fragrances — "
                    "prefers woody, amber, oud notes. Loves Estée Lauder Bronze Goddess "
                    "Nuit (rated 5/5: 'complex, evening-perfect'). Molton Brown "
                    "Coastal Cypress is his everyday shower gel and hand wash. "
                    "Burns NEOM candles at home — owns 3 different scents. Buys gift "
                    "sets frequently for friends. Sol de Janeiro for summer body care. "
                    "LIFESTYLE: Design-conscious, cares about packaging aesthetics. "
                    "Budget £20-70 per product, higher for fragrances. Total spend "
                    "~£340 across 5 orders. Shops seasonally — woody in winter, "
                    "citrus/fresh in summer."
                ),
                "memory": [
                    "Fragrance obsessed: collects and layers scents — woody, amber, oud preferred",
                    "Moroccanoil Treatment is essential for his curls — only oil that works without weight (rated 5/5)",
                    "Estée Lauder Bronze Goddess Nuit is his signature evening scent (rated 5/5)",
                    "Molton Brown Coastal Cypress is his everyday scent — shower gel + hand wash",
                    "Burns NEOM candles at home — owns Happiness, Sleep, and Rosy scents",
                    "Buys gift sets frequently — good target for seasonal gift recommendations",
                    "Thick curly hair needs sulphate-free + deep conditioning weekly",
                    "Sol de Janeiro for summer body care — loves tropical scents in warm weather",
                ],
            },
        )

        # ── 3f. Desmond (anti-aging early adopter) ─────────────
        print("  + Desmond (demo customer — anti-aging early adopter)")
        await db.query(
            "CREATE customer:`desmond` SET "
            "name = $name, city = $city, state = $state, "
            "skin_type = $skin_type, hair_type = $hair_type, "
            "concerns = $concerns, preferences = $preferences, "
            "allergies = $allergies, age = $age, bio = $bio, "
            "profile_type = $profile_type, experience_level = $experience_level, "
            "preferred_brands = $preferred_brands, "
            "email = $email, goals = $goals, "
            "context = $context, memory = $memory",
            {
                "name": "Desmond",
                "city": "Edinburgh",
                "state": None,
                "skin_type": "Sensitive, dehydrated",
                "hair_type": "Short, low-maintenance buzz cut",
                "concerns": [
                    "Fine lines around eyes", "Dehydrated skin",
                    "Dark circles", "Sun damage prevention",
                    "Stress-related skin dullness",
                ],
                "preferences": [
                    "Anti-aging serums", "Eye creams", "SPF daily",
                    "Night repair treatments", "Luxury skincare",
                    "Relaxation and wellness", "Evidence-based",
                ],
                "allergies": ["Retinol above 0.5%", "Glycolic acid"],
                "age": 30,
                "bio": (
                    "Junior doctor in Edinburgh. Long hospital shifts leave his "
                    "skin dehydrated and dull. Started an anti-aging routine at 28 — "
                    "focused on eye cream, serums, and SPF. Sensitive skin that can't "
                    "tolerate strong actives. Uses NEOM for stress relief after shifts."
                ),
                "profile_type": "Anti-aging early adopter",
                "experience_level": "Intermediate",
                "preferred_brands": [
                    "Estée Lauder", "Clinique", "NEOM", "The Ordinary",
                ],
                "email": "desmond@taro.ai",
                "goals": ["anti_aging", "hydration", "sun_protection"],
                "context": (
                    "Desmond is a 30-year-old junior doctor in Edinburgh. "
                    "SKINCARE: Sensitive, dehydrated skin aggravated by long hospital "
                    "shifts and air conditioning. Primary concern is early anti-aging — "
                    "fine lines around eyes and forehead. Daily SPF is non-negotiable. "
                    "Holy grail: Estée Lauder Advanced Night Repair serum (rated 5/5: "
                    "'visible improvement in skin texture after 2 weeks'). Uses Estée "
                    "Lauder Eye Lift cream for dark circles from night shifts. "
                    "Can't tolerate retinol above 0.5% or glycolic acid — both cause "
                    "redness and peeling. The Ordinary Multi-Peptide serum is his "
                    "gentle anti-aging alternative. Clinique Dramatically Different "
                    "as daily moisturiser. HAIRCARE: Buzz cut, zero maintenance. Only "
                    "buys shampoo occasionally. BODY & FRAGRANCE: Uses NEOM for stress "
                    "relief — owns the Sleep essential oil blend and the Wellbeing Pod "
                    "diffuser. Burns NEOM candles during days off. Not a fragrance "
                    "collector but appreciates calming scents (lavender, chamomile). "
                    "LIFESTYLE: High-stress medical career, sleep-deprived. Budget "
                    "£15-55 per product — willing to invest in proven anti-aging. "
                    "Total spend ~£280 across 4 orders. Shops based on clinical "
                    "reviews and dermatologist recommendations."
                ),
                "memory": [
                    "Holy grail: Estée Lauder Advanced Night Repair — visible texture improvement in 2 weeks (rated 5/5)",
                    "Estée Lauder Eye Lift works well for dark circles from night shifts (rated 4/5)",
                    "Cannot tolerate retinol above 0.5% — causes redness and peeling",
                    "Cannot tolerate glycolic acid — too harsh for sensitive skin",
                    "The Ordinary Multi-Peptide serum is his gentle anti-aging pick",
                    "Uses NEOM Sleep essential oil + diffuser for stress relief after hospital shifts",
                    "Daily SPF is non-negotiable — sun damage prevention is top priority",
                    "Clinique Dramatically Different is reliable daily moisturiser",
                ],
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

        # ── 5c. Demo customer orders (Jordan, Shaswat, Baran, Desmond) ─
        demo_customers_orders = {
            "jordan": [
                {"id": "jordan_ord_1", "total": 16.60, "products": ["07761550", "ce5b9184"]},
                {"id": "jordan_ord_2", "total": 53.50, "products": ["53b36df6", "53c61580"]},
                {"id": "jordan_ord_3", "total": 25.50, "products": ["3fcd8dfe"]},
            ],
            "shaswat": [
                {"id": "shaswat_ord_1", "total": 15.19, "products": ["94e25ee5"]},
                {"id": "shaswat_ord_2", "total": 53.50, "products": ["3fcd8dfe", "19c91ef9"]},
                {"id": "shaswat_ord_3", "total": 7.00, "products": ["ce5b9184"]},
                {"id": "shaswat_ord_4", "total": 11.00, "products": ["d245838e"]},
            ],
            "baran": [
                {"id": "baran_ord_1", "total": 70.00, "products": ["629beb8e"]},
                {"id": "baran_ord_2", "total": 62.50, "products": ["53c61580", "47969dd9"]},
                {"id": "baran_ord_3", "total": 48.00, "products": ["53b36df6", "4a9947ec"]},
                {"id": "baran_ord_4", "total": 58.00, "products": ["01b154ce"]},
                {"id": "baran_ord_5", "total": 105.00, "products": ["bf06a69b"]},
            ],
            "desmond": [
                {"id": "desmond_ord_1", "total": 100.75, "products": ["e13cf838", "fedccbd5"]},
                {"id": "desmond_ord_2", "total": 18.40, "products": ["fff0a542"]},
                {"id": "desmond_ord_3", "total": 35.00, "products": ["ce5b9184", "19c91ef9"]},
                {"id": "desmond_ord_4", "total": 124.00, "products": ["f092eaa7", "e8349493"]},
            ],
        }
        for cust_id, orders_list in demo_customers_orders.items():
            print(f"  + {cust_id}'s {len(orders_list)} orders")
            for co in orders_list:
                oid = co["id"]
                await db.query(
                    f"CREATE order:`{oid}` SET price = $price, total = $total, "
                    "status = 'delivered', currency = 'GBP'",
                    {"price": co["total"], "total": co["total"]},
                )
                await db.query(f"RELATE customer:`{cust_id}`->placed->order:`{oid}`")
                for pid in co["products"]:
                    full_pid = None
                    for pr in products_raw:
                        if pr["product_id"].startswith(pid):
                            full_pid = pr["product_id"]
                            break
                    if full_pid:
                        await db.query(f"RELATE order:`{oid}`->contains->product:`{full_pid}`")
                        customer_products[cust_id].add(full_pid)
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

        # ── 6c. Demo customer reviews (Jordan, Shaswat, Baran, Desmond) ─
        demo_reviews = [
            # Jordan
            {
                "id": "jordan_rev_1", "order": "jordan_ord_1", "score": 5,
                "comment": "Only cleanser that keeps my skin clear after heavy gym sessions. No breakouts in 3 weeks — that's a first.",
                "sentiment": "positive",
            },
            {
                "id": "jordan_rev_2", "order": "jordan_ord_2", "score": 4,
                "comment": "Moroccanoil tames my frizz without making my hair greasy. Light enough for daily use after washing.",
                "sentiment": "positive",
            },
            {
                "id": "jordan_rev_3", "order": "jordan_ord_2", "score": 5,
                "comment": "Eucalyptus shower gel is perfect post-workout — cooling sensation and the scent doesn't linger too long.",
                "sentiment": "positive",
            },
            # Shaswat
            {
                "id": "shaswat_rev_1", "order": "shaswat_ord_1", "score": 5,
                "comment": "Finally a moisturiser that calms my eczema without irritation. Ceramide-based, fragrance-free, no essential oils — exactly what my skin needs.",
                "sentiment": "positive",
            },
            {
                "id": "shaswat_rev_2", "order": "shaswat_ord_2", "score": 3,
                "comment": "Weleda Skin Food has too many botanical extracts for eczema-prone skin. Triggered a mild flare-up on my cheeks. Returned to my ceramide routine.",
                "sentiment": "negative",
            },
            {
                "id": "shaswat_rev_3", "order": "shaswat_ord_2", "score": 4,
                "comment": "The Ordinary Multi-Peptide serum absorbs well and no irritation. Good evidence for peptides in anti-aging. Will repurchase.",
                "sentiment": "positive",
            },
            # Baran
            {
                "id": "baran_rev_1", "order": "baran_ord_1", "score": 5,
                "comment": "Bronze Goddess Nuit is intoxicating — complex amber and sandalwood, perfect for evenings out. Gets compliments every time.",
                "sentiment": "positive",
            },
            {
                "id": "baran_rev_2", "order": "baran_ord_2", "score": 5,
                "comment": "Moroccanoil is the only oil that defines my curls without weighing them down. Smells incredible too.",
                "sentiment": "positive",
            },
            {
                "id": "baran_rev_3", "order": "baran_ord_4", "score": 4,
                "comment": "NEOM Rosy candle fills the whole flat — beautiful floral scent. Burns evenly. Bought another as a gift for my mum.",
                "sentiment": "positive",
            },
            # Desmond
            {
                "id": "desmond_rev_1", "order": "desmond_ord_1", "score": 5,
                "comment": "Advanced Night Repair changed my skin — visible improvement in texture and fine lines after just 2 weeks. Worth every penny for night shift recovery.",
                "sentiment": "positive",
            },
            {
                "id": "desmond_rev_2", "order": "desmond_ord_1", "score": 4,
                "comment": "Eye Lift cream reduced my dark circles noticeably. Not a miracle cure for sleep deprivation, but the best eye cream I've tried.",
                "sentiment": "positive",
            },
            {
                "id": "desmond_rev_3", "order": "desmond_ord_2", "score": 5,
                "comment": "NEOM Sleep oil is my wind-down ritual after night shifts. Few drops on the pillow and I'm out. Lavender and chamomile blend is perfect.",
                "sentiment": "positive",
            },
        ]
        print(f"  + {len(demo_reviews)} demo customer reviews")
        demo_review_texts = [r["comment"] for r in demo_reviews]
        demo_review_vecs = await embeddings.aembed_documents(demo_review_texts)
        for r, vec in zip(demo_reviews, demo_review_vecs):
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
