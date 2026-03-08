"""
Remap all products from fake verticals/subcategories to real, product-appropriate
categories using 3 verticals and 9 subcategories.

Maps brands (extracted from product URLs) to correct categories:

Skincare (3 subcategories):
  - Serums & Treatments: The Ordinary, Paula's Choice, The Inkey List, Drunk Elephant
  - Cleansers & Moisturisers: CeraVe, La Roche-Posay, Clinique, Weleda
  - Premium: Laneige, Tatcha, Elemis, Nuxe

Haircare (3 subcategories):
  - Styling Tools: ghd, Beauty Works, FOREO
  - Treatments: Moroccanoil
  - Accessories: Real Techniques, Tangle Teezer

Body & Fragrance (3 subcategories):
  - Bath & Body: Sol de Janeiro, Rituals, Molton Brown, This Works, NEOM
  - Fragrance: Narciso Rodriguez, Calvin Klein, Estée Lauder
  - Makeup: NARS, Bobbi Brown

Usage: python Datasets/remap_categories.py
"""

import json
import re
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent / "trimmed"
SCRAPED_PATH = Path(__file__).parent / "scraped_products.json"

# Brand slug (from product URL) -> (vertical, subcategory)
BRAND_MAP = {
    # Skincare / Serums & Treatments
    "the-ordinary": ("Skincare", "Serums & Treatments"),
    "paula-s-choice": ("Skincare", "Serums & Treatments"),
    "the-inkey-list": ("Skincare", "Serums & Treatments"),
    "drunk-elephant": ("Skincare", "Serums & Treatments"),
    # Skincare / Cleansers & Moisturisers
    "cerave": ("Skincare", "Cleansers & Moisturisers"),
    "la-roche-posay": ("Skincare", "Cleansers & Moisturisers"),
    "clinique": ("Skincare", "Cleansers & Moisturisers"),
    "weleda": ("Skincare", "Cleansers & Moisturisers"),
    # Skincare / Premium
    "laneige": ("Skincare", "Premium"),
    "tatcha": ("Skincare", "Premium"),
    "elemis": ("Skincare", "Premium"),
    "nuxe": ("Skincare", "Premium"),
    # Haircare / Styling Tools
    "ghd": ("Haircare", "Styling Tools"),
    "beauty-works": ("Haircare", "Styling Tools"),
    "foreo": ("Haircare", "Styling Tools"),
    # Haircare / Treatments
    "moroccanoil": ("Haircare", "Treatments"),
    # Haircare / Accessories
    "real-techniques": ("Haircare", "Accessories"),
    "tangle-teezer": ("Haircare", "Accessories"),
    # Body & Fragrance / Bath & Body
    "sol-de-janeiro": ("Body & Fragrance", "Bath & Body"),
    "rituals": ("Body & Fragrance", "Bath & Body"),
    "molton-brown": ("Body & Fragrance", "Bath & Body"),
    "this-works": ("Body & Fragrance", "Bath & Body"),
    "neom": ("Body & Fragrance", "Bath & Body"),
    # Body & Fragrance / Fragrance
    "narciso-rodriguez": ("Body & Fragrance", "Fragrance"),
    "calvin-klein": ("Body & Fragrance", "Fragrance"),
    "estee-lauder": ("Body & Fragrance", "Fragrance"),
    # Body & Fragrance / Makeup
    "nars": ("Body & Fragrance", "Makeup"),
    "bobbi-brown": ("Body & Fragrance", "Makeup"),
}


def extract_brand_slug(product_url: str) -> str | None:
    """Extract brand slug from a lookfantastic.com product URL."""
    path = product_url.split("/p/")[-1] if "/p/" in product_url else ""
    if not path:
        return None

    # First try: brand slug at start of path (most common)
    for brand_slug in sorted(BRAND_MAP.keys(), key=len, reverse=True):
        if path.startswith(brand_slug):
            return brand_slug

    # Second try: brand slug anywhere in the path (handles "exclusive-brand-..." etc)
    for brand_slug in sorted(BRAND_MAP.keys(), key=len, reverse=True):
        if brand_slug in path:
            return brand_slug

    # Third try: match by product name keywords for edge cases
    if "detangler" in path or "tangle" in path:
        return "tangle-teezer"
    if "ritual-of-" in path or "rituals" in path:
        return "rituals"
    # Bundles / generic pages — map by reasonable category
    if "mothers-day" in path or "bundle" in path:
        return "tangle-teezer"  # Tangle Teezer bundles

    return None


