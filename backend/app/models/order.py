import uuid
import enum
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Text, Enum, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class OrderStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    processing = "processing"
    shipped = "shipped"
    completed = "completed"
    cancelled = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id")
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.pending
    )
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    delivery_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    delivery_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    promo_code_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("promo_codes.id"), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    payment: Mapped[Optional["Payment"]] = relationship(back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orders.id", ondelete="CASCADE")
    )
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id")
    )
    variant_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("product_variants.id"), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    order: Mapped["Order"] = relationship(back_populates="items")
