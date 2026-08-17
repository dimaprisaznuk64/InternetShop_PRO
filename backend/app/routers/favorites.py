from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.favorite import Favorite
from app.models.product import Product
from app.schemas.favorite import FavoriteResponse, FavoriteListResponse
from app.utils.dependencies import get_current_user
from app.utils.exceptions import NotFoundError, AlreadyExistsError

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.get("/", response_model=FavoriteListResponse)
async def list_favorites(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Favorite).where(Favorite.user_id == current_user.id)
    )
    favorites = result.scalars().all()
    return FavoriteListResponse(
        favorites=[FavoriteResponse.model_validate(f) for f in favorites],
        total=len(favorites),
    )


@router.post("/{product_id}", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    product_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prod = await db.execute(select(Product).where(Product.id == product_id))
    if not prod.scalar_one_or_none():
        raise NotFoundError("Product not found")

    existing = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.product_id == product_id,
        )
    )
    if existing.scalar_one_or_none():
        raise AlreadyExistsError("Already in favorites")

    fav = Favorite(user_id=current_user.id, product_id=product_id)
    db.add(fav)
    await db.commit()
    await db.refresh(fav)
    return fav


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    product_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.product_id == product_id,
        )
    )
    fav = result.scalar_one_or_none()
    if not fav:
        raise NotFoundError("Not in favorites")

    await db.delete(fav)
    await db.commit()
