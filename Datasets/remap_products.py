"""
Remap trimmed Olist products to THG-style verticals.
Only modifies products.csv — all other files stay the same.
"""

import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

TRIMMED = Path(__file__).parent / "trimmed"

# ── Step 1: Map 64 Olist categories → 3 verticals + subcategories ────

CATEGORY_MAP = {
    # ── FITNESS & NUTRITION ──
    "sports_leisure":           ("Fitness", "Equipment"),
    "food_drink":               ("Fitness", "Nutrition"),
    "food":                     ("Fitness", "Nutrition"),
    "drinks":                   ("Fitness", "Drinks"),
    "consoles_games":           ("Fitness", "Equipment"),
    "auto":                     ("Fitness", "Equipment"),
    "cool_stuff":               ("Fitness", "Accessories"),
    "toys":                     ("Fitness", "Accessories"),
    "luggage_accessories":      ("Fitness", "Accessories"),

    # ── BEAUTY & SKINCARE ──
    "health_beauty":            ("Beauty", "Skincare"),
    "perfumery":                ("Beauty", "Fragrance"),
    "fashion_bags_accessories": ("Beauty", "Accessories"),
    "fashion_shoes":            ("Beauty", "Accessories"),
    "fashion_male_clothing":    ("Beauty", "Grooming"),
    "fashion_underwear_beach":  ("Beauty", "Body Care"),
    "fashio_female_clothing":   ("Beauty", "Accessories"),
    "fashion_childrens_clothes":("Beauty", "Accessories"),
    "diapers_and_hygiene":      ("Beauty", "Body Care"),
    "bed_bath_table":           ("Beauty", "Bath & Body"),
    "housewares":               ("Beauty", "Tools"),
    "home_appliances":          ("Beauty", "Tools"),
    "home_appliances_2":        ("Beauty", "Tools"),
    "small_appliances":         ("Beauty", "Tools"),
    "small_appliances_home_oven_and_coffee": ("Beauty", "Tools"),
    "home_confort":             ("Beauty", "Bath & Body"),
    "home_comfort_2":           ("Beauty", "Bath & Body"),

    # ── WELLNESS ──
    "baby":                     ("Wellness", "Family Health"),
    "pet_shop":                 ("Wellness", "Lifestyle"),
    "garden_tools":             ("Wellness", "Lifestyle"),
    "watches_gifts":            ("Wellness", "Gifts"),
    "stationery":               ("Wellness", "Mindfulness"),
    "books_general_interest":   ("Wellness", "Mindfulness"),
    "books_technical":          ("Wellness", "Mindfulness"),
    "books_imported":           ("Wellness", "Mindfulness"),
    "musical_instruments":      ("Wellness", "Mindfulness"),
    "dvds_blu_ray":             ("Wellness", "Mindfulness"),
    "art":                      ("Wellness", "Mindfulness"),
    "christmas_supplies":       ("Wellness", "Gifts"),
    "market_place":             ("Wellness", "Lifestyle"),

    # ── Map remaining to best-fit vertical ──
    "furniture_decor":          ("Wellness", "Home Wellness"),
    "furniture_living_room":    ("Wellness", "Home Wellness"),
    "furniture_bedroom":        ("Wellness", "Home Wellness"),
    "furniture_mattress_and_upholstery": ("Wellness", "Sleep"),
    "office_furniture":         ("Wellness", "Home Wellness"),
    "kitchen_dining_laundry_garden_furniture": ("Wellness", "Home Wellness"),
    "computers_accessories":    ("Fitness", "Tech"),
    "computers":                ("Fitness", "Tech"),
    "telephony":                ("Fitness", "Tech"),
    "fixed_telephony":          ("Fitness", "Tech"),
    "tablets_printing_image":   ("Fitness", "Tech"),
    "electronics":              ("Fitness", "Tech"),
    "audio":                    ("Fitness", "Tech"),
    "cine_photo":               ("Fitness", "Tech"),
    "air_conditioning":         ("Wellness", "Home Wellness"),
    "construction_tools_construction": ("Wellness", "Lifestyle"),
    "construction_tools_lights":("Wellness", "Lifestyle"),
    "construction_tools_safety":("Wellness", "Lifestyle"),
    "costruction_tools_garden": ("Wellness", "Lifestyle"),
    "costruction_tools_tools":  ("Wellness", "Lifestyle"),
    "home_construction":        ("Wellness", "Home Wellness"),
    "signaling_and_security":   ("Wellness", "Lifestyle"),
    "industry_commerce_and_business": ("Wellness", "Lifestyle"),
    "agro_industry_and_commerce":("Wellness", "Lifestyle"),
    "portateis_cozinha_e_preparadores_de_alimentos": ("Fitness", "Nutrition"),
}

