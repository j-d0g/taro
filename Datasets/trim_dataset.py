"""
Trim Olist dataset to ~5K customers with full order chains.
Merge orders + order_items into one table. Add synthetic names.
Outputs go to Datasets/trimmed/ folder.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import random

random.seed(42)
np.random.seed(42)

SRC = Path(__file__).parent / "Customer_behaviour"
OUT = Path(__file__).parent / "trimmed"
OUT.mkdir(exist_ok=True)

# ── Load original data ──────────────────────────────────────────────
customers = pd.read_csv(SRC / "olist_customers_dataset.csv")
orders = pd.read_csv(SRC / "olist_orders_dataset.csv")
order_items = pd.read_csv(SRC / "olist_order_items_dataset.csv")
products = pd.read_csv(SRC / "olist_products_dataset.csv")
reviews = pd.read_csv(SRC / "olist_order_reviews_dataset.csv")
payments = pd.read_csv(SRC / "olist_order_payments_dataset.csv")
cat_translation = pd.read_csv(SRC / "product_category_name_translation.csv")

print(f"Original: {len(customers)} customers, {len(orders)} orders, {len(products)} products")

# ── Step 1: Sample 5000 unique customers ─────────────────────────────
unique_customers = customers["customer_unique_id"].unique()
sampled_unique = np.random.choice(unique_customers, size=5000, replace=False)
customers_trim = customers[customers["customer_unique_id"].isin(sampled_unique)]

# ── Step 2: Filter orders for these customers ────────────────────────
orders_trim = orders[orders["customer_id"].isin(customers_trim["customer_id"])]

# ── Step 3: Filter order items, reviews, payments ────────────────────
order_ids = set(orders_trim["order_id"])
order_items_trim = order_items[order_items["order_id"].isin(order_ids)]
reviews_trim = reviews[reviews["order_id"].isin(order_ids)]
payments_trim = payments[payments["order_id"].isin(order_ids)]

# ── Step 4: Keep only products that appear in these orders ───────────
product_ids = set(order_items_trim["product_id"])
products_trim = products[products["product_id"].isin(product_ids)]

# ── Step 5: Add English category names to products ───────────────────
products_trim = products_trim.merge(cat_translation, on="product_category_name", how="left")
products_trim["category_english"] = products_trim["product_category_name_english"].fillna(
    products_trim["product_category_name"]
)
products_trim.drop(columns=["product_category_name_english"], inplace=True)

# ── Step 6: Generate synthetic product names ─────────────────────────
ADJECTIVES = [
    "Premium", "Classic", "Elite", "Essential", "Pro", "Ultra", "Smart",
    "Compact", "Deluxe", "Advanced", "Basic", "Modern", "Eco", "Slim",
    "Power", "Flex", "Prime", "Nova", "Apex", "Swift", "Bold", "Vivid",
    "Pure", "Max", "Core", "Zen", "Edge", "Pixel", "Turbo", "Stellar"
]

def make_product_name(row):
    adj = ADJECTIVES[hash(row["product_id"]) % len(ADJECTIVES)]
    cat = str(row["category_english"]).replace("_", " ").title()
    short_id = row["product_id"][:6].upper()
    return f"{adj} {cat} #{short_id}"

products_trim["product_name"] = products_trim.apply(make_product_name, axis=1)

# ── Step 7: Generate synthetic customer names ────────────────────────
FIRST_NAMES = [
    "Emma", "Liam", "Olivia", "Noah", "Ava", "Lucas", "Sophia", "Mason",
    "Isabella", "Ethan", "Mia", "James", "Charlotte", "Ben", "Amelia",
    "Alex", "Harper", "Daniel", "Ella", "Matthew", "Lily", "Jack", "Grace",
    "Henry", "Chloe", "Owen", "Zoe", "Samuel", "Nora", "Ryan", "Aria",
    "Leo", "Luna", "David", "Layla", "Carlos", "Ana", "Pedro", "Julia",
    "Rafael", "Maria", "Gabriel", "Beatriz", "Thiago", "Larissa", "Felipe",
    "Camila", "Bruno", "Fernanda", "Diego", "Valentina", "Marco", "Sofia",
    "Luis", "Isabela", "Andre", "Leticia", "Gustavo", "Mariana", "Eduardo"
]

LAST_NAMES = [
    "Silva", "Santos", "Oliveira", "Costa", "Pereira", "Lima", "Souza",
    "Almeida", "Ferreira", "Ribeiro", "Carvalho", "Gomes", "Martins",
    "Rocha", "Araujo", "Barbosa", "Mendes", "Nascimento", "Moreira",
    "Cardoso", "Nunes", "Melo", "Correia", "Pinto", "Lopes", "Vieira",
    "Monteiro", "Freitas", "Dias", "Castro", "Teixeira", "Campos",
    "Reis", "Andrade", "Duarte", "Moura", "Ramos", "Cunha", "Batista",
    "Fonseca", "Marques", "Tavares", "Borges", "Azevedo", "Machado"
]

unique_ids = customers_trim["customer_unique_id"].unique()
name_map = {}
for uid in unique_ids:
    fn = FIRST_NAMES[hash(uid) % len(FIRST_NAMES)]
    ln = LAST_NAMES[hash(uid + "_ln") % len(LAST_NAMES)]
    name_map[uid] = f"{fn} {ln}"

customers_trim = customers_trim.copy()
customers_trim["customer_name"] = customers_trim["customer_unique_id"].map(name_map)

# ── Step 8: Compute average rating per product ──────────────────────
review_products = (
    reviews_trim[["order_id", "review_score"]]
    .merge(order_items_trim[["order_id", "product_id"]], on="order_id")
)
avg_ratings = review_products.groupby("product_id")["review_score"].mean().round(2)
products_trim = products_trim.copy()
products_trim["avg_rating"] = products_trim["product_id"].map(avg_ratings)

# ── Step 9: Add simple sentiment to reviews ──────────────────────────
def simple_sentiment(score):
    if score >= 4:
        return "positive"
    elif score == 3:
        return "neutral"
    else:
        return "negative"

reviews_trim = reviews_trim.copy()
reviews_trim["sentiment"] = reviews_trim["review_score"].apply(simple_sentiment)

# ── Step 10: Merge orders + order_items ──────────────────────────────
orders_merged = orders_trim[["order_id", "customer_id"]].merge(
    order_items_trim[["order_id", "product_id", "price"]],
    on="order_id"
)

# ── Step 11: Filter reviews to only orders that survived the merge ──
merged_order_ids = set(orders_merged["order_id"])
reviews_trim = reviews_trim[reviews_trim["order_id"].isin(merged_order_ids)]

# ── Step 12: Slim down columns ───────────────────────────────────────
customers_out = customers_trim[["customer_id", "customer_name", "customer_city", "customer_state"]]
reviews_out = reviews_trim[["review_id", "order_id", "review_score", "review_comment_message", "sentiment"]]
payments_out = payments_trim[["order_id", "payment_type", "payment_installments", "payment_value"]]

# ── Save trimmed datasets ───────────────────────────────────────────
customers_out.to_csv(OUT / "customers.csv", index=False)
orders_merged.to_csv(OUT / "orders.csv", index=False)
products_trim.to_csv(OUT / "products.csv", index=False)
reviews_out.to_csv(OUT / "reviews.csv", index=False)
payments_out.to_csv(OUT / "payments.csv", index=False)

# Remove old files that are no longer needed
for old_file in ["order_items.csv", "sellers.csv", "co_purchased_with.csv"]:
    old_path = OUT / old_file
    if old_path.exists():
        old_path.unlink()
        print(f"  Removed old file: {old_file}")

print(f"\nTrimmed dataset saved to {OUT}/")
print(f"  Customers:      {len(customers_trim)}")
print(f"  Orders:         {len(orders_merged)} (merged orders + items)")
print(f"  Products:       {len(products_trim)}")
print(f"  Reviews:        {len(reviews_trim)}")
print(f"  Payments:       {len(payments_trim)}")
print(f"\nSample customer: {customers_out[['customer_name','customer_city','customer_state']].iloc[0].to_dict()}")
print(f"Sample product:  {products_trim[['product_name','category_english','avg_rating']].iloc[0].to_dict()}")
