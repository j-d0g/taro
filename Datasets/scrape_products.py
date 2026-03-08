"""
Scrape real product data from lookfantastic.com using JSON-LD structured data.
Extracts: name, description, image, price, rating, product_url per product.

Strategy: Hit category listing pages to discover product URLs, then scrape
each product page for JSON-LD data. Category pages are SSR so only a few
products appear, but we supplement with brand pages and search.

Usage:
    python Datasets/scrape_products.py

Output:
    Datasets/scraped_products.json
"""

import json
import re
import time
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Category and brand URLs to crawl for product links
# Each maps to our subcategory for assignment
# Brand pages work reliably (category pages 404). Map brands -> our subcategories.
CRAWL_URLS = {
    # Beauty / Skincare
    "Beauty/Skincare": [
        "https://www.lookfantastic.com/c/brands/the-ordinary/",
        "https://www.lookfantastic.com/c/brands/cerave/",
        "https://www.lookfantastic.com/c/brands/la-roche-posay/",
        "https://www.lookfantastic.com/c/brands/paula-s-choice/",
    ],
    # Beauty / Tools
    "Beauty/Tools": [
        "https://www.lookfantastic.com/c/brands/ghd/",
        "https://www.lookfantastic.com/c/brands/beauty-works/",
    ],
    # Beauty / Bath & Body
    "Beauty/Bath & Body": [
        "https://www.lookfantastic.com/c/brands/sol-de-janeiro/",
        "https://www.lookfantastic.com/c/brands/rituals/",
    ],
    # Beauty / Fragrance
    "Beauty/Fragrance": [
        "https://www.lookfantastic.com/c/brands/narciso-rodriguez/",
        "https://www.lookfantastic.com/c/brands/calvin-klein/",
    ],
    # Beauty / Body Care
    "Beauty/Body Care": [
        "https://www.lookfantastic.com/c/brands/elemis/",
        "https://www.lookfantastic.com/c/brands/nuxe/",
    ],
    # Beauty / Accessories
    "Beauty/Accessories": [
        "https://www.lookfantastic.com/c/brands/real-techniques/",
        "https://www.lookfantastic.com/c/brands/tangle-teezer/",
    ],
    # Fitness / Equipment + Tech + Nutrition + Accessories + Drinks
    "Fitness/Equipment": [
        "https://www.lookfantastic.com/c/brands/clinique/",
    ],
    "Fitness/Tech": [
        "https://www.lookfantastic.com/c/brands/foreo/",
    ],
    "Fitness/Nutrition": [
        "https://www.lookfantastic.com/c/brands/the-inkey-list/",
    ],
    "Fitness/Accessories": [
        "https://www.lookfantastic.com/c/brands/nars/",
    ],
    "Fitness/Drinks": [
        "https://www.lookfantastic.com/c/brands/drunk-elephant/",
    ],
    # Wellness
    "Wellness/Home Wellness": [
        "https://www.lookfantastic.com/c/brands/laneige/",
        "https://www.lookfantastic.com/c/brands/tatcha/",
    ],
    "Wellness/Family Health": [
        "https://www.lookfantastic.com/c/brands/weleda/",
        "https://www.lookfantastic.com/c/brands/bobbi-brown/",
    ],
    "Wellness/Mindfulness": [
        "https://www.lookfantastic.com/c/brands/neom/",
    ],
    "Wellness/Sleep": [
        "https://www.lookfantastic.com/c/brands/this-works/",
    ],
    "Wellness/Gifts": [
        "https://www.lookfantastic.com/c/brands/molton-brown/",
    ],
    "Wellness/Lifestyle": [
        "https://www.lookfantastic.com/c/brands/estee-lauder/",
        "https://www.lookfantastic.com/c/brands/moroccanoil/",
    ],
}


def fetch(url: str) -> str:
    """Fetch a URL with browser-like headers."""
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


