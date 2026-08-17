from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.product import ProductVariant
from app.schemas.product_variant import (
    ProductVariantCreate,
    ProductVariantUpdate,
    ProductVariantResponse,
    ProductVariantListResponse,
)
from app.utils.dependencies import require_manager
from app.utils.exceptions import NotFoundError, AlreadyExistsError

router = APIRouter(prefix="/api/products/{product_id}/variants", tags=["product variants"])


@router.get("/", response_model=ProductVariantListResponse)
async def list_variants(
    product_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProductVariant).where(ProductVariant.product_id == product_id)
    )
    variants = result.scalars().all()
    return ProductVariantListResponse(
        variants=[ProductVariantResponse.model_validate(v) for v in variants],
        total=len(variants),
    )


@router.get("/{variant_id}", response_model=ProductVariantResponse)
async def get_variant(
    product_id: str,
    variant_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProductVariant).where(
            ProductVariant.id == variant_id,
            ProductVariant.product_id == product_id,
        )
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise NotFoundError("Variant not found")
    return variant


@router.post("/", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
async def create_variant(
    product_id: str,
    data: ProductVariantCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager),
):
    existing = await db.execute(
        select(ProductVariant).where(ProductVariant.sku == data.sku)
    )
    if existing.scalar_one_or_none():
        raise AlreadyExistsError("Variant with this SKU already exists")

    variant = ProductVariant(product_id=product_id, **data.model_dump())
    db.add(variant)
    await db.commit()
    await db.refresh(variant)
    return variant


@router.put("/{variant_id}", response_model=ProductVariantResponse)
async def update_variant(
    product_id: str,
    variant_id: str,
    data: ProductVariantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager),
):
    result = await db.execute(
        select(ProductVariant).where(
            ProductVariant.id == variant_id,
            ProductVariant.product_id == product_id,
        )
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise NotFoundError("Variant not found")

    existing = await db.execute(
        select(ProductVariant).where(
            ProductVariant.sku == data.sku,
            ProductVariant.id != variant_id,
        )
    )
    if existing.scalar_one_or_none():
        raise AlreadyExistsError("Variant with this SKU already exists")

    for key, value in data.model_dump().items():
        setattr(variant, key, value)

    await db.commit()
    await db.refresh(variant)
    return variant


@router.delete("/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant(
    product_id: str,
    variant_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager),
):
    result = await db.execute(
        select(ProductVariant).where(
            ProductVariant.id == variant_id,
            ProductVariant.product_id == product_id,
        )
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise NotFoundError("Variant not found")

    await db.delete(variant)
    await db.commit()
