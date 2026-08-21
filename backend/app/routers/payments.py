import uuid
import hmac
import hashlib
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.config import get_settings
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
from app.services.background import email_service, notification_service, task_manager

settings = get_settings()

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

    await task_manager.submit(
        email_service.send_payment_confirmation,
        current_user.email, order.id, f"${float(order.total):.2f}",
    )
    notification_service.create(
        current_user.id, "order_paid",
        "Payment received",
        f"Payment of ${float(order.total):.2f} received for order #{order.id[:8]}.",
        {"order_id": order.id, "payment_id": payment.id},
    )

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
    x_webhook_signature: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    from app.models.user import User

    if not settings.WEBHOOK_SECRET and settings.is_production:
        raise BadRequestError("Webhook secret is not configured")

    if settings.WEBHOOK_SECRET:
        if not x_webhook_signature:
            raise BadRequestError("Missing webhook signature")
        raw = f"{data.provider_payment_id}:{data.status}"
        expected = hmac.new(
            settings.WEBHOOK_SECRET.encode(), raw.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, x_webhook_signature):
            raise BadRequestError("Invalid webhook signature")

    result = await db.execute(select(Payment).where(Payment.provider_payment_id == data.provider_payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise NotFoundError("Payment not found")

    target_status = {
        "success": PaymentStatus.success,
        "failed": PaymentStatus.failed,
        "refunded": PaymentStatus.refunded,
    }.get(data.status)
    if target_status is None:
        raise BadRequestError(f"Unknown webhook status: {data.status}")

    if payment.status == target_status:
        return {"status": "ok", "idempotent": True}

    order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = order_result.scalar_one_or_none()

    if data.status == "success":
        payment.status = PaymentStatus.success
        if order:
            order.status = OrderStatus.paid

            user_result = await db.execute(select(User).where(User.id == order.user_id))
            order_user = user_result.scalar_one_or_none()
            if order_user:
                await task_manager.submit(
                    email_service.send_payment_confirmation,
                    order_user.email, order.id, f"${float(order.total):.2f}",
                )
                notification_service.create(
                    order_user.id, "order_paid",
                    "Payment confirmed",
                    f"Payment of ${float(order.total):.2f} confirmed for order #{order.id[:8]}.",
                    {"order_id": order.id, "payment_id": payment.id},
                )
    elif data.status == "failed":
        payment.status = PaymentStatus.failed
        if order:
            user_result = await db.execute(select(User).where(User.id == order.user_id))
            order_user = user_result.scalar_one_or_none()
            if order_user:
                await task_manager.submit(
                    email_service.send_payment_failed,
                    order_user.email, order.id,
                )
                notification_service.create(
                    order_user.id, "payment_failed",
                    "Payment failed",
                    f"Payment failed for order #{order.id[:8]}.",
                    {"order_id": order.id, "payment_id": payment.id},
                )
    elif data.status == "refunded":
        payment.status = PaymentStatus.refunded

    await db.commit()
    return {"status": "ok"}
