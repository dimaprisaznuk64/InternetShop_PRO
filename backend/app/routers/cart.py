from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.schemas.cart import (
    CartItemAdd,
    CartItemUpdate,
    CartItemResponse,
    CartResponse,
)
from app.utils.dependencies import get_current_user
from app.utils.exceptions import NotFoundError, BadRequestError

router = APIRouter(prefix="/api/cart", tags=["cart"])


async def _get_or_create_cart(user_id: str, db: AsyncSession) -> Cart:
    result = await db.execute(select(Cart).where(Cart.user_id == user_id))
    cart = result.scalar_one_or_none()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)
    return cart


async def _build_cart_response(cart: Cart, db: AsyncSession) -> CartResponse:
    await db.refresh(cart, ["items"])

    items = []
    subtotal = 0

    for item in cart.items:
        result = await db.execute(select(Product).where(Product.id == item.product_id))
        product = result.scalar_one_or_none()
        if not product:
            continue

        price = float(product.price)
        line_total = price * item.quantity
        subtotal += line_total

        items.append(CartItemResponse(
            id=item.id,
            product_id=item.product_id,
            variant_id=item.variant_id,
            quantity=item.quantity,
            product_name=product.name,
            product_price=str(product.price),
            product_sku=product.sku,
            line_total=f"{line_total:.2f}",
        ))

    return CartResponse(
        id=cart.id,
        items=items,
        items_count=sum(i.quantity for i in items),
        subtotal=f"{subtotal:.2f}",
    )


@router.get("/", response_model=CartResponse)
async def get_cart(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart = await _get_or_create_cart(current_user.id, db)
    return await _build_cart_response(cart, db)


@router.post("/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    data: CartItemAdd,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product).where(Product.id == data.product_id).with_for_update()
    )
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundError("Product not found")

    cart = await _get_or_create_cart(current_user.id, db)

    result = await db.execute(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == data.product_id,
            CartItem.variant_id == data.variant_id,
        )
    )
    existing_item = result.scalar_one_or_none()

    if existing_item:
        new_qty = existing_item.quantity + data.quantity
        if new_qty > product.stock:
            raise BadRequestError(f"Not enough stock. Available: {product.stock}")
        existing_item.quantity = new_qty
        item = existing_item
    else:
        if data.quantity > product.stock:
            raise BadRequestError(f"Not enough stock. Available: {product.stock}")
        item = CartItem(
            cart_id=cart.id,
            product_id=data.product_id,
            variant_id=data.variant_id,
            quantity=data.quantity,
        )
        db.add(item)

    await db.commit()
    await db.refresh(item)

    price = float(product.price)
    line_total = price * item.quantity

    return CartItemResponse(
        id=item.id,
        product_id=item.product_id,
        variant_id=item.variant_id,
        quantity=item.quantity,
        product_name=product.name,
        product_price=str(product.price),
        product_sku=product.sku,
        line_total=f"{line_total:.2f}",
    )


@router.put("/items/{item_id}", response_model=CartItemResponse)
async def update_cart_item(
    item_id: str,
    data: CartItemUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart = await _get_or_create_cart(current_user.id, db)

    result = await db.execute(
        select(CartItem).where(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("Cart item not found")

    result = await db.execute(select(Product).where(Product.id == item.product_id).with_for_update())
    product = result.scalar_one_or_none()

    if data.quantity > product.stock:
        raise BadRequestError(f"Not enough stock. Available: {product.stock}")

    item.quantity = data.quantity
    await db.commit()
    await db.refresh(item)

    price = float(product.price)
    line_total = price * item.quantity

    return CartItemResponse(
        id=item.id,
        product_id=item.product_id,
        variant_id=item.variant_id,
        quantity=item.quantity,
        product_name=product.name,
        product_price=str(product.price),
        product_sku=product.sku,
        line_total=f"{line_total:.2f}",
    )


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_cart_item(
    item_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart = await _get_or_create_cart(current_user.id, db)

    result = await db.execute(
        select(CartItem).where(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("Cart item not found")

    await db.delete(item)
    await db.commit()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart = await _get_or_create_cart(current_user.id, db)
    await db.refresh(cart, ["items"])
    for item in cart.items:
        await db.delete(item)
    await db.commit()