def extract_product_urls(html: str) -> list[str]:
    """Pull /p/slug/id/ links from category page HTML."""
    results = set()
    # Full absolute URLs
    for m in re.findall(r'https://www\.lookfantastic\.com/p/[a-z0-9-]+/[0-9]+/', html):
        results.add(m)
    # Relative paths — ensure /p/ prefix
    for slug, pid in re.findall(r'/p/([a-z0-9][a-z0-9-]+)/([0-9]+)/', html):
        results.add(f"https://www.lookfantastic.com/p/{slug}/{pid}/")
    # Href patterns without /p/ (brand pages sometimes use short paths)
    for slug, pid in re.findall(r'href="/?([a-z0-9][a-z0-9-]+)/([0-9]{7,})/"', html):
        if slug not in ("c", "p", "search"):
            results.add(f"https://www.lookfantastic.com/p/{slug}/{pid}/")
    return list(results)


def extract_jsonld(html: str) -> dict | None:
    """Extract Product JSON-LD from a product page."""
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
    """Parse JSON-LD Product into our schema."""
    # Get best price
    price = None
    if data.get("offers"):
        prices = [float(o["price"]) for o in data["offers"] if o.get("price")]
        price = min(prices) if prices else None

    # Get rating
    rating = None
    if data.get("aggregateRating"):
        rating = round(float(data["aggregateRating"].get("ratingValue", 0)), 1)

    # Clean description (remove HTML entities)
    desc = data.get("description", "")
    desc = re.sub(r'&nbsp;', ' ', desc)
    desc = re.sub(r'<[^>]+>', '', desc)
    desc = re.sub(r'\s+', ' ', desc).strip()
    # Truncate at sentence boundary if very long
    if len(desc) > 300:
        # Find last period before 300 chars
        cut = desc[:300].rfind(".")
        if cut > 100:
            desc = desc[:cut + 1]
        else:
            desc = desc[:300]

    # Get image — extract the static.thcdn.com URL from the thgimages wrapper
    image = data.get("image", "")
    # Pattern: https://main.thgimages.com/?url=https://static.thcdn.com/...&format=webp&...
    thcdn_match = re.search(r'(https://static\.thcdn\.com/productimg/original/[^&]+)', image)
    if thcdn_match:
        image = thcdn_match.group(1)
    elif "thgimages.com" in image:
        # Try to extract any static URL
        url_match = re.search(r'url=(https?://[^&]+)', image)
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
    all_product_urls: dict[str, str] = {}  # url -> subcategory_key

    print("Phase 1: Crawling category pages for product URLs...")
    seen_categories = set()
    for subcat_key, urls in CRAWL_URLS.items():
        for url in urls:
            if url in seen_categories:
                continue
            seen_categories.add(url)
            print(f"  Crawling {url}")
            html = fetch(url)
            if not html:
                continue
            found = extract_product_urls(html)
            for purl in found:
                if purl not in all_product_urls:
                    all_product_urls[purl] = subcat_key
            print(f"    Found {len(found)} product links (total unique: {len(all_product_urls)})")
            time.sleep(1)

    print(f"\nPhase 1 complete: {len(all_product_urls)} unique product URLs")

    print(f"\nPhase 2: Scraping {len(all_product_urls)} product pages for JSON-LD...")
    products = []
    for i, (url, subcat) in enumerate(all_product_urls.items()):
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(all_product_urls)} ({len(products)} scraped)")
        html = fetch(url)
        if not html:
            continue
        data = extract_jsonld(html)
        if not data:
            continue
        product = parse_product(data, url)
        product["assigned_subcategory"] = subcat
        products.append(product)
        time.sleep(0.5)  # Be polite

    print(f"\nDone! Scraped {len(products)} products")

    # Save
    out_path = Path(__file__).parent / "scraped_products.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"Saved to {out_path}")

    # Stats
    by_subcat = {}
    for p in products:
        key = p["assigned_subcategory"]
        by_subcat[key] = by_subcat.get(key, 0) + 1
    print("\nProducts per subcategory:")
    for k, v in sorted(by_subcat.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
