from fastapi import APIRouter, Depends, status
from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.order import Order, OrderItem
from app.models.payment import Payment
from app.models.review import Review
from app.models.favorite import Favorite
from app.models.notification import Notification
from app.models.cart import Cart, CartItem
from app.schemas.user import UserResponse, UserUpdate, PasswordChange
from app.utils.dependencies import get_current_user
from app.utils.security import hash_password, verify_password
from app.utils.exceptions import BadRequestError, AlreadyExistsError
from app.repositories.user_repo import get_user_by_id

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/", response_model=UserResponse)
async def get_profile(current_user=Depends(get_current_user)):
    return current_user


@router.put("/", response_model=UserResponse)
async def update_profile(
    data: UserUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.email != current_user.email:
        from app.repositories.user_repo import get_user_by_email
        existing = await get_user_by_email(db, data.email)
        if existing:
            raise AlreadyExistsError("User with this email already exists")

    if data.username != current_user.username:
        from app.repositories.user_repo import get_user_by_username
        existing = await get_user_by_username(db, data.username)
        if existing:
            raise AlreadyExistsError("User with this username already exists")

    current_user.username = data.username
    current_user.email = data.email
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: PasswordChange,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise BadRequestError("Current password is incorrect")
    current_user.hashed_password = hash_password(data.new_password)
    await db.commit()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order_ids = (
        await db.execute(select(Order.id).where(Order.user_id == current_user.id))
    ).scalars().all()

    if order_ids:
        await db.execute(sa_delete(Payment).where(Payment.order_id.in_(order_ids)))
        await db.execute(sa_delete(OrderItem).where(OrderItem.order_id.in_(order_ids)))
        await db.execute(sa_delete(Order).where(Order.id.in_(order_ids)))

    await db.execute(sa_delete(Review).where(Review.user_id == current_user.id))
    await db.execute(sa_delete(Favorite).where(Favorite.user_id == current_user.id))
    await db.execute(
        sa_delete(Notification).where(Notification.user_id == current_user.id)
    )

    user_cart_ids = (
        await db.execute(select(Cart.id).where(Cart.user_id == current_user.id))
    ).scalars().all()
    if user_cart_ids:
        await db.execute(sa_delete(CartItem).where(CartItem.cart_id.in_(user_cart_ids)))
        await db.execute(sa_delete(Cart).where(Cart.id.in_(user_cart_ids)))

    await db.delete(current_user)
    await db.commit()