# ── Step 2: Product name pools per vertical + subcategory ────────────

PRODUCT_NAMES = {
    ("Fitness", "Protein"): [
        "Impact Whey Protein 1kg Chocolate",
        "Impact Whey Protein 1kg Vanilla",
        "Impact Whey Protein 2.5kg Strawberry",
        "Impact Whey Isolate 1kg Unflavoured",
        "Impact Whey Isolate 500g Salted Caramel",
        "Vegan Protein Blend 1kg Banana",
        "Vegan Protein Blend 500g Coffee & Walnut",
        "Clear Whey Isolate 500g Peach Tea",
        "Clear Whey Isolate 500g Bitter Lemon",
        "Casein Protein 1kg Chocolate",
        "Soy Protein Isolate 1kg Unflavoured",
        "Collagen Protein 500g Berry",
    ],
    ("Fitness", "Supplements"): [
        "Creatine Monohydrate 250g",
        "Creatine Monohydrate 500g",
        "BCAA 2:1:1 Powder 250g Tropical",
        "L-Glutamine Powder 500g",
        "Beta-Alanine Powder 250g",
        "ZMA Capsules 90 tabs",
        "HMB Tablets 180 tabs",
        "L-Carnitine Liquid 500ml Berry",
        "Electrolyte Plus Powder 250g Lemon",
        "EAA Powder 500g Cola",
    ],
    ("Fitness", "Pre-Workout"): [
        "THE Pre-Workout 300g Blue Raspberry",
        "THE Pre-Workout 300g Orange Mango",
        "Impact Pre-Workout 250g Fruit Punch",
        "Caffeine Pro 200mg 100 tabs",
        "Mypre 2.0 420g Sour Apple",
        "Energy Gel 70ml Citrus (12 pack)",
    ],
    ("Fitness", "Equipment"): [
        "Gym Shaker Bottle 700ml",
        "Resistance Band Set (3 pack)",
        "Foam Roller 45cm",
        "Lifting Gloves Size M",
        "Lifting Gloves Size L",
        "Gym Towel Microfibre",
        "Skipping Rope Pro",
        "Yoga Mat 6mm Grey",
        "Yoga Mat 6mm Black",
        "Pull-Up Bar Doorframe",
        "Ab Roller Wheel",
        "Gym Duffel Bag 40L",
    ],
    ("Fitness", "Accessories"): [
        "Sports Water Bottle 750ml",
        "Meal Prep Containers (10 pack)",
        "Gym Headband 3-pack",
        "Wrist Wraps Pair",
        "Knee Sleeves Pair",
        "Pill Box 7-Day",
    ],
    ("Fitness", "Nutrition"): [
        "Protein Flapjack Bar 70g Chocolate",
        "Protein Flapjack Bar 70g Oat & Raisin",
        "Layered Protein Bar 60g Cookies & Cream",
        "Layered Protein Bar 60g Peanut Butter",
        "Protein Cookie 75g White Choc Almond",
        "Protein Brownie 75g Double Chocolate",
        "Peanut Butter Crunchy 1kg",
        "Peanut Butter Smooth 1kg",
        "Instant Oats 2.5kg",
        "Protein Pancake Mix 500g",
        "Zero Sugar Syrup Maple 400ml",
        "Protein Spread Chocolate 360g",
    ],
    ("Fitness", "Drinks"): [
        "Protein Shake RTD 330ml Chocolate",
        "BCAA Energy Drink 330ml Tropical",
        "Zero Calorie Drops 50ml Strawberry",
        "Coconut Water 330ml",
    ],
    ("Fitness", "Tech"): [
        "Smart Fitness Tracker Band",
        "Bluetooth Sport Earbuds",
        "Digital Kitchen Scale",
        "Smart Water Bottle LED",
        "Heart Rate Monitor Chest Strap",
        "Wireless Gym Speaker Mini",
    ],
    ("Beauty", "Skincare"): [
        "Vitamin C Brightening Serum 30ml",
        "Hyaluronic Acid Serum 30ml",
        "Retinol Night Serum 30ml",
        "Niacinamide 10% Serum 30ml",
        "AHA BHA Exfoliating Toner 200ml",
        "Gentle Foaming Cleanser 150ml",
        "Micellar Cleansing Water 400ml",
        "Daily Moisturizer SPF 30 50ml",
        "Rich Night Cream 50ml",
        "Eye Cream Anti-Fatigue 15ml",
        "Clay Face Mask Detox 75ml",
        "Sheet Mask Hydrating (5 pack)",
        "Lip Balm SPF 15 10ml",
        "Exfoliating Scrub 75ml",
    ],
    ("Beauty", "Fragrance"): [
        "Eau de Parfum Rose & Oud 50ml",
        "Eau de Toilette Fresh Citrus 100ml",
        "Body Mist Vanilla Blossom 200ml",
        "Body Mist Ocean Breeze 200ml",
        "Perfume Discovery Set (5x 10ml)",
        "Scented Candle Sandalwood 220g",
        "Room Diffuser Lavender 100ml",
    ],
    ("Beauty", "Body Care"): [
        "Body Lotion Shea Butter 250ml",
        "Body Scrub Coffee & Coconut 200g",
        "Shower Gel Refreshing Mint 500ml",
        "Bath Bomb Set (6 pack)",
        "Hand Cream Aloe Vera 75ml",
        "Deodorant Natural Roll-On 50ml",
        "Body Oil Argan & Jojoba 100ml",
        "Foot Cream Intensive 75ml",
    ],
    ("Beauty", "Bath & Body"): [
        "Luxury Bath Towel Set",
        "Bamboo Face Cloths (3 pack)",
        "Silk Pillowcase",
        "Bath Robe Cotton White",
        "Shower Cap Reusable",
        "Konjac Sponge Natural",
    ],
    ("Beauty", "Accessories"): [
        "Makeup Brush Set (12 piece)",
        "Jade Face Roller",
        "Gua Sha Rose Quartz",
        "Hair Claw Clips (4 pack)",
        "Cosmetics Bag Vegan Leather",
        "LED Makeup Mirror",
    ],
    ("Beauty", "Grooming"): [
        "Beard Oil Cedar & Lime 30ml",
        "Beard Balm 60ml",
        "Face Wash Men Charcoal 150ml",
        "Aftershave Balm 100ml",
        "Hair Pomade Matte 85g",
        "Nose & Ear Trimmer",
    ],
    ("Beauty", "Tools"): [
        "Hair Dryer Ionic 2200W",
        "Straightener Ceramic Plates",
        "Curling Wand 28mm",
        "Facial Steamer Nano Mist",
        "Derma Roller 0.5mm",
        "Electric Face Brush",
    ],
    ("Beauty", "Haircare"): [
        "Argan Oil Repair Shampoo 300ml",
        "Argan Oil Repair Conditioner 300ml",
        "Hair Mask Keratin 200ml",
        "Dry Shampoo Volume 200ml",
        "Scalp Scrub Sea Salt 200g",
        "Heat Protectant Spray 200ml",
        "Leave-In Conditioner 150ml",
    ],
    ("Wellness", "Vitamins"): [
        "Daily Multivitamin 60 tabs",
        "Vitamin D3 2500IU 180 tabs",
        "Vitamin C 1000mg 90 tabs",
        "Vitamin B Complex 90 tabs",
        "Iron & Folic Acid 90 tabs",
        "Zinc 15mg 90 tabs",
        "Magnesium Citrate 90 tabs",
    ],
    ("Wellness", "Supplements"): [
        "Omega-3 Fish Oil 90 softgels",
        "Collagen Peptides 300g",
        "Turmeric & Black Pepper 60 caps",
        "Ashwagandha KSM-66 60 caps",
        "Probiotics 30 Billion CFU 30 caps",
        "Apple Cider Vinegar Gummies 60",
        "Glucosamine & Chondroitin 120 tabs",
    ],
    ("Wellness", "Sleep"): [
        "Sleep Aid Melatonin 5mg 60 tabs",
        "Magnesium Glycinate Night 90 caps",
        "Pillow Spray Lavender 75ml",
        "Weighted Blanket 7kg",
        "Silk Sleep Mask",
        "Chamomile Night Tea 20 bags",
    ],
    ("Wellness", "Mindfulness"): [
        "Meditation Cushion Buckwheat",
        "Yoga Block Cork (2 pack)",
        "Gratitude Journal Hardcover",
        "Essential Oil Set (6x 10ml)",
        "Aromatherapy Diffuser 300ml",
        "Stress Ball Set (3 pack)",
        "Adult Colouring Book Mandalas",
        "Acupressure Mat & Pillow Set",
    ],
    ("Wellness", "Family Health"): [
        "Kids Multivitamin Gummies 60",
        "Baby Vitamin D Drops 30ml",
        "Prenatal Vitamins 90 tabs",
        "Kids Omega-3 Chewables 60",
        "Baby Skin Cream 100ml",
        "Stretch Mark Cream 150ml",
    ],
    ("Wellness", "Gifts"): [
        "Wellness Gift Box (5 items)",
        "Self-Care Starter Kit",
        "Fitness Starter Pack",
        "Spa Day Gift Set",
        "Protein Taster Box (8 sachets)",
    ],
    ("Wellness", "Lifestyle"): [
        "Reusable Water Bottle 500ml",
        "Beeswax Food Wraps (3 pack)",
        "Stainless Steel Lunchbox",
        "Bamboo Toothbrush Set (4 pack)",
        "Natural Deodorant Balm 60g",
        "Eco Tote Bag Canvas",
    ],
    ("Wellness", "Home Wellness"): [
        "Himalayan Salt Lamp",
        "Air Purifier HEPA Mini",
        "White Noise Machine",
        "Posture Corrector Adjustable",
        "Lumbar Support Cushion",
        "Standing Desk Converter",
        "Blue Light Glasses",
    ],
}

