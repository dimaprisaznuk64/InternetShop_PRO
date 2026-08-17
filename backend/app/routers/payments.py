import uuid
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.payment import Payment, PaymentStatus
from app.models.order import Order, OrderStatus
from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentListResponse,
    WebhookPayload,
)
from app.utils.dependencies import get_current_user, require_admin
from app.utils.exceptions import NotFoundError, BadRequestError

router = APIRouter(prefix="/api/payments", tags=["payments"])


def _serialize_payment(p: Payment) -> PaymentResponse:
    return PaymentResponse(
        id=p.id,
        order_id=p.order_id,
        amount=f"{float(p.amount):.2f}",
        method=p.method,
        status=p.status.value if hasattr(p.status, 'value') else p.status,
        provider_payment_id=p.provider_payment_id,
        created_at=p.created_at.isoformat(),
    )


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    data: PaymentCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(Order.id == data.order_id).options(selectinload(Order.payment))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundError("Order not found")

    if order.user_id != current_user.id:
        raise BadRequestError("Access denied")

    if order.payment:
        raise BadRequestError("Payment already exists for this order")

    provider_id = f"sim_{uuid.uuid4().hex[:16]}"

    payment = Payment(
        order_id=order.id,
        amount=order.total,
        method=data.method,
        status=PaymentStatus.success,
        provider_payment_id=provider_id,
    )
    db.add(payment)

    order.status = OrderStatus.paid
    await db.commit()

    result = await db.execute(
        select(Payment).where(Payment.id == payment.id)
    )
    payment = result.scalar_one()
    return _serialize_payment(payment)


@router.get("/", response_model=PaymentListResponse)
async def list_my_payments(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Payment)
        .join(Order, Payment.order_id == Order.id)
        .where(Order.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
    )
    result = await db.execute(stmt)
    payments = result.scalars().all()
    return PaymentListResponse(
        payments=[_serialize_payment(p) for p in payments],
        total=len(payments),
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise NotFoundError("Payment not found")

    result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = result.scalar_one_or_none()
    if order.user_id != current_user.id and current_user.role not in ("admin", "manager"):
        raise BadRequestError("Access denied")

    return _serialize_payment(payment)


@router.post("/webhook")
async def payment_webhook(
    data: WebhookPayload,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Payment).where(Payment.provider_payment_id == data.provider_payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise NotFoundError("Payment not found")

    if data.status == "success":
        payment.status = PaymentStatus.success
        result = await db.execute(select(Order).where(Order.id == payment.order_id))
        order = result.scalar_one()
        order.status = OrderStatus.paid
    elif data.status == "failed":
        payment.status = PaymentStatus.failed
    elif data.status == "refunded":
        payment.status = PaymentStatus.refunded

    await db.commit()
    return {"status": "ok"}
