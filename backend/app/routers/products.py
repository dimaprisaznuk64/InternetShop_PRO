from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.product import Product
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
)
from app.utils.dependencies import require_admin, require_manager
from app.utils.exceptions import NotFoundError, AlreadyExistsError
from app.cache import cache_get, cache_set, cache_delete, cache_delete_pattern

router = APIRouter(prefix="/api/products", tags=["products"])

PRODUCTS_CACHE_PREFIX = "products"
PRODUCTS_LIST_TTL = 120  # 2 min
PRODUCT_DETAIL_TTL = 300  # 5 min


def _products_list_cache_key(
    q, category_id, min_price, max_price, in_stock, brand, sort_by, sort_order, limit, offset
) -> str:
    parts = [
        f"q={q}", f"cat={category_id}", f"minp={min_price}", f"maxp={max_price}",
        f"stock={in_stock}", f"brand={brand}", f"sort={sort_by}", f"order={sort_order}",
        f"lim={limit}", f"off={offset}",
    ]
    return f"{PRODUCTS_CACHE_PREFIX}:list:{'|'.join(parts)}"


@router.get("/", response_model=ProductListResponse)
async def list_products(
    q: Optional[str] = Query(None, description="Search by name or SKU"),
    category_id: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock: Optional[bool] = Query(None, description="Only in stock"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="asc or desc"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    cache_key = _products_list_cache_key(
        q, category_id, min_price, max_price, in_stock, brand, sort_by, sort_order, limit, offset
    )
    cached = await cache_get(cache_key)
    if cached is not None:
        return ProductListResponse(**cached)

    stmt = select(Product).options(
        selectinload(Product.images),
        selectinload(Product.variants),
        selectinload(Product.category),
    )

    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Product.name.ilike(pattern),
                Product.sku.ilike(pattern),
                Product.description.ilike(pattern),
            )
        )

    if category_id:
        stmt = stmt.where(Product.category_id == category_id)

    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)

    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)

    if in_stock is not None:
        if in_stock:
            stmt = stmt.where(Product.stock > 0)
        else:
            stmt = stmt.where(Product.stock == 0)

    if brand:
        stmt = stmt.where(Product.brand.ilike(f"%{brand}%"))

    allowed_sort_fields = {
        "created_at",
        "updated_at",
        "name",
        "price",
        "stock",
        "brand",
    }
    sort_field = sort_by if sort_by in allowed_sort_fields else "created_at"
    sort_column = getattr(Product, sort_field)
    if sort_order == "asc":
        stmt = stmt.order_by(sort_column.asc())
    else:
        stmt = stmt.order_by(sort_column.desc())

    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    products = result.scalars().all()

    count_stmt = select(Product)
    if q:
        pattern = f"%{q}%"
        count_stmt = count_stmt.where(
            or_(
                Product.name.ilike(pattern),
                Product.sku.ilike(pattern),
                Product.description.ilike(pattern),
            )
        )
    if category_id:
        count_stmt = count_stmt.where(Product.category_id == category_id)
    if min_price is not None:
        count_stmt = count_stmt.where(Product.price >= min_price)
    if max_price is not None:
        count_stmt = count_stmt.where(Product.price <= max_price)
    if in_stock is not None:
        if in_stock:
            count_stmt = count_stmt.where(Product.stock > 0)
        else:
            count_stmt = count_stmt.where(Product.stock == 0)
    if brand:
        count_stmt = count_stmt.where(Product.brand.ilike(f"%{brand}%"))

    total_result = await db.execute(select(func.count()).select_from(count_stmt.subquery()))
    total = total_result.scalar()

    data = ProductListResponse(
        products=[ProductResponse.model_validate(p) for p in products],
        total=total,
    )
    await cache_set(cache_key, data.model_dump(), PRODUCTS_LIST_TTL)
    return data


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    cache_key = f"{PRODUCTS_CACHE_PREFIX}:detail:{product_id}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return ProductResponse(**cached)

    result = await db.execute(
        select(Product)
        .options(
            selectinload(Product.images),
            selectinload(Product.variants),
            selectinload(Product.category),
        )
        .where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundError("Product not found")

    data = ProductResponse.model_validate(product)
    await cache_set(cache_key, data.model_dump(), PRODUCT_DETAIL_TTL)
    return data


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager),
):
    existing = await db.execute(
        select(Product).where((Product.slug == data.slug) | (Product.sku == data.sku))
    )
    if existing.scalar_one_or_none():
        raise AlreadyExistsError("Product with this slug or SKU already exists")

    product = Product(**data.model_dump())
    db.add(product)
    await db.commit()

    result = await db.execute(
        select(Product)
        .options(
            selectinload(Product.images),
            selectinload(Product.variants),
            selectinload(Product.category),
        )
        .where(Product.id == product.id)
    )
    product = result.scalar_one()

    await cache_delete_pattern(f"{PRODUCTS_CACHE_PREFIX}:list:*")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundError("Product not found")

    existing = await db.execute(
        select(Product).where(
            (Product.slug == data.slug) | (Product.sku == data.sku),
            Product.id != product_id,
        )
    )
    if existing.scalar_one_or_none():
        raise AlreadyExistsError("Product with this slug or SKU already exists")

    for key, value in data.model_dump().items():
        setattr(product, key, value)

    await db.commit()

    result = await db.execute(
        select(Product)
        .options(
            selectinload(Product.images),
            selectinload(Product.variants),
            selectinload(Product.category),
        )
        .where(Product.id == product_id)
    )
    product = result.scalar_one()

    await cache_delete_pattern(f"{PRODUCTS_CACHE_PREFIX}:list:*")
    await cache_delete(f"{PRODUCTS_CACHE_PREFIX}:detail:{product_id}")
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundError("Product not found")

    await db.delete(product)
    await db.commit()

    await cache_delete_pattern(f"{PRODUCTS_CACHE_PREFIX}:list:*")
    await cache_delete(f"{PRODUCTS_CACHE_PREFIX}:detail:{product_id}")
