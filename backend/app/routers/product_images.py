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

router = APIRouter(prefix="/api/products/{product_id}/images", tags=["product images"])


@router.get("/", response_model=ProductImageListResponse)
async def list_images(
    product_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProductImage).where(ProductImage.product_id == product_id)
    )
    images = result.scalars().all()
    return ProductImageListResponse(
        images=[ProductImageResponse.model_validate(i) for i in images],
        total=len(images),
    )


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
