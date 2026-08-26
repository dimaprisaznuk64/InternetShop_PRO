from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from app.database import get_db
from app.config import get_settings
from app.models.user import User
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus
from app.models.promo import PromoCode
from app.schemas.order import (
    CheckoutRequest,
    OrderResponse,
    OrderItemResponse,
    OrderListResponse,
    OrderStatusUpdate,
)
from app.utils.dependencies import get_current_user, require_admin
from app.utils.exceptions import NotFoundError, BadRequestError
from app.cache import cache_delete, cache_delete_pattern
from app.services.background import email_service, notification_service, task_manager
from app.services.websocket import ws_manager

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _serialize_order(order: Order) -> OrderResponse:
    items = [
        OrderItemResponse(
            id=i.id,
            product_id=i.product_id,
            variant_id=i.variant_id,
            quantity=i.quantity,
            price=str(i.price),
        )
        for i in order.items
    ]
    return OrderResponse(
        id=order.id,
        status=order.status.value if hasattr(order.status, 'value') else order.status,
        total=f"{float(order.total):.2f}",
        discount=f"{float(order.discount or 0):.2f}",
        delivery_method=order.delivery_method,
        delivery_address=order.delivery_address,
        notes=order.notes,
        items=items,
        created_at=order.created_at.isoformat(),
    )


def _validate_promo(promo: PromoCode, subtotal: float) -> None:
    if not promo.is_active:
        raise BadRequestError("Promo code is inactive")

    if promo.expires_at:
        exp = promo.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            raise BadRequestError("Promo code has expired")

    if promo.max_uses is not None and promo.used_count >= promo.max_uses:
        raise BadRequestError("Promo code usage limit reached")

    if promo.min_order_amount is not None and subtotal < float(promo.min_order_amount):
        raise BadRequestError(
            f"Order total must be at least {float(promo.min_order_amount):.2f} for this promo code"
        )


@router.post("/checkout", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def checkout(
    data: CheckoutRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Cart).where(Cart.user_id == current_user.id).options(selectinload(Cart.items))
    )
    cart = result.scalar_one_or_none()
    if not cart:
        raise BadRequestError("Cart is empty")

    if not cart.items:
        raise BadRequestError("Cart is empty")

    total = 0
    order_items = []
    for cart_item in cart.items:
        result = await db.execute(
            select(Product).where(Product.id == cart_item.product_id).with_for_update()
        )
        product = result.scalar_one_or_none()
        if not product:
            raise BadRequestError(f"Product not found: {cart_item.product_id}")

        if cart_item.quantity > product.stock:
            raise BadRequestError(f"Not enough stock for {product.name}")

        product.stock -= cart_item.quantity
        price = float(product.price)
        line_total = price * cart_item.quantity
        total += line_total

        order_items.append(OrderItem(
            product_id=cart_item.product_id,
            variant_id=cart_item.variant_id,
            quantity=cart_item.quantity,
            price=product.price,
        ))

    discount = Decimal("0.00")
    promo = None
    if data.promo_code:
        result = await db.execute(
            select(PromoCode).where(PromoCode.code == data.promo_code).with_for_update()
        )
        promo = result.scalar_one_or_none()
        if not promo:
            raise BadRequestError("Promo code not found")

        _validate_promo(promo, total)

        if promo.discount_type.value == "percentage":
            discount = (Decimal(str(total)) * promo.discount_value / Decimal("100"))
        else:
            discount = promo.discount_value

        discount = min(discount, Decimal(str(total)))
        promo.used_count += 1

    order = Order(
        user_id=current_user.id,
        total=Decimal(str(total)) - discount,
        discount=discount,
        promo_code_id=promo.id if promo else None,
        delivery_method=data.delivery_method,
        delivery_address=data.delivery_address,
        notes=data.notes,
    )
    db.add(order)
    await db.flush()

    for oi in order_items:
        oi.order_id = order.id
        db.add(oi)

    for cart_item in cart.items:
        await db.delete(cart_item)

    await db.commit()

    result = await db.execute(
        select(Order).where(Order.id == order.id).options(selectinload(Order.items))
    )
    order = result.scalar_one()

    await cache_delete("admin:stats")
    await cache_delete_pattern("products:list:*")
    await cache_delete_pattern("admin:popular_products:*")

    await task_manager.submit(
        email_service.send_order_confirmation,
        current_user.email, order.id, f"${float(order.total):.2f}",
    )
    await notification_service.create(
        db, current_user.id, "order_created",
        "Order placed",
        f"Your order #{order.id[:8]} for ${float(order.total):.2f} has been placed.",
        {"order_id": order.id},
    )

    return _serialize_order(order)


