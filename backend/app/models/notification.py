import uuid
import enum
from datetime import datetime, UTC
from typing import Optional
from sqlalchemy import String, Text, Enum, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class NotificationType(str, enum.Enum):
    welcome = "welcome"
    order_created = "order_created"
    order_paid = "order_paid"
    order_shipped = "order_shipped"
    order_completed = "order_completed"
    order_cancelled = "order_cancelled"
    payment_failed = "payment_failed"
    promo_created = "promo_created"
    system = "system"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True
    )
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType))
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC)
    )
