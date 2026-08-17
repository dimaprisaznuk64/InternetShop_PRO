from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/", response_model=ProductListResponse)
async def list_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product))
    products = result.scalars().all()
    return ProductListResponse(
        products=[ProductResponse.model_validate(p) for p in products],
        total=len(products),
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundError("Product not found")
    return product


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
    await db.refresh(product)
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
    await db.refresh(product)
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
