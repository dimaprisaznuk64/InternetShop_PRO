from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.product import ProductImage
from app.schemas.product_image import (
    ProductImageCreate,
    ProductImageResponse,
    ProductImageListResponse,
)
from app.utils.dependencies import get_current_user, require_manager
from app.utils.exceptions import NotFoundError
from app.cache import cache_get, cache_set, cache_delete

router = APIRouter(prefix="/api/products/{product_id}/images", tags=["product images"])

IMAGES_CACHE_PREFIX = "images"
IMAGES_TTL = 300  # 5 min


@router.get("/", response_model=ProductImageListResponse)
async def list_images(
    product_id: str,
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"{IMAGES_CACHE_PREFIX}:product:{product_id}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return ProductImageListResponse(**cached)

    result = await db.execute(
        select(ProductImage).where(ProductImage.product_id == product_id)
    )
    images = result.scalars().all()
    data = ProductImageListResponse(
        images=[ProductImageResponse.model_validate(i) for i in images],
        total=len(images),
    )
    await cache_set(cache_key, data.model_dump(), IMAGES_TTL)
    return data


@router.post("/", response_model=ProductImageResponse, status_code=status.HTTP_201_CREATED)
async def add_image(
    product_id: str,
    data: ProductImageCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager),
):
    image = ProductImage(product_id=product_id, **data.model_dump())
    db.add(image)
    await db.commit()
    await db.refresh(image)

    await cache_delete(f"{IMAGES_CACHE_PREFIX}:product:{product_id}")
    return image


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    product_id: str,
    image_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager),
):
    result = await db.execute(
        select(ProductImage).where(
            ProductImage.id == image_id,
            ProductImage.product_id == product_id,
        )
    )
    image = result.scalar_one_or_none()
    if not image:
        raise NotFoundError("Image not found")

    await db.delete(image)
    await db.commit()

    await cache_delete(f"{IMAGES_CACHE_PREFIX}:product:{product_id}")
