"""
Overlay scraped product data (real names, descriptions, image URLs) onto products.csv.
- Scraped products: use real name as-is (no variant suffix)
- Original products: keep generated name with realistic suffix (e.g. "- Blue")
"""

import json
import pandas as pd
import urllib.request

JSON_PATH = "c:/Users/charlottegong/AppData/Roaming/Claude/local-agent-mode-sessions/a5d7585d-45c5-420d-b7df-2a8824fb7a93/7330d3c6-a9fe-44c5-8f27-6f792a0ea0aa/local_94420d5a-712b-47ec-a967-c728972bf90a/outputs/all_products_scraped.json"

REAL_DESCS = {
    "17696069": "Clinique Moisture Surge Hydration Skin Heroes Set with four full-sized skincare essentials for a visibly brighter and hydrated complexion.",
    "13713961": "Silky-smooth matte bronzer with buildable coverage for a natural sun-kissed look. Sweep across face or chisel cheekbones for a contoured effect.",
    "16090309": "Botanical hand wash infused with gentle cleansing agents and botanical extracts. Light cloud-like lather with mandarin rind, rosemary leaf, and cedar atlas.",
    "11512195": "Bestselling hybrid primer and moisturiser enriched with hyaluronic acid, shea butter and vitamins B5, C and E. Lightweight, fast-absorbing, vegan formula.",
    "12226515": "Bath and shower gel with pure essential oils of bergamot and jasmine. Soap-free formula gently cleanses without stripping moisture for a satin-smooth finish.",
    "10540680": "Award-winning intensive moisturizing cream for dry skin. Rich formula with wild pansy, calendula, rosemary and sunflower seed oil. Suitable for face and body.",
    "12183657": "Sport roll-on anti-perspirant enriched with Magnesia for 96-hour protection. Crisp woody fragrance with XXL roll-on ball for precise application.",
    "13735080": "Nourishing body butter with ceramides and cocoa butter for up to 100 hours of hydration. 97% natural origin ingredients, fast-absorbing, non-greasy.",
    "15229253": "Best-selling hair oil with French camellia and argan oil. Heat protection up to 230C, 2x shinier hair for 48 hours, 4 days anti-frizz protection.",
    "13043383": "Hair mask with patented metal detox technology. Removes copper deposits from water, delivers 87% less breakage and 2x shinier hair in single use.",
    "16718539": "Heated LED electric gua sha with heat, vibration and three light modes. Supports lymphatic drainage for visible facial sculpting and firming.",
    "15463353": "Essential oil discovery set with six trial-sized wellbeing blends. Scents for sleep, relaxation, energy and happiness with natural botanical ingredients.",
    "14242474": "Gel-to-foam facial cleanser with plant-derived formula. Gently removes impurities while supporting the moisture barrier for a clarified complexion.",
    "17726736": "2-in-1 straightener and dryer with HeatSense Ceramic Plates and rapid-dry technology. Minimizes heat damage with high-velocity airflow and interchangeable combs.",
    "15061739": "Skincare set with Hyaluronic Acid 2% + B5 for plumping hydration and Niacinamide 10% + Zinc 1% for skin brightness and smoothness.",
    "14234448": "Vanilla-scented lip sleeping mask delivering intense moisture overnight. Melts away dead skin cells while you sleep for soft, supple lips.",
    "11144730": "Lightweight cleansing balm that dissolves makeup, sunscreen and impurities. Transforms from balm to silky oil, rinsing clean without residue.",
    "10606208": "Strengthening shampoo and conditioner bundle for damaged hair with protein and strength complex for stronger, more resilient hair.",
    "17538813": "Starter retinol serum for improving skin texture and reducing visible signs of ageing. Gentle formula suitable for retinol beginners.",
    "13223099": "Daily rehab cream for damaged hair providing deep nourishment and repair. Lightweight formula strengthens and smooths without weighing hair down.",
    "16858532": "Exfoliating pore pads that refine pores and smooth skin texture. Removes excess sebum and dead skin cells for a clearer complexion.",
}

# Load scraped data
with open(JSON_PATH, "r") as f:
    scraped = json.load(f)

# Check which image URLs are alive
lookup = {}
for item in scraped:
    img = item["image_urls"][0]
    try:
        req = urllib.request.Request(img, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=5)
        if resp.getcode() != 200:
            continue
    except Exception:
        continue
    prod_id = img.split("/")[-1].split("-")[0]
    lookup[item["source_product_name"]] = {
        "matched_name": item["matched_product_name"],
        "image_url": img,
        "description": REAL_DESCS.get(prod_id),
    }

print(f"Working scraped products: {len(lookup)}")

# Load products
products = pd.read_csv("trimmed/products.csv")
products["image_url"] = None

n_name = n_desc = n_img = 0

for idx, row in products.iterrows():
    pname = row["product_name"]
    # Get base name by stripping " - Suffix"
    if " - " in pname:
        bn = pname[: pname.rfind(" - ")]
    else:
        bn = pname

    if bn in lookup:
        info = lookup[bn]
        # Scraped products: use real name, no suffix
        products.at[idx, "product_name"] = info["matched_name"]
        n_name += 1
        if info["description"]:
            products.at[idx, "description"] = info["description"]
            n_desc += 1
        products.at[idx, "image_url"] = info["image_url"]
        n_img += 1

products.to_csv("trimmed/products.csv", index=False)

print(f"Updated: {n_name} names, {n_desc} descriptions, {n_img} images")
print(f"Kept original (with suffix): {len(products) - n_name}")
print(f"Unique names: {products['product_name'].nunique()}")
print()
print("Sample scraped:")
for _, r in products[products["image_url"].notna()].head(5).iterrows():
    print(f"  {r['product_name']}  |  {r['vertical']}/{r['subcategory']}  |  GBP{r['price']}")
print()
print("Sample original:")
for _, r in products[products["image_url"].isna()].head(5).iterrows():
    print(f"  {r['product_name']}  |  {r['vertical']}/{r['subcategory']}  |  GBP{r['price']}")
