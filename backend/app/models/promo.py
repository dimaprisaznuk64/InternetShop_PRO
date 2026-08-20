import uuid
import enum
from datetime import datetime, UTC
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Boolean, Numeric, Integer, DateTime
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class DiscountType(str, enum.Enum):
    percentage = "percentage"
    fixed = "fixed"


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    discount_type: Mapped[DiscountType] = mapped_column()
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    min_order_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    max_uses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=sa.text("true"))
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC)
    )