# ── Step 3: Load products and remap ──────────────────────────────────

products = pd.read_csv(TRIMMED / "products.csv")
print(f"Original: {len(products)} products across {products['category_english'].nunique()} categories")

# Map category → (vertical, subcategory)
def map_category(cat):
    if pd.isna(cat):
        return ("Wellness", "Lifestyle")  # default for nulls
    return CATEGORY_MAP.get(cat, ("Wellness", "Lifestyle"))

products["vertical"] = products["category_english"].apply(lambda c: map_category(c)[0])
products["subcategory"] = products["category_english"].apply(lambda c: map_category(c)[1])

# ── Step 4: Assign product names from pools ──────────────────────────

# For each product, pick a name from its (vertical, subcategory) pool
# Realistic variant suffixes by subcategory type
VARIANT_SUFFIXES = {
    # Fitness
    ("Fitness", "Equipment"):   ["Black", "Grey", "Blue", "Red", "Green", "Navy", "White", "Orange", "Purple", "Camo"],
    ("Fitness", "Tech"):        ["Black", "White", "Grey", "Navy", "Rose Gold", "Silver", "Midnight Blue", "Forest Green"],
    ("Fitness", "Accessories"):  ["Black", "Navy", "Grey", "Pink", "Blue", "Red", "White", "Teal", "Coral", "Lime"],
    ("Fitness", "Nutrition"):   ["Chocolate", "Vanilla", "Strawberry", "Peanut Butter", "Cookies & Cream", "Salted Caramel", "Berry", "Banana", "Mocha", "Unflavoured"],
    ("Fitness", "Drinks"):      ["Tropical", "Berry", "Citrus", "Grape", "Watermelon", "Mango", "Lemon Lime", "Peach"],
    # Beauty
    ("Beauty", "Skincare"):     ["30ml", "50ml", "75ml", "100ml", "Travel Size", "Duo Pack", "Value Size 200ml", "Mini 15ml"],
    ("Beauty", "Bath & Body"):  ["White", "Grey", "Blush Pink", "Sage Green", "Lavender", "Cream", "Charcoal", "Stone"],
    ("Beauty", "Tools"):        ["Black", "Rose Gold", "White", "Pink", "Gold", "Silver", "Matte Black", "Pearl"],
    ("Beauty", "Fragrance"):    ["Rose", "Vanilla", "Jasmine", "Citrus", "Sandalwood", "Lavender", "Oud", "Bergamot"],
    ("Beauty", "Accessories"):  ["Rose Gold", "Gold", "Silver", "Pink", "Black", "Marble", "Blush", "Clear"],
    ("Beauty", "Grooming"):     ["Sensitive", "Original", "Cool Mint", "Cedar", "Charcoal", "Unscented"],
    ("Beauty", "Body Care"):    ["Coconut", "Shea Butter", "Aloe Vera", "Argan", "Cocoa Butter", "Vitamin E", "Rose Hip", "Lavender"],
    # Wellness
    ("Wellness", "Home Wellness"):  ["White", "Natural Wood", "Black", "Grey", "Bamboo", "Oak", "Walnut", "Mint"],
    ("Wellness", "Lifestyle"):      ["Natural", "Sage Green", "Ocean Blue", "Charcoal", "Sand", "Coral", "Olive", "Oat"],
    ("Wellness", "Gifts"):          ["Classic", "Premium", "Deluxe", "Essentials", "Starter", "Signature", "Ultimate", "Discovery"],
    ("Wellness", "Mindfulness"):    ["Lavender", "Eucalyptus", "Sage", "Natural", "Navy", "Grey", "Charcoal", "Stone"],
    ("Wellness", "Family Health"):  ["Strawberry", "Orange", "Berry", "Unflavoured", "Grape", "Tropical", "Cherry", "Lemon"],
    ("Wellness", "Sleep"):          ["Lavender", "Chamomile", "Vanilla", "Unflavoured"],
}

