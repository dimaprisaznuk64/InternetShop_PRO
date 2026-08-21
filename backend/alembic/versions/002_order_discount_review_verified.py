"""orders.discount + reviews.is_verified_purchase

Revision ID: 002
Revises: 001
Create Date: 2026-08-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("discount", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "reviews",
        sa.Column(
            "is_verified_purchase",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("reviews", "is_verified_purchase")
    op.drop_column("orders", "discount")