# Fallback: map by product name when URL doesn't contain brand
NAME_FALLBACKS = {
    "morphe": ("Body & Fragrance", "Makeup"),
    "kiehl": ("Skincare", "Premium"),
    "laura mercier": ("Body & Fragrance", "Makeup"),
    "color wow": ("Haircare", "Treatments"),
    "caudalie": ("Skincare", "Serums & Treatments"),
    "lancaster": ("Skincare", "Premium"),
    "la mer": ("Skincare", "Premium"),
}


def fallback_by_name(product_name: str) -> tuple[str, str] | None:
    """Match product name to category when URL-based matching fails."""
    name_lower = product_name.lower() if isinstance(product_name, str) else ""
    for keyword, category in NAME_FALLBACKS.items():
        if keyword in name_lower:
            return category
    return None


def remap_scraped():
    """Remap scraped_products.json assigned_subcategory values."""
    with open(SCRAPED_PATH, encoding="utf-8") as f:
        products = json.load(f)

    unmapped = []
    counts = {}
    for p in products:
        brand = extract_brand_slug(p["product_url"])
        if brand and brand in BRAND_MAP:
            vertical, subcat = BRAND_MAP[brand]
        else:
            fb = fallback_by_name(p.get("product_name", ""))
            if fb:
                vertical, subcat = fb
            else:
                unmapped.append(p["product_url"])
                continue
        p["assigned_subcategory"] = f"{vertical}/{subcat}"
        key = f"{vertical}/{subcat}"
        counts[key] = counts.get(key, 0) + 1

    if unmapped:
        print(f"WARNING: {len(unmapped)} products could not be mapped:")
        for u in unmapped[:5]:
            print(f"  {u}")

    with open(SCRAPED_PATH, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    print(f"Remapped {len(products) - len(unmapped)}/{len(products)} scraped products")
    print("\nScraped products per new category:")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")

    return counts


def remap_products_csv():
    """Remap products.csv vertical and subcategory columns."""
    products = pd.read_csv(DATA_DIR / "products.csv")

    unmapped = 0
    counts = {}
    for idx, row in products.iterrows():
        url = row.get("product_url", "")
        if not isinstance(url, str) or not url:
            unmapped += 1
            continue
        brand = extract_brand_slug(url)
        if brand and brand in BRAND_MAP:
            vertical, subcat = BRAND_MAP[brand]
        else:
            fb = fallback_by_name(row.get("product_name", ""))
            if fb:
                vertical, subcat = fb
            else:
                unmapped += 1
                continue
        products.at[idx, "vertical"] = vertical
        products.at[idx, "subcategory"] = subcat
        key = f"{vertical}/{subcat}"
        counts[key] = counts.get(key, 0) + 1

    if unmapped:
        print(f"\nWARNING: {unmapped} products in CSV could not be mapped")

    products.to_csv(DATA_DIR / "products.csv", index=False)

    print(f"\nRemapped {len(products) - unmapped}/{len(products)} CSV products")
    print("\nCSV products per new category:")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")

    # Summary stats
    print(f"\nVertical distribution:")
    for v in sorted(products["vertical"].unique()):
        n = len(products[products["vertical"] == v])
        print(f"  {v}: {n}")

    print(f"\nSubcategory distribution:")
    for s in sorted(products["subcategory"].unique()):
        n = len(products[products["subcategory"] == s])
        v = products[products["subcategory"] == s].iloc[0]["vertical"]
        print(f"  {v}/{s}: {n}")


def main():
    print("=" * 60)
    print("REMAPPING CATEGORIES")
    print("=" * 60)

    print("\n--- Scraped Products (scraped_products.json) ---")
    remap_scraped()

    print("\n--- Products CSV (trimmed/products.csv) ---")
    remap_products_csv()

    print("\nDone! Categories remapped to 3 verticals, 9 subcategories.")


if __name__ == "__main__":
    main()
