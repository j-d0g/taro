"""
Fix dataset consistency issues:
1. Deduplicate review_ids (assign new UUIDs to duplicates)
2. Generate payments for new orders (3,950 missing)
3. Remove orphaned payments (referencing deleted orders)
4. Generate reviews for orders without reviews (23 missing)
5. Fix 1 product with missing avg_rating

Usage: python Datasets/fix_consistency.py
"""

import random
import uuid
import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

DATA_DIR = Path(__file__).parent / "trimmed"

# ── Load ────────────────────────────────────────────────────
customers = pd.read_csv(DATA_DIR / "customers.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
orders = pd.read_csv(DATA_DIR / "orders.csv")
reviews = pd.read_csv(DATA_DIR / "reviews.csv")
payments = pd.read_csv(DATA_DIR / "payments.csv")

print("=== BEFORE ===")
print(f"customers: {len(customers)}, products: {len(products)}")
print(f"orders: {len(orders)}, reviews: {len(reviews)}, payments: {len(payments)}")

# ── 1. Fix duplicate review_ids ─────────────────────────────
dupes = reviews[reviews["review_id"].duplicated(keep="first")]
print(f"\n[1] Fixing {len(dupes)} duplicate review_ids...")
for idx in dupes.index:
    reviews.at[idx, "review_id"] = uuid.uuid4().hex[:32]
assert reviews["review_id"].duplicated().sum() == 0, "Still have duplicates!"

# ── 2. Fix missing avg_rating ───────────────────────────────
null_ratings = products["avg_rating"].isnull()
print(f"[2] Fixing {null_ratings.sum()} products with missing avg_rating...")
products.loc[null_ratings, "avg_rating"] = 4.5  # reasonable default

# ── 3. Remove orphaned payments ─────────────────────────────
valid_order_ids = set(orders["order_id"])
orphaned = ~payments["order_id"].isin(valid_order_ids)
print(f"[3] Removing {orphaned.sum()} orphaned payments...")
payments = payments[~orphaned]

# ── 4. Generate payments for orders without payments ────────
orders_with_payment = set(payments["order_id"])
orders_needing_payment = orders[~orders["order_id"].isin(orders_with_payment)]
print(f"[4] Generating {len(orders_needing_payment)} missing payments...")

PAYMENT_TYPES = ["credit_card", "debit_card", "voucher", "boleto"]
PAYMENT_WEIGHTS = [0.70, 0.15, 0.10, 0.05]

new_payments = []
for _, row in orders_needing_payment.iterrows():
    ptype = random.choices(PAYMENT_TYPES, weights=PAYMENT_WEIGHTS, k=1)[0]
    installments = 1
    if ptype == "credit_card":
        installments = random.choices([1, 2, 3, 4, 6, 8, 10], weights=[0.4, 0.15, 0.15, 0.1, 0.1, 0.05, 0.05], k=1)[0]

    new_payments.append({
        "order_id": row["order_id"],
        "payment_type": ptype,
        "payment_installments": installments,
        "payment_value": round(row["price"], 2) if pd.notna(row["price"]) else 25.0,
    })

payments = pd.concat([payments, pd.DataFrame(new_payments)], ignore_index=True)

# ── 5. Generate reviews for orders without reviews ──────────
orders_with_review = set(reviews["order_id"])
orders_needing_review = orders[~orders["order_id"].isin(orders_with_review)]
print(f"[5] Generating {len(orders_needing_review)} missing reviews...")

REVIEW_TEMPLATES = {
    5: [
        "Absolutely love this product! Will definitely repurchase.",
        "Exceeded my expectations. Great quality for the price.",
        "Perfect addition to my routine. Highly recommend.",
        "Best purchase I've made in a while. Five stars!",
        "Amazing results after just a few uses. So impressed.",
    ],
    4: [
        "Really good product, just wish the packaging was better.",
        "Great results overall, slightly overpriced though.",
        "Very pleased with this purchase. Minor improvements possible.",
        "Good quality product that does what it promises.",
    ],
    3: [
        "Decent product but nothing special. Average performance.",
        "It's okay, does the job but I've tried better.",
        "Mixed feelings. Some aspects are good, others not so much.",
    ],
    2: [
        "Disappointed with the results. Expected more for the price.",
        "Not great quality. Wouldn't recommend to others.",
    ],
    1: [
        "Very disappointing. Product didn't work as described.",
        "Would not recommend. Complete waste of money.",
    ],
}
SCORE_WEIGHTS = [0.05, 0.05, 0.10, 0.22, 0.58]
SENTIMENTS = {1: "negative", 2: "negative", 3: "neutral", 4: "positive", 5: "positive"}

new_reviews = []
for _, row in orders_needing_review.iterrows():
    score = random.choices([1, 2, 3, 4, 5], weights=SCORE_WEIGHTS, k=1)[0]
    new_reviews.append({
        "review_id": uuid.uuid4().hex[:32],
        "order_id": row["order_id"],
        "review_score": score,
        "review_comment_message": random.choice(REVIEW_TEMPLATES[score]),
        "sentiment": SENTIMENTS[score],
    })

reviews = pd.concat([reviews, pd.DataFrame(new_reviews)], ignore_index=True)

# ── Save ────────────────────────────────────────────────────
products.to_csv(DATA_DIR / "products.csv", index=False)
orders.to_csv(DATA_DIR / "orders.csv", index=False)
reviews.to_csv(DATA_DIR / "reviews.csv", index=False)
payments.to_csv(DATA_DIR / "payments.csv", index=False)

print(f"\n=== AFTER ===")
print(f"customers: {len(customers)}, products: {len(products)}")
print(f"orders: {len(orders)}, reviews: {len(reviews)}, payments: {len(payments)}")

# ── Final verification ──────────────────────────────────────
print("\n=== VERIFICATION ===")
checks = [
    ("Orders->customers", set(orders["customer_id"]) - set(customers["customer_id"])),
    ("Orders->products", set(orders["product_id"]) - set(products["product_id"])),
    ("Reviews->orders", set(reviews["order_id"]) - set(orders["order_id"])),
    ("Payments->orders", set(payments["order_id"]) - set(orders["order_id"])),
    ("Orders w/o review", set(orders["order_id"]) - set(reviews["order_id"])),
    ("Orders w/o payment", set(orders["order_id"]) - set(payments["order_id"])),
    ("Customers w/o order", set(customers["customer_id"]) - set(orders["customer_id"])),
    ("Products w/o order", set(products["product_id"]) - set(orders["product_id"])),
]

all_ok = True
for label, orphans in checks:
    status = "OK" if len(orphans) == 0 else f"FAIL ({len(orphans)})"
    print(f"  {label}: {status}")
    if len(orphans) > 0:
        all_ok = False

print(f"  Duplicate review_ids: {'OK' if reviews['review_id'].duplicated().sum() == 0 else 'FAIL'}")
print(f"  Null avg_ratings: {'OK' if products['avg_rating'].isnull().sum() == 0 else 'FAIL'}")

if all_ok:
    print("\nAll checks passed!")
else:
    print("\nSome checks failed!")
