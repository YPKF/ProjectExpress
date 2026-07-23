"""
Product Search API

Provides full-text search with filtering, sorting, and cursor-based pagination.
Uses PostgreSQL full-text search with ts_rank for relevance scoring.
"""

from typing import Optional, List
from enum import Enum

from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, text, desc, and_, or_
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.product import Product, Category
from ..auth.jwt import get_current_user

router = APIRouter(prefix="/search", tags=["search"])


class SortOption(str, Enum):
    RELEVANCE = "relevance"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    NEWEST = "newest"
    POPULARITY = "popularity"


class SearchFilters(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    category_id: Optional[int] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    in_stock_only: bool = True
    sort: SortOption = SortOption.RELEVANCE
    cursor: Optional[str] = None
    limit: int = Field(20, ge=1, le=100)


class ProductResult(BaseModel):
    id: int
    name: str
    slug: str
    price: float
    category_name: str
    image_url: str
    rating: float
    review_count: int
    in_stock: bool
    highlighted_name: Optional[str] = None
    highlighted_description: Optional[str] = None


class SearchResponse(BaseModel):
    results: List[ProductResult]
    total_count: int
    next_cursor: Optional[str]
    page_time_ms: float


def build_search_query(db: Session, filters: SearchFilters):
    """Build the base SQLAlchemy query with full-text search and filters."""
    ts_query = func.plainto_tsquery("english", filters.query)
    ts_vector = func.to_tsvector("english", Product.name + " " + Product.description)

    # Full-text search with ranking
    query = (
        db.query(
            Product,
            func.ts_rank(ts_vector, ts_query).label("rank"),
            func.ts_headline(
                "english",
                Product.name,
                ts_query,
                "StartSel=<mark>, StopSel=</mark>, MaxWords=60, MinWords=20",
            ).label("highlighted_name"),
            func.ts_headline(
                "english",
                Product.description,
                ts_query,
                "StartSel=<mark>, StopSel=</mark>, MaxWords=60, MinWords=20",
            ).label("highlighted_description"),
        )
        .filter(ts_vector.match(filters.query))
    )

    # Category filter
    if filters.category_id is not None:
        query = query.filter(Product.category_id == filters.category_id)

    # Price range filter
    if filters.min_price is not None:
        query = query.filter(Product.price >= filters.min_price)
    if filters.max_price is not None:
        query = query.filter(Product.price <= filters.max_price)

    # Stock filter
    if filters.in_stock_only:
        query = query.filter(Product.stock_quantity > 0)

    return query


def apply_sorting(query, sort: SortOption):
    """Apply sort order to the query."""
    sort_map = {
        SortOption.RELEVANCE: desc("rank"),
        SortOption.PRICE_ASC: Product.price.asc(),
        SortOption.PRICE_DESC: Product.price.desc(),
        SortOption.NEWEST: Product.created_at.desc(),
        SortOption.POPULARITY: Product.sales_count.desc(),
    }
    return query.order_by(sort_map[sort])


def decode_cursor(cursor: str) -> tuple:
    """Decode a base64 cursor into (sort_value, id) for keyset pagination."""
    import base64
    import json
    try:
        decoded = base64.urlsafe_b64decode(cursor + "==")
        data = json.loads(decoded)
        return data["sort_value"], data["id"]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid pagination cursor")


def encode_cursor(sort_value, product_id: int) -> str:
    """Encode sort_value and id into a base64 cursor."""
    import base64
    import json
    data = json.dumps({"sort_value": sort_value, "id": product_id})
    return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")


@router.get("/", response_model=SearchResponse)
def search_products(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    in_stock: bool = Query(True, description="Only show in-stock products"),
    sort: SortOption = Query(SortOption.RELEVANCE, description="Sort order"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db),
):
    """
    Search products with full-text search, filtering, and pagination.

    Uses PostgreSQL full-text search with ts_rank for relevance scoring.
    Supports cursor-based pagination for consistent results.
    """
    import time
    start = time.monotonic()

    filters = SearchFilters(
        query=q,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock,
        sort=sort,
        cursor=cursor,
        limit=limit,
    )

    query = build_search_query(db, filters)
    query = apply_sorting(query, sort)

    # Keyset pagination
    if cursor:
        sort_val, last_id = decode_cursor(cursor)
        if sort in (SortOption.PRICE_ASC, SortOption.PRICE_DESC):
            op = Product.price > sort_val if sort == SortOption.PRICE_ASC else Product.price < sort_val
            query = query.filter(or_(op, and_(Product.price == sort_val, Product.id > last_id)))
        elif sort == SortOption.RELEVANCE:
            query = query.filter(
                or_(
                    text("rank < :rank"),
                    and_(text("rank = :rank"), Product.id > last_id),
                )
            ).params(rank=sort_val)
        elif sort == SortOption.NEWEST:
            query = query.filter(
                or_(
                    Product.created_at < sort_val,
                    and_(Product.created_at == sort_val, Product.id > last_id),
                )
            )

    # Fetch one extra to detect if there are more results
    rows = query.limit(limit + 1).all()
    has_next = len(rows) > limit
    rows = rows[:limit]

    results = []
    last_sort_value = None
    for product, rank, h_name, h_desc in rows:
        results.append(
            ProductResult(
                id=product.id,
                name=product.name,
                slug=product.slug,
                price=product.price,
                category_name=product.category.name if product.category else "",
                image_url=product.image_url,
                rating=product.avg_rating or 0.0,
                review_count=product.review_count or 0,
                in_stock=product.stock_quantity > 0,
                highlighted_name=h_name,
                highlighted_description=h_desc,
            )
        )
        last_sort_value = rank if sort == SortOption.RELEVANCE else getattr(product, sort.value.split("_")[0], rank)

    next_cursor = encode_cursor(last_sort_value, rows[-1].id) if has_next and rows else None

    # Get total count (cached in production)
    total = build_search_query(db, filters).count()

    elapsed_ms = round((time.monotonic() - start) * 1000, 1)

    return SearchResponse(
        results=results,
        total_count=total,
        next_cursor=next_cursor,
        page_time_ms=elapsed_ms,
    )
