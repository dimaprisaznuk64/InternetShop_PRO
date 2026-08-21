from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.review import Review
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewListResponse
from app.utils.dependencies import get_current_user, require_admin
from app.utils.exceptions import NotFoundError, AlreadyExistsError, BadRequestError
from app.cache import cache_get, cache_set, cache_delete, cache_delete_pattern

router = APIRouter(prefix="/api/reviews", tags=["reviews"])

REVIEWS_CACHE_PREFIX = "reviews"
REVIEWS_TTL = 120  # 2 min

VERIFIED_PURCHASE_STATUSES = (
    OrderStatus.paid,
    OrderStatus.processing,
    OrderStatus.shipped,
    OrderStatus.completed,
)


async def _has_verified_purchase(db: AsyncSession, user_id: str, product_id: str) -> bool:
    result = await db.execute(
        select(OrderItem.id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(
            Order.user_id == user_id,
            OrderItem.product_id == product_id,
            Order.status.in_(VERIFIED_PURCHASE_STATUSES),
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


@router.get("/product/{product_id}", response_model=ReviewListResponse)
async def list_reviews(
    product_id: str,
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"{REVIEWS_CACHE_PREFIX}:product:{product_id}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return ReviewListResponse(**cached)

    result = await db.execute(
        select(Review).where(Review.product_id == product_id, Review.is_moderated == True)
    )
    reviews = result.scalars().all()
    data = ReviewListResponse(
        reviews=[ReviewResponse.model_validate(r) for r in reviews],
        total=len(reviews),
    )
    await cache_set(cache_key, data.model_dump(), REVIEWS_TTL)
    return data


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    data: ReviewCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prod = await db.execute(select(Product).where(Product.id == data.product_id))
    if not prod.scalar_one_or_none():
        raise NotFoundError("Product not found")

    existing = await db.execute(
        select(Review).where(
            Review.user_id == current_user.id,
            Review.product_id == data.product_id,
        )
    )
    if existing.scalar_one_or_none():
        raise AlreadyExistsError("You already reviewed this product")

    review = Review(
        user_id=current_user.id,
        product_id=data.product_id,
        rating=data.rating,
        text=data.text,
        is_verified_purchase=await _has_verified_purchase(db, current_user.id, data.product_id),
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    await cache_delete(f"{REVIEWS_CACHE_PREFIX}:product:{data.product_id}")
    return review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise NotFoundError("Review not found")

    if review.user_id != current_user.id and current_user.role != "admin":
        raise BadRequestError("Access denied")

    product_id = review.product_id
    await db.delete(review)
    await db.commit()

    await cache_delete(f"{REVIEWS_CACHE_PREFIX}:product:{product_id}")


@router.patch("/{review_id}/moderate", response_model=ReviewResponse)
async def moderate_review(
    review_id: str,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise NotFoundError("Review not found")

    review.is_moderated = True
    await db.commit()
    await db.refresh(review)

    await cache_delete("admin:stats")
    await cache_delete(f"{REVIEWS_CACHE_PREFIX}:product:{review.product_id}")
    return review
