import uuid
from datetime import datetime, UTC
from typing import Optional
from sqlalchemy import String, Text, Boolean, ForeignKey, Integer
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id")
    )
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id")
    )
    rating: Mapped[int] = mapped_column(Integer)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_moderated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified_purchase: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=sa.text("false")
    )
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), 
        default=lambda: datetime.now(UTC)
    )