# If a pool runs out, cycle through it with realistic suffixes
def assign_names(group):
    key = (group["vertical"].iloc[0], group["subcategory"].iloc[0])
    pool = PRODUCT_NAMES.get(key)
    if pool is None:
        vertical = key[0]
        for k, v in PRODUCT_NAMES.items():
            if k[0] == vertical:
                pool = v
                break
    if pool is None:
        pool = ["Wellness Product"]

    suffixes = VARIANT_SUFFIXES.get(key, ["Classic", "Original", "Standard", "Premium", "Lite", "Pro", "Plus", "Max"])

    n = len(group)
    names = []
    for i in range(n):
        base_name = pool[i % len(pool)]
        cycle = i // len(pool)
        suffix = suffixes[cycle % len(suffixes)]
        if cycle == 0:
            names.append(base_name)
        else:
            names.append(f"{base_name} - {suffix}")

    # Shuffle so same-named products aren't consecutive
    rng = np.random.RandomState(hash(key[0] + key[1]) % 2**31)
    rng.shuffle(names)
    return pd.Series(names, index=group.index)

products["product_name"] = products.groupby(
    ["vertical", "subcategory"], group_keys=False
).apply(assign_names)

# ── Step 5: Update prices to be realistic for the vertical ──────────

PRICE_RANGES = {
    "Fitness": (8.99, 59.99),
    "Beauty": (5.99, 49.99),
    "Wellness": (6.99, 39.99),
}

