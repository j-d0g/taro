"""
Strategy B: Diversify product mapping.
For each of the 1,890 product rows, assign a real scraped product from the
matching subcategory (round-robin). Graph structure stays identical.

Usage:
    python Datasets/apply_scraped_v2.py
"""

import json
import pandas as pd
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent / "trimmed"
SCRAPED_PATH = Path(__file__).parent / "scraped_products.json"

# Load scraped products
with open(SCRAPED_PATH, encoding="utf-8") as f:
    scraped = json.load(f)

# Build subcategory -> [products] lookup
# The assigned_subcategory is "Vertical/Subcategory" format
subcat_products = defaultdict(list)
for p in scraped:
    key = p["assigned_subcategory"]
    if "/" in key:
        _, subcat = key.split("/", 1)
    else:
        subcat = key
    subcat_products[subcat].append(p)

print("Scraped products per subcategory:")
for k, v in sorted(subcat_products.items()):
    print(f"  {k}: {len(v)}")

# Load products
products = pd.read_csv(DATA_DIR / "products.csv")
print(f"\nProducts to remap: {len(products)}")
print(f"Unique product names before: {products['product_name'].nunique()}")

# Round-robin assign scraped products per subcategory
counters = defaultdict(int)
updated = 0
missing_subcats = set()

for idx, row in products.iterrows():
    subcat = row["subcategory"]
    pool = subcat_products.get(subcat)
    if not pool:
        missing_subcats.add(subcat)
        continue

    # Pick next product in round-robin
    sp = pool[counters[subcat] % len(pool)]
    counters[subcat] += 1

    products.at[idx, "product_name"] = sp["product_name"]
    products.at[idx, "description"] = sp["description"] or ""
    products.at[idx, "image_url"] = sp["image_url"]
    products.at[idx, "product_url"] = sp["product_url"]
    # Keep original price and avg_rating (from Olist data — adds variety)
    # But use real price if available and original is unrealistic
    if sp.get("price_gbp") and sp["price_gbp"] > 0:
        products.at[idx, "price"] = sp["price_gbp"]
    if sp.get("avg_rating") and sp["avg_rating"] > 0:
        products.at[idx, "avg_rating"] = sp["avg_rating"]
    updated += 1

if missing_subcats:
    print(f"\nWARNING: No scraped products for subcategories: {missing_subcats}")

# Save
products.to_csv(DATA_DIR / "products.csv", index=False)

print(f"\nRemapped {updated}/{len(products)} products")
print(f"Unique product names after: {products['product_name'].nunique()}")
print(f"Unique image URLs: {products['image_url'].nunique()}")
print(f"Unique product URLs: {products['product_url'].nunique()}")

# Show sample per subcategory
print("\nSample per subcategory:")
for subcat in sorted(products["subcategory"].unique()):
    sample = products[products["subcategory"] == subcat].iloc[0]
    print(f"  {sample['vertical']}/{subcat}: {sample['product_name'][:50]} £{sample['price']:.2f}")
