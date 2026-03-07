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

| File | Rows | Key columns |
|---|---|---|
| customers.csv | 5,153 | customer_id, customer_unique_id, customer_name, city, state |
| products.csv | 3,943 | product_id, product_name, vertical, subcategory, price, avg_rating, description |
| orders.csv | 5,849 | order_id, customer_id, product_id, order_status, price, freight_value |
| reviews.csv | 5,101 | review_id, order_id, review_score, comment, sentiment |
| payments.csv | 5,431 | order_id, payment_type, installments, value |

**Join keys:**
- `customer_id` links customers <-> orders
- `order_id` links orders <-> reviews, orders <-> payments
- `product_id` links orders <-> products

**Product verticals (3 verticals, 18 subcategories):**

| Vertical | Products | Subcategories |
|---|---|---|
| Fitness | 1,448 | Equipment, Tech, Accessories, Nutrition, Drinks |
| Beauty | 1,265 | Bath & Body, Tools, Skincare, Fragrance, Accessories, Grooming, Body Care |
| Wellness | 1,230 | Home Wellness, Lifestyle, Gifts, Mindfulness, Family Health, Sleep |

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
Phase 5: Compute co_purchased edges at DB level (see below)
```

### Co-purchased edges (computed in SurrealDB, not in CSV)

Two signals to detect products frequently bought together:

**Signal A — same order:** if product X and Y appear in the same order, they're co-purchased.
```sql
-- Find all product pairs within the same order
LET $pairs = SELECT order_id, product_id FROM orders GROUP BY order_id;
-- For each order with 2+ products, RELATE them:
RELATE product:X -> co_purchased -> product:Y SET weight += 1;
```

**Signal B — same customer across orders:** if the same customer bought X in one order and Y in another.
```sql
-- Find all products per customer
SELECT customer_id, array::distinct(product_id) AS products
FROM orders GROUP BY customer_id;
-- For each customer with 2+ distinct products, RELATE them:
RELATE product:X -> co_purchased -> product:Y SET weight += 1;
```

Only keep edges with weight >= 2 to filter noise.

## Scripts

- `python trim_dataset.py` — Regenerate trimmed/ from raw Olist (needs Customer_behaviour/)
- `python remap_products.py` — Remap trimmed products to THG verticals (run after trim)
- `python check_schema.py` — Verify schemas, sample data, and cross-dataset integrity
