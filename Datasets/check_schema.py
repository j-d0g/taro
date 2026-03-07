"""
Check schema, sample data, and stats for all datasets.
Run anytime to verify data integrity before SurrealDB ingestion.
"""

import pandas as pd
from pathlib import Path

TRIMMED = Path(__file__).parent / "trimmed"
BITEXT = Path(__file__).parent / "bitext_faq.csv"


def check_dataset(name, df):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} cols")
    print(f"\nColumns & Types:")
    for col in df.columns:
        nulls = df[col].isnull().sum()
        nunique = df[col].nunique()
        null_str = f"  ({nulls} nulls)" if nulls > 0 else ""
        print(f"  {col:<40} {str(df[col].dtype):<10} {nunique} unique{null_str}")
    print(f"\nSample (first 2 rows):")
    print(df.head(2).to_string(index=False))
    print()


# ── Trimmed Olist datasets ──────────────────────────────────────────
datasets = {
    "TRIMMED: customers": pd.read_csv(TRIMMED / "customers.csv"),
    "TRIMMED: products": pd.read_csv(TRIMMED / "products.csv"),
    "TRIMMED: orders": pd.read_csv(TRIMMED / "orders.csv"),
    "TRIMMED: reviews": pd.read_csv(TRIMMED / "reviews.csv"),
    "TRIMMED: payments": pd.read_csv(TRIMMED / "payments.csv"),
}

# ── Bitext FAQ dataset ──────────────────────────────────────────────
datasets["BITEXT: faq"] = pd.read_csv(BITEXT)

for name, df in datasets.items():
    check_dataset(name, df)

# ── Cross-dataset integrity checks ──────────────────────────────────
print(f"\n{'='*60}")
print(f"  CROSS-DATASET INTEGRITY")
print(f"{'='*60}")

customers = datasets["TRIMMED: customers"]
orders = datasets["TRIMMED: orders"]
products = datasets["TRIMMED: products"]
reviews = datasets["TRIMMED: reviews"]

order_cust_ids = set(orders["customer_id"])
cust_ids = set(customers["customer_id"])
orphan_orders = order_cust_ids - cust_ids
print(f"\nOrders with missing customer:    {len(orphan_orders)}")

order_product_ids = set(orders["product_id"])
product_ids = set(products["product_id"])
orphan_products = order_product_ids - product_ids
print(f"Orders with missing product:     {len(orphan_products)}")

review_order_ids = set(reviews["order_id"])
order_ids = set(orders["order_id"])
orphan_reviews = review_order_ids - order_ids
print(f"Reviews with missing order:      {len(orphan_reviews)}")

print(f"\nAll checks passed!" if all(
    len(x) == 0 for x in [orphan_orders, orphan_products, orphan_reviews]
) else "\nSome integrity issues found - review above.")
