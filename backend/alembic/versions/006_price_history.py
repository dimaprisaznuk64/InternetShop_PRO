"""006 price_history

Revision ID: 006
Revises: 005
Create Date: 2026-08-26 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "price_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("variant_id", sa.String(36), sa.ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("old_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("new_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("changed_by_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_price_history_product_changed", "price_history", ["product_id", "changed_at"])
    op.create_index("ix_price_history_variant_changed", "price_history", ["variant_id", "changed_at"])


def downgrade() -> None:
    op.drop_index("ix_price_history_variant_changed")
    op.drop_index("ix_price_history_product_changed")
    op.drop_table("price_history")
