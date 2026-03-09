"""Product endpoints: GET /products, GET /products/{product_id}."""

from typing import Optional

from fastapi import APIRouter

import db
from helpers import str_id


router = APIRouter()


@router.get("/products")
async def list_products(
    vertical: Optional[str] = None,
    search: Optional[str] = None,
    brand: Optional[str] = None,
    limit: int = 2000,
    offset: int = 0,
):
    """List products with optional filters and pagination."""
    async with db.get_db() as conn:
        where_clauses = []
        params: dict = {}

        if vertical:
            where_clauses.append("vertical = $vertical")
            params["vertical"] = vertical
        if search:
            where_clauses.append("(name ~ $search OR description ~ $search OR subcategory ~ $search)")
            params["search"] = search
        if brand:
            where_clauses.append("brand = $brand")
            params["brand"] = brand

        where = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        surql = (
            "SELECT id, name, vertical, subcategory, price, avg_rating, brand, "
            f"image_url, description FROM product{where} ORDER BY name "
            f"LIMIT {min(limit, 2000)} START {offset}"
        )
        rows = await conn.query(surql, params)

        # Deduplicate by product name (CSV has ~1890 rows but only ~355 unique)
        seen: dict[str, bool] = {}
        deduped: list[dict] = []
        for row in rows:
            name = row.get("name", "")
            if name not in seen:
                seen[name] = True
                row["id"] = str_id(row.get("id", ""))
                deduped.append(row)
        return deduped


@router.get("/products/{product_id}")
async def get_product(product_id: str):
    """Get product detail with also_bought graph edges and reviews."""
    async with db.get_db() as conn:
        # Product record
        rows = await conn.query(f"SELECT * FROM product:`{product_id}`")
        if not rows:
            return {"error": f"Product not found: {product_id}"}
        product = rows[0]
        product["id"] = str_id(product.get("id", ""))

        # Also bought (product -> also_bought -> product)
        ab_rows = await conn.query(
            f"SELECT ->also_bought->product.{{id, name, price, avg_rating, image_url, subcategory}} "
            f"AS also_bought FROM product:`{product_id}`"
        )
        also_bought = ab_rows[0].get("also_bought", []) if ab_rows else []
        for ab in also_bought:
            ab["id"] = str_id(ab.get("id", ""))
        product["also_bought"] = also_bought

        # Reviews via order -> contains -> product, order -> has_review -> review
        rev_rows = await conn.query(
            "SELECT id, score, comment, sentiment FROM review "
            f"WHERE <-has_review<-order->contains->product CONTAINS product:`{product_id}` "
            "ORDER BY score DESC LIMIT 10"
        )
        for r in rev_rows:
            r["review_id"] = str_id(r.pop("id", ""))
        product["reviews"] = rev_rows

        return product
