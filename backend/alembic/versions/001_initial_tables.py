"""initial tables

Revision ID: 001
Revises:
Create Date: 2026-08-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, index=True),
        sa.Column("username", sa.String(100), unique=True, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("user", "manager", "admin", name="userrole"), server_default="user"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), unique=True, index=True),
        sa.Column("parent_id", sa.String(36), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), unique=True, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("sku", sa.String(100), unique=True, index=True),
        sa.Column("stock", sa.Integer(), server_default=sa.text("0")),
        sa.Column("category_id", sa.String(36), sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("brand", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "product_images",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("position", sa.Integer(), server_default=sa.text("0")),
    )

    op.create_table(
        "product_variants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sku", sa.String(100), unique=True, index=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("stock", sa.Integer(), server_default=sa.text("0")),
        sa.Column("attributes", sa.Text(), nullable=True),
    )

    op.create_table(
        "promo_codes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, index=True),
        sa.Column("discount_type", sa.Enum("percentage", "fixed", name="discounttype"), nullable=False),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("min_order_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), server_default=sa.text("0")),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "carts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "cart_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cart_id", sa.String(36), sa.ForeignKey("carts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("variant_id", sa.String(36), sa.ForeignKey("product_variants.id"), nullable=True),
        sa.Column("quantity", sa.Integer(), server_default=sa.text("1")),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.Enum("pending", "paid", "processing", "shipped", "completed", "cancelled", name="orderstatus"), server_default="pending"),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("delivery_method", sa.String(100), nullable=True),
        sa.Column("delivery_address", sa.String(500), nullable=True),
        sa.Column("promo_code_id", sa.String(36), sa.ForeignKey("promo_codes.id"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "order_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("variant_id", sa.String(36), sa.ForeignKey("product_variants.id"), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("method", sa.String(100), nullable=False),
        sa.Column("status", sa.Enum("pending", "success", "failed", "refunded", name="paymentstatus"), server_default="pending"),
        sa.Column("provider_payment_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("is_moderated", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "favorites",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "product_id", name="uq_user_product"),
    )


def downgrade() -> None:
    op.drop_table("favorites")
    op.drop_table("reviews")
    op.drop_table("payments")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("cart_items")
    op.drop_table("carts")
    op.drop_table("promo_codes")
    op.drop_table("product_variants")
    op.drop_table("product_images")
    op.drop_table("products")
    op.drop_table("categories")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS paymentstatus")
    op.execute("DROP TYPE IF EXISTS orderstatus")
    op.execute("DROP TYPE IF EXISTS discounttype")
    op.execute("DROP TYPE IF EXISTS userrole")
