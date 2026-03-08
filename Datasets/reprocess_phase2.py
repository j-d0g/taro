"""
Re-process Phase 2 only: re-fetch the 431 product pages from scraped_products.json
and re-parse with fixed description truncation + image URL extraction.
Does NOT re-crawl category/brand pages.

Usage:
    python Datasets/reprocess_phase2.py
"""

import json
import re
import time
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
SCRAPED_PATH = Path(__file__).parent / "scraped_products.json"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-GB,en;q=0.9",
    })
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  FAIL {url}: {e}")
        return ""


def extract_jsonld(html: str) -> dict | None:
    matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    for m in matches:
        try:
            data = json.loads(m)
            if data.get("@type") == "Product":
                return data
        except json.JSONDecodeError:
            continue
    return None


def parse_product(data: dict, url: str) -> dict:
    # Price
    price = None
    if data.get("offers"):
        offers = data["offers"] if isinstance(data["offers"], list) else [data["offers"]]
        prices = [float(o["price"]) for o in offers if o.get("price")]
        price = min(prices) if prices else None

    # Rating
    rating = None
    if data.get("aggregateRating"):
        rating = round(float(data["aggregateRating"].get("ratingValue", 0)), 1)

    # Description — clean HTML, truncate at sentence boundary within 300 chars
    desc = data.get("description", "")
    desc = re.sub(r'&nbsp;', ' ', desc)
    desc = re.sub(r'<[^>]+>', '', desc)
    desc = re.sub(r'\s+', ' ', desc).strip()
    if len(desc) > 300:
        cut = desc[:300].rfind(".")
        if cut > 100:
            desc = desc[:cut + 1]
        else:
            desc = desc[:300]

    # Image — extract static.thcdn.com URL from thgimages wrapper
    image = data.get("image", "")
    thcdn_match = re.search(r'(https://static\.thcdn\.com/productimg/original/[^&"]+)', image)
    if thcdn_match:
        image = thcdn_match.group(1)
    elif "thgimages.com" in image:
        url_match = re.search(r'url=(https?://[^&"]+)', image)
        if url_match:
            image = url_match.group(1)

    return {
        "product_name": data.get("name", ""),
        "product_url": url,
        "image_url": image,
        "price_gbp": price,
        "avg_rating": rating,
        "description": desc,
        "sku": data.get("sku", ""),
    }


def main():
    # Load existing scraped data to get URLs + subcategory assignments
    with open(SCRAPED_PATH, encoding="utf-8") as f:
        old_data = json.load(f)

    print(f"Loaded {len(old_data)} existing products to re-process")

    # Build list of (url, subcategory) pairs
    to_process = [(p["product_url"], p["assigned_subcategory"]) for p in old_data]

    products = []
    failed = 0
    for i, (url, subcat) in enumerate(to_process):
        if i % 50 == 0:
            print(f"  Progress: {i}/{len(to_process)} ({len(products)} ok, {failed} failed)")
        html = fetch(url)
        if not html:
            failed += 1
            continue
        data = extract_jsonld(html)
        if not data:
            failed += 1
            continue
        product = parse_product(data, url)
        product["assigned_subcategory"] = subcat
        products.append(product)
        time.sleep(0.5)

    print(f"\nDone! Re-processed {len(products)}/{len(to_process)} ({failed} failed)")

    # Validate fixes
    bad_img = sum(1 for p in products if "thgimages.com" in p["image_url"] or not p["image_url"])
    trunc = sum(1 for p in products if p["description"].endswith("..."))
    print(f"Bad image URLs: {bad_img}")
    print(f"Descriptions ending with '...': {trunc}")

    # Sample
    if products:
        s = products[0]
        print(f"\nSample:")
        print(f"  Name: {s['product_name']}")
        print(f"  Image: {s['image_url'][:80]}...")
        print(f"  Desc: {s['description'][:100]}...")

    # Save
    with open(SCRAPED_PATH, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(products)} products to {SCRAPED_PATH}")


if __name__ == "__main__":
    main()
