from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus
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
        delivery_method=order.delivery_method,
        delivery_address=order.delivery_address,
        notes=order.notes,
        items=items,
        created_at=order.created_at.isoformat(),
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
            select(Product).where(Product.id == cart_item.product_id)
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

    order = Order(
        user_id=current_user.id,
        total=total,
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

    result = await db.execute(
        select(Order).where(Order.id == order.id).options(selectinload(Order.items))
    )
    order = result.scalar_one()

    await cache_delete("admin:stats")
    await cache_delete_pattern("admin:popular_products:*")
    return _serialize_order(order)
