# Data Layer Documentation

## Folder Structure

```
Datasets/
├── Customer_behaviour/     # Original Olist (99K records, untouched)
├── trimmed/                # Trimmed Olist (5K customers, ready for SurrealDB)
├── bitext_faq.csv          # Bitext FAQ dataset (26,872 Q&A pairs)
├── trim_dataset.py         # Script to regenerate trimmed/ from originals
├── check_schema.py         # Schema + integrity checker (reusable)
├── FAQ_vector_search.py    # Script to download bitext FAQ from HuggingFace
└── DATA_README.md          # This file
```

## Two Data Layers

### 1. Trimmed Olist (Knowledge Graph backbone)

Source: Brazilian E-Commerce (Kaggle), sampled to 5K customers with full order chains.

| File | Rows | Purpose |
|---|---|---|
| customers.csv | 5,153 | Synthetic names added (e.g. "Ava Machado") |
| products.csv | 3,943 | Synthetic names + English categories + avg_rating |
| orders.csv | 5,153 | Full timestamps, status |
| order_items.csv | 5,849 | Links orders to products + sellers, with price |
| reviews.csv | 5,134 | Sentiment derived from score (positive/neutral/negative) |
| payments.csv | 5,431 | Payment type, installments, value |
| sellers.csv | 1,246 | Seller location data |
| co_purchased_with.csv | 770 | Pre-computed product-to-product edges |

**Co-purchase signals** (two sources):
- Signal A: Products in the same order
- Signal B: Products bought by the same customer across different orders

**Nulls to watch:**
- 67 products missing category (will show as NaN)
- 29 products missing avg_rating (no reviews)
- 3,025 reviews missing comment text (score-only reviews)

### 2. Bitext FAQ (FAQ vector search + support ticket history)

Source: Bitext Customer Support LLM Dataset (HuggingFace), 26,872 Q&A pairs.

- 11 categories: ORDER, SHIPPING, BILLING, ACCOUNT, etc.
- 27 intents: cancel_order, track_refund, change_shipping_address, etc.
- Dual purpose from one dataset:
  - **FAQ nodes** — question/answer pairs with embeddings for `search_faq()` vector search
  - **Support ticket nodes** — customer queries grouped by intent and category for `get_resolution_memory()`
- Columns: flags, instruction (question), category, intent, response (answer)

## SurrealDB Ingestion Order

```
Phase 1: Define schema (SCHEMAFULL tables + relation edges + vector index)
Phase 2: Ingest nodes (customer → product → seller → order → review → faq → support_ticket)
Phase 3: Ingest edges (placed, contains, reviewed, sold_by, co_purchased_with)
Phase 4: Generate + store FAQ embeddings, define vector index
Phase 5: resolution table starts empty — populated by agent's reflect-persist loop
```

## Scripts

- `python trim_dataset.py` — Regenerate trimmed/ from originals (deterministic, seed=42)
- `python check_schema.py` — Verify all schemas, sample data, and cross-dataset integrity
- `python FAQ_vector_search.py` — Re-download bitext FAQ from HuggingFace
