import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    parent_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("categories.id"), nullable=True
    )
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    parent: Mapped[Optional["Category"]] = relationship(
        back_populates="children", remote_side="Category.id"
    )
    children: Mapped[list["Category"]] = relationship(back_populates="parent")
    products: Mapped[list["Product"]] = relationship(back_populates="category")