def realistic_price(row):
    lo, hi = PRICE_RANGES[row["vertical"]]
    # Use original price as a seed to keep some variation
    orig = row["price"] if "price" in row and not pd.isna(row.get("price")) else 20.0
    rng = np.random.RandomState(hash(row["product_id"]) % 2**31)
    return round(rng.uniform(lo, hi), 2)

products["price"] = products.apply(realistic_price, axis=1)

# ── Step 6: Add product descriptions ─────────────────────────────────

DESC_TEMPLATES = {
    "Fitness": "High-quality {name}. Perfect for supporting your fitness goals. {sub} range product designed for active lifestyles.",
    "Beauty": "Premium {name}. Part of our {sub} collection. Formulated with carefully selected ingredients for visible results.",
    "Wellness": "Natural {name}. From our {sub} range. Designed to support your overall wellbeing and healthy lifestyle.",
}

products["description"] = products.apply(
    lambda r: DESC_TEMPLATES[r["vertical"]].format(name=r["product_name"], sub=r["subcategory"]),
    axis=1
)

# ── Step 7: Clean up columns ─────────────────────────────────────────

# Drop old Olist-specific columns, keep useful ones
products_out = products[[
    "product_id", "product_name", "vertical", "subcategory",
    "price", "avg_rating", "description",
    "product_weight_g"
]].copy()

products_out.rename(columns={"product_weight_g": "weight_g"}, inplace=True)

# ── Save ─────────────────────────────────────────────────────────────
products_out.to_csv(TRIMMED / "products.csv", index=False)

print(f"\nRemapped to THG-style verticals:")
print(f"  Total products: {len(products_out)}")
print(f"\n  By vertical:")
for v, count in products_out["vertical"].value_counts().items():
    subs = products_out[products_out["vertical"] == v]["subcategory"].nunique()
    print(f"    {v}: {count} products across {subs} subcategories")

print(f"\n  Subcategory breakdown:")
for (v, s), count in products_out.groupby(["vertical", "subcategory"]).size().items():
    print(f"    {v} / {s}: {count}")

print(f"\n  Sample products:")
for v in ["Fitness", "Beauty", "Wellness"]:
    sample = products_out[products_out["vertical"] == v].iloc[0]
    print(f"    [{v}] {sample['product_name']} - GBP{sample['price']} ({sample['avg_rating']}/5)")