@router.get("/", response_model=OrderListResponse)
async def list_my_orders(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(
            Order.user_id == current_user.id
        ).options(selectinload(Order.items)).order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()

    serialized = []
    for order in orders:
        serialized.append(_serialize_order(order))

    return OrderListResponse(orders=serialized, total=len(serialized))


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundError("Order not found")

    if order.user_id != current_user.id:
        raise BadRequestError("Access denied")

    if order.status not in (OrderStatus.pending, OrderStatus.paid):
        raise BadRequestError(
            f"Cannot cancel order with status '{order.status.value}'. "
            "Only pending or paid orders can be cancelled."
        )

    if order.status == OrderStatus.paid:
        from datetime import datetime, timedelta, UTC
        window = timedelta(minutes=get_settings().ORDER_CANCEL_WINDOW_MINUTES)
        if datetime.now(UTC) - order.created_at > window:
            raise BadRequestError(
                "Cancellation window expired. Paid orders can only be "
                f"cancelled within {get_settings().ORDER_CANCEL_WINDOW_MINUTES} minutes."
            )

    order.status = OrderStatus.cancelled
    await db.commit()

    result = await db.execute(
        select(Order).where(Order.id == order.id).options(selectinload(Order.items))
    )
    order = result.scalar_one()

    await cache_delete("admin:stats")
    await cache_delete_pattern("admin:popular_products:*")

    await notification_service.create(
        db, current_user.id, "order_cancelled",
        "Order cancelled",
        f"Your order #{order.id[:8]} has been cancelled.",
        {"order_id": order.id},
    )

    return _serialize_order(order)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundError("Order not found")

    if order.user_id != current_user.id and current_user.role not in ("admin", "manager"):
        raise BadRequestError("Access denied")

    return _serialize_order(order)


@router.get("/admin/all", response_model=OrderListResponse)
async def admin_list_orders(
    status_filter: str = Query(None, alias="status"),
    user_id: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Order)

    if status_filter:
        stmt = stmt.where(Order.status == status_filter)

    if user_id:
        stmt = stmt.where(Order.user_id == user_id)

    stmt = stmt.options(selectinload(Order.items)).order_by(Order.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    orders = result.scalars().all()

    serialized = []
    for order in orders:
        serialized.append(_serialize_order(order))

    return OrderListResponse(orders=serialized, total=len(serialized))


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    data: OrderStatusUpdate,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundError("Order not found")

    valid_statuses = [s.value for s in OrderStatus]
    if data.status not in valid_statuses:
        raise BadRequestError(f"Invalid status. Must be one of: {valid_statuses}")

    order.status = data.status
    await db.commit()

    # Broadcast status change to connected WebSocket clients
    status_val = data.status if isinstance(data.status, str) else data.status.value
    await ws_manager.broadcast(order_id, {
        "type": "status_update",
        "status": status_val,
        "order_id": order_id,
    })

    result = await db.execute(
        select(Order).where(Order.id == order.id).options(selectinload(Order.items))
    )
    order = result.scalar_one()

    await cache_delete("admin:stats")
    await cache_delete_pattern("admin:popular_products:*")

    # Send notification to order owner
    user_result = await db.execute(select(User).where(User.id == order.user_id))
    order_user = user_result.scalar_one_or_none()
    if order_user:
        status_label = data.status.replace("_", " ").title()
        await task_manager.submit(
            email_service.send_order_status_change,
            order_user.email, order.id, status_label,
        )
        await notification_service.create(
            db, order_user.id, f"order_{data.status}",
            f"Order status: {status_label}",
            f"Your order #{order.id[:8]} is now {status_label}.",
            {"order_id": order.id, "status": data.status},
        )

    return _serialize_order(order)
