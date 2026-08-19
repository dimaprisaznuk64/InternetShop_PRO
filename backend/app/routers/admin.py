from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user import User
from app.models.order import Order
from app.models.product import Product
from app.models.review import Review
from app.schemas.user import UserResponse
from app.utils.dependencies import require_admin
from app.utils.exceptions import NotFoundError, BadRequestError
from app.cache import cache_get, cache_set, cache_delete

router = APIRouter(prefix="/api/admin", tags=["admin"])

STATS_CACHE_KEY = "admin:stats"
STATS_TTL = 60  # 1 min


@router.get("/users")
async def list_users(
    q: str = Query(None, description="Search by email or username"),
    role: str = Query(None),
    is_active: bool = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User)

    if q:
        pattern = f"%{q}%"
        from sqlalchemy import or_
        stmt = stmt.where(or_(User.email.ilike(pattern), User.username.ilike(pattern)))

    if role:
        stmt = stmt.where(User.role == role)

    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)

    count_stmt = stmt
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    users = result.scalars().all()

    total_result = await db.execute(select(func.count()).select_from(count_stmt.subquery()))
    total = total_result.scalar()

    return {
        "users": [UserResponse.model_validate(u) for u in users],
        "total": total,
    }


@router.patch("/users/{user_id}/block")
async def block_user(
    user_id: str,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found")

    user.is_active = False
    await db.commit()
    await db.refresh(user)

    await cache_delete(STATS_CACHE_KEY)
    return UserResponse.model_validate(user)


@router.patch("/users/{user_id}/unblock")
async def unblock_user(
    user_id: str,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found")

    user.is_active = True
    await db.commit()
    await db.refresh(user)

    await cache_delete(STATS_CACHE_KEY)
    return UserResponse.model_validate(user)


@router.patch("/users/{user_id}/role")
async def change_role(
    user_id: str,
    role: str = Query(..., description="New role"),
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.models.user import UserRole
    valid_roles = [r.value for r in UserRole]
    if role not in valid_roles:
        raise BadRequestError(f"Invalid role. Must be one of: {valid_roles}")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found")

    user.role = role
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/stats")
async def get_statistics(
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    cached = await cache_get(STATS_CACHE_KEY)
    if cached is not None:
        return cached

    from app.models.order import OrderStatus

    users_result = await db.execute(select(func.count(User.id)))
    total_users = users_result.scalar()

    active_result = await db.execute(select(func.count(User.id)).where(User.is_active == True))
    active_users = active_result.scalar()

    products_result = await db.execute(select(func.count(Product.id)))
    total_products = products_result.scalar()

    orders_result = await db.execute(select(func.count(Order.id)))
    total_orders = orders_result.scalar()

    revenue_result = await db.execute(
        select(func.coalesce(func.sum(Order.total), 0)).where(Order.status == OrderStatus.paid)
    )
    total_revenue = float(revenue_result.scalar())

    reviews_result = await db.execute(select(func.count(Review.id)))
    total_reviews = reviews_result.scalar()

    avg_rating_result = await db.execute(select(func.avg(Review.rating)).where(Review.is_moderated == True))
    avg_rating = float(avg_rating_result.scalar() or 0)

    data = {
        "total_users": total_users,
        "active_users": active_users,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": f"{total_revenue:.2f}",
        "total_reviews": total_reviews,
        "average_rating": f"{avg_rating:.2f}",
    }
    await cache_set(STATS_CACHE_KEY, data, STATS_TTL)
    return data
