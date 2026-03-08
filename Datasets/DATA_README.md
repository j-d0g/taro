# Data Layer Documentation

## Folder Structure

```
Datasets/
├── trimmed/                # Trimmed Olist + scraped product data
├── scraped_products.json   # 431 products scraped from lookfantastic.com
├── bitext_faq.csv          # Bitext FAQ dataset (26,872 Q&A pairs)
├── trim_dataset.py         # Generate trimmed/ from raw Olist data (seed=42)
├── remap_products.py       # Remap products to THG-style verticals
├── scrape_products.py      # Scrape product data from lookfantastic.com (Phase 1+2)
├── reprocess_phase2.py     # Re-process scraped pages with fixed parsing (Phase 2 only)
├── apply_scraped_v2.py     # Strategy B: round-robin remap products with scraped data
├── remap_categories.py     # Remap products to real 3-vertical, 9-subcategory structure
├── check_schema.py         # Schema + integrity checker (reusable)
└── DATA_README.md          # This file
```

> `Customer_behaviour/` (raw Olist, 121 MB) is gitignored. Download from Kaggle if you need to re-run trim_dataset.py.

## Two Data Layers

### 1. Trimmed Olist + Scraped Products (Knowledge Graph backbone)

Source: Brazilian E-Commerce (Kaggle), sampled to ~2.5K customers with full order chains.
Products remapped from 64 generic Olist categories into 3 verticals with 9 subcategories based on real product brands, then overlaid with 431 real products scraped from lookfantastic.com (round-robin per subcategory).

| File | Rows | Key columns |
|---|---|---|
| customers.csv | 2,526 | customer_id, customer_name, customer_city, customer_state |
| products.csv | 1,890 | product_id, product_name, vertical, subcategory, price, avg_rating, description, weight_g, image_url, product_url |
| orders.csv | 2,912 | order_id, customer_id, product_id, price |
| reviews.csv | 2,515 | review_id, order_id, review_score, review_comment_message, sentiment |

**Join keys:**
- `customer_id` links customers <-> orders
- `order_id` links orders <-> reviews
- `product_id` links orders <-> products

**Product verticals (3 verticals, 9 subcategories):**

| Vertical | Products | Subcategories |
|---|---|---|
| Skincare | 512 | Serums & Treatments, Cleansers & Moisturisers, Premium |
| Haircare | 658 | Styling Tools, Treatments, Accessories |
| Body & Fragrance | 720 | Bath & Body, Fragrance, Makeup |

**Brands per subcategory:**

| Subcategory | Brands |
|---|---|
| Skincare / Serums & Treatments | The Ordinary, Paula's Choice, The Inkey List, Drunk Elephant |
| Skincare / Cleansers & Moisturisers | CeraVe, La Roche-Posay, Clinique, Weleda |
| Skincare / Premium | Laneige, Tatcha, Elemis, Nuxe |
| Haircare / Styling Tools | ghd, Beauty Works, FOREO |
| Haircare / Treatments | Moroccanoil |
| Haircare / Accessories | Real Techniques, Tangle Teezer |
| Body & Fragrance / Bath & Body | Sol de Janeiro, Rituals, Molton Brown, This Works, NEOM |
| Body & Fragrance / Fragrance | Narciso Rodriguez, Calvin Klein, Estée Lauder |
| Body & Fragrance / Makeup | NARS, Bobbi Brown |

**Product data quality:**
- 355 unique product names (round-robin mapped from 431 scraped products)
- All products have real image URLs (`static.thcdn.com`) and product URLs (`lookfantastic.com`)
- Descriptions are complete sentences (truncated at sentence boundary within 300 chars)

### 2. Bitext FAQ (FAQ vector search + support ticket history)

Source: Bitext Customer Support LLM Dataset (HuggingFace), 26,872 Q&A pairs.

- 11 categories: ORDER, SHIPPING, DELIVERY, ACCOUNT, PAYMENT, REFUND, CANCEL, CONTACT, INVOICE, FEEDBACK, SUBSCRIPTION
- 27 intents: cancel_order, track_order, track_refund, change_shipping_address, etc.
- Columns: flags, instruction (question), category, intent, response (answer)

## SurrealDB Ingestion

```
Phase 1: Define schema (SCHEMAFULL tables + HNSW/BM25 indexes)
Phase 2: Ingest nodes (customer, product, order, review, faq)
Phase 3: Ingest edges (RELATE customer -> placed -> order, RELATE order -> contains -> product)
Phase 4: Generate + store embeddings (products, reviews, FAQs)
Phase 5: Compute also_bought edges (derived from co-purchase patterns)
```

### Also-bought edges (derived in seed script)

Two signals to detect products frequently bought together:

**Signal A — same customer across orders:** if the same customer bought X in one order and Y in another, they're co-purchased. The seed script (`schema/seed.py`) computes all pairwise co-purchase edges with weights.

```sql
-- Conceptual SurrealQL (actual computation done in Python seed script)
RELATE product:X -> also_bought -> product:Y SET weight = $count;
```

## Scripts

- `python trim_dataset.py` — Regenerate trimmed/ from raw Olist (needs Customer_behaviour/)
- `python remap_products.py` — Remap trimmed products to THG verticals (legacy, run after trim)
- `python remap_categories.py` — Remap to real 3-vertical, 9-subcategory structure (brand-based)
- `python scrape_products.py` — Scrape products from lookfantastic.com (Phase 1: crawl brand pages, Phase 2: parse product pages)
- `python reprocess_phase2.py` — Re-parse already-scraped product pages with fixed logic (no re-crawl)
- `python apply_scraped_v2.py` — Round-robin remap products.csv with scraped data (Strategy B)
- `python check_schema.py` — Verify schemas, sample data, and cross-dataset integrity
