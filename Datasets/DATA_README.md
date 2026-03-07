# Data Layer Documentation

## Folder Structure

```
Datasets/
├── trimmed/                # Trimmed Olist (5K customers, THG-style verticals)
├── bitext_faq.csv          # Bitext FAQ dataset (26,872 Q&A pairs)
├── trim_dataset.py         # Generate trimmed/ from raw Olist data (seed=42)
├── remap_products.py       # Remap products to THG-style verticals
├── check_schema.py         # Schema + integrity checker (reusable)
└── DATA_README.md          # This file
```

> `Customer_behaviour/` (raw Olist, 121 MB) is gitignored. Download from Kaggle if you need to re-run trim_dataset.py.

## Two Data Layers

### 1. Trimmed Olist (Knowledge Graph backbone)

Source: Brazilian E-Commerce (Kaggle), sampled to 5K customers with full order chains.
Products remapped from 64 generic Olist categories into 3 THG-style verticals.

| File | Rows | Purpose |
|---|---|---|
| customers.csv | 5,153 | Synthetic names (e.g. "Ava Machado") |
| products.csv | 3,943 | THG-style names, 3 verticals, 18 subcategories |
| orders.csv | 5,153 | Full timestamps, status |
| order_items.csv | 5,849 | Links orders to products + sellers, with price |
| reviews.csv | 5,134 | Sentiment derived from score |
| payments.csv | 5,431 | Payment type, installments, value |
| sellers.csv | 1,246 | Seller location data |
| co_purchased_with.csv | 770 | Pre-computed product-to-product edges |

**Product verticals (3 verticals, 18 subcategories):**

| Vertical | Products | Subcategories |
|---|---|---|
| Fitness | 1,448 | Equipment, Tech, Accessories, Nutrition, Drinks |
| Beauty | 1,265 | Bath & Body, Tools, Skincare, Fragrance, Accessories, Grooming, Body Care |
| Wellness | 1,230 | Home Wellness, Lifestyle, Gifts, Mindfulness, Family Health, Sleep |

**Product columns:** product_id, product_name, vertical, subcategory, price, avg_rating, description, weight_g

**Co-purchase signals** (two sources):
- Signal A: Products in the same order
- Signal B: Products bought by the same customer across different orders

### 2. Bitext FAQ (FAQ vector search + support ticket history)

Source: Bitext Customer Support LLM Dataset (HuggingFace), 26,872 Q&A pairs.

- 11 categories: ORDER, SHIPPING, BILLING, ACCOUNT, etc.
- 27 intents: cancel_order, track_refund, change_shipping_address, etc.
- Dual purpose:
  - **FAQ nodes** — question/answer pairs for vector search
  - **Support ticket nodes** — grouped by intent/category for resolution memory
- Columns: flags, instruction (question), category, intent, response (answer)

## SurrealDB Ingestion Order

```
Phase 1: Define schema (SCHEMAFULL tables + indexes)
Phase 2: Ingest nodes (customer, product, seller, order, review, faq)
Phase 3: Ingest edges (placed, contains, reviewed, sold_by, co_purchased_with)
Phase 4: Generate + store embeddings (products, reviews, FAQs), define HNSW + BM25 indexes
Phase 5: Resolution table starts empty — populated by agent's reflect-persist loop
```

## Scripts

- `python trim_dataset.py` — Regenerate trimmed/ from raw Olist (needs Customer_behaviour/)
- `python remap_products.py` — Remap trimmed products to THG verticals (run after trim)
- `python check_schema.py` — Verify schemas, sample data, and cross-dataset integrity
