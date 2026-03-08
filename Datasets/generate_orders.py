"""
Generate additional synthetic orders for existing customers to create
a richer purchase graph with also_bought edges.

Distribution: ~60% of customers end up with 2-3 total products,
some with 4-5, a few with 6+. Uses a clipped normal distribution.

Each new order gets a new order_id + a synthetic review.

Usage: python Datasets/generate_orders.py
"""

import random
import uuid
import pandas as pd
import numpy as np
from pathlib import Path

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

DATA_DIR = Path(__file__).parent / "trimmed"

# ── Load existing data ──────────────────────────────────────
customers = pd.read_csv(DATA_DIR / "customers.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
orders = pd.read_csv(DATA_DIR / "orders.csv")
reviews = pd.read_csv(DATA_DIR / "reviews.csv")

print(f"Before: {len(orders)} orders, {len(reviews)} reviews")
print(f"Customers: {len(customers)}, Products: {len(products)}")

# Current products per customer
cust_products = orders.groupby("customer_id")["product_id"].apply(set).to_dict()
cust_current_count = {c: len(ps) for c, ps in cust_products.items()}

# All product IDs grouped by subcategory for semi-realistic selection
products_by_subcat = products.groupby("subcategory")["product_id"].apply(list).to_dict()
all_product_ids = products["product_id"].tolist()
all_subcats = list(products_by_subcat.keys())

# Product prices for order price
product_prices = products.set_index("product_id")["price"].to_dict()

# ── Target distribution ─────────────────────────────────────
# Normal distribution centered at 2.5, std=1.2, clipped to [1, 8]
# This gives ~60% in 2-3 range

target_counts = np.random.normal(loc=2.5, scale=1.2, size=len(customers))
target_counts = np.clip(np.round(target_counts), 1, 8).astype(int)

# Stats
from collections import Counter
dist = Counter(target_counts)
print(f"\nTarget product count distribution:")
for k in sorted(dist):
    pct = dist[k] / len(customers) * 100
    print(f"  {k} products: {dist[k]} customers ({pct:.1f}%)")
in_2_3 = (dist.get(2, 0) + dist.get(3, 0)) / len(customers) * 100
print(f"  2-3 products: {in_2_3:.1f}%")

# ── Generate new orders ─────────────────────────────────────
# Synthetic review templates by score
REVIEW_TEMPLATES = {
    5: [
        "Absolutely love this product! Will definitely repurchase.",
        "Exceeded my expectations. Great quality for the price.",
        "Perfect addition to my routine. Highly recommend.",
        "Best purchase I've made in a while. Five stars!",
        "Amazing results after just a few uses. So impressed.",
        "Lovely product, arrived quickly and well packaged.",
        "Works exactly as described. Very happy with this.",
        "Outstanding quality. Already recommended to friends.",
        "This has become a staple in my collection. Love it!",
        "Incredible value. The quality is truly impressive.",
    ],
    4: [
        "Really good product, just wish the packaging was better.",
        "Great results overall, slightly overpriced though.",
        "Very pleased with this purchase. Minor improvements possible.",
        "Good quality product that does what it promises.",
        "Solid product, would buy again. Delivery was quick too.",
        "Nice product, not quite perfect but very close.",
        "Happy with the results. Took a few days to notice a difference.",
        "Good value for money. Would recommend to others.",
    ],
    3: [
        "Decent product but nothing special. Average performance.",
        "It's okay, does the job but I've tried better.",
        "Mixed feelings. Some aspects are good, others not so much.",
        "Reasonable for the price. Not blown away though.",
        "Average product. Works fine but wouldn't rush to repurchase.",
        "Not bad, not great. Somewhere in the middle.",
    ],
    2: [
        "Disappointed with the results. Expected more for the price.",
        "Not great quality. Wouldn't recommend to others.",
        "Below expectations. The product didn't work well for me.",
        "Poor value for money. Probably won't buy again.",
    ],
    1: [
        "Very disappointing. Product didn't work as described.",
        "Would not recommend. Complete waste of money.",
        "Terrible experience. Product arrived damaged and performs poorly.",
    ],
}

# Score distribution: weighted towards positive (matching existing data)
SCORE_WEIGHTS = [0.05, 0.05, 0.10, 0.22, 0.58]  # scores 1-5
SENTIMENTS = {1: "negative", 2: "negative", 3: "neutral", 4: "positive", 5: "positive"}

new_orders = []
new_reviews = []

for i, cust_id in enumerate(customers["customer_id"]):
    current_count = cust_current_count.get(cust_id, 0)
    target = target_counts[i]
    needed = target - current_count

    if needed <= 0:
        continue

    owned_products = cust_products.get(cust_id, set()).copy()

    for _ in range(needed):
        # Pick a product not already owned by this customer
        # 70% chance: same vertical as something they own, 30% random
        chosen_pid = None

        if owned_products and random.random() < 0.7:
            # Pick from a related subcategory
            owned_subcats = products[products["product_id"].isin(owned_products)]["subcategory"].unique()
            # Pick from same vertical's subcategories
            owned_verticals = products[products["product_id"].isin(owned_products)]["vertical"].unique()
            related_subcats = products[products["vertical"].isin(owned_verticals)]["subcategory"].unique()

            candidates = []
            for sc in related_subcats:
                candidates.extend(products_by_subcat.get(sc, []))
            candidates = [p for p in candidates if p not in owned_products]

            if candidates:
                chosen_pid = random.choice(candidates)

        if not chosen_pid:
            # Random product not already owned
            candidates = [p for p in all_product_ids if p not in owned_products]
            if not candidates:
                break
            chosen_pid = random.choice(candidates)

        owned_products.add(chosen_pid)

        # Create order
        order_id = uuid.uuid4().hex[:32]
        price = product_prices.get(chosen_pid, 25.0)

        new_orders.append({
            "order_id": order_id,
            "customer_id": cust_id,
            "product_id": chosen_pid,
            "price": price,
        })

        # Create review
        review_id = uuid.uuid4().hex[:32]
        score = random.choices([1, 2, 3, 4, 5], weights=SCORE_WEIGHTS, k=1)[0]
        comment = random.choice(REVIEW_TEMPLATES[score])
        sentiment = SENTIMENTS[score]

        new_reviews.append({
            "review_id": review_id,
            "order_id": order_id,
            "review_score": score,
            "review_comment_message": comment,
            "sentiment": sentiment,
        })

print(f"\nGenerated {len(new_orders)} new orders + {len(new_reviews)} new reviews")

# ── Merge and save ──────────────────────────────────────────
new_orders_df = pd.DataFrame(new_orders)
new_reviews_df = pd.DataFrame(new_reviews)

orders_combined = pd.concat([orders, new_orders_df], ignore_index=True)
reviews_combined = pd.concat([reviews, new_reviews_df], ignore_index=True)

orders_combined.to_csv(DATA_DIR / "orders.csv", index=False)
reviews_combined.to_csv(DATA_DIR / "reviews.csv", index=False)

print(f"\nAfter: {len(orders_combined)} orders, {len(reviews_combined)} reviews")

# ── Verify distribution ────────────────────────────────────
final_cust_products = orders_combined.groupby("customer_id")["product_id"].nunique()
final_dist = Counter(final_cust_products.values)
print(f"\nFinal products-per-customer distribution:")
for k in sorted(final_dist):
    pct = final_dist[k] / len(customers) * 100
    print(f"  {k} products: {final_dist[k]} customers ({pct:.1f}%)")
in_2_3 = (final_dist.get(2, 0) + final_dist.get(3, 0)) / len(customers) * 100
print(f"  2-3 products: {in_2_3:.1f}%")

# Also-bought potential
multi_product_custs = final_cust_products[final_cust_products > 1].count()
print(f"\nCustomers with 2+ products (also_bought contributors): {multi_product_custs}")
